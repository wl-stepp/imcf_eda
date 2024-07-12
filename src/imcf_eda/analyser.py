from threading import Thread
from pathlib import Path

import zarr
import numpy as np
from pymmcore_plus import CMMCorePlus
from pymmcore_plus.mda import handlers
from useq import MDAEvent, MDASequence
from psygnal import SignalGroup

from skimage import morphology, measure, transform
from tensorflow import keras

from imcf_eda.events import EventHub
from imcf_eda.model import SETTINGS

class MIPAnalyser():
    def __init__(self, mmc:CMMCorePlus, event_hub: EventHub,
                 settings:dict = SETTINGS, **kwargs):
        self.mmc = mmc
        self.event_hub = event_hub
        self.settings = settings

        self.analyse_channel = settings['analyser']['channel']
        self.path = Path(self.settings["save"]) / "scan.ome.zarr"
        self.writer = handlers.OMEZarrWriter(self.path, overwrite=True)

        self.events = []
        self.metadatas = []
        self.sizes = None
        self.stack = None
        self.model = keras.models.load_model(settings['analyser']['model_path'])
        self.model.predict(np.random.randint(100,300,((1, 256, 256, 1))))
        self.sequence = None
        self.analysis_threads = []

    def frameReady(self, image: np.ndarray, event: MDAEvent, metadata: dict):
        # Check if the frame is for us
        if self.analyse_channel is None or event.channel != self.analyse_channel:
            return

        self.stack[event.index.get('c', 0), event.index.get('z', 0)] = image

        # Check if we have a full stack
        if event.index.get('z', 0) == self.sizes['z'] - 1:
            print("Full stack received!", self.stack.shape, "Computing MIP...")
            self.mip = np.max(self.stack[event.index.get('c', 0)], axis=0)
            self.writer.frameReady(self.mip, event, metadata)
            self.events.append(event)
            self.metadatas.append(metadata)

    def sequenceStarted(self, sequence: MDASequence):
        self.sequence = sequence
        self.sizes = sequence.sizes
        self.stack = np.zeros((max(1, self.sizes.get('c', 1)), self.sizes.get('z', 1),
                               self.mmc.getImageHeight(), self.mmc.getImageWidth()), dtype=np.uint16)
        self.writer.sequenceStarted(sequence)

    def sequenceFinished(self):
        self.writer.sequenceFinished(self.sequence)
        mips = zarr.open(str(self.path/'p0'), mode='r')
        print(mips)
        self.net_writer = handlers.OMEZarrWriter(self.settings["save"] + "/network.ome.zarr", overwrite=True)
        self.net_writer.sequenceStarted(self.sequence)
        for event, metadata in zip(self.events, self.metadatas):
            print(event.index)
            mip = mips[event.index['g'], event.index['c'], event.index['z'], :, :].copy()
            worker = MIPWorker(mip, event, metadata, self.settings, self.model, self.event_hub, self.net_writer)
            worker.run()
        self.net_writer.sequenceFinished(self.sequence)
        self.event_hub.analysis_finished.emit()

class MIPWorker():
    def __init__(self, mip: np.ndarray, event:MDAEvent, metadata, settings, model: keras.Model,
                 event_hub: SignalGroup, writer: handlers.TensorStoreHandler, **kwargs):
        self.mip = mip
        self.event = event
        self.metadata = metadata
        self.settings = settings
        self.model = model
        self.event_hub = event_hub
        self.writer = writer

    def run(self):
        """Get the first pixel value of the passed images and return."""
        network_input = self.prepare_image(self.mip)
        print(f"NET IN {network_input.shape}")
        network_output = self.model.predict(network_input)
        network_output = network_output.reshape((9,9,256,256)).swapaxes(2,1).reshape((2304, 2304))
        network_output = self.post_process_net_out(network_output)
        print(f"RESHAPED OUT {network_output.shape}, max {network_output.max()}")
        positions = self.get_positions(network_output)
        print("EMIT positions")
        self.event_hub.new_positions.emit(positions)        
        self.writer.frameReady(network_output, self.event, self.metadata)

    def prepare_image(self, image: np.ndarray):
        """Here if we need to do some preprocessing."""
        image = image.astype(np.float32,copy=False)
        image = (image - np.amin(image)) / (np.amax(image) - np.amin(image) + 1e-10)
        image = image.reshape((9,256,9,256)).swapaxes(1,2).reshape((81,256,256))
        return image

    def post_process_net_out(self, network_output: np.ndarray):
        network_output[network_output < self.settings['analyser']['threshold']] = 0
        network_output[network_output >= self.settings['analyser']['threshold']] = 1
        kernel_size = self.settings['analyser']['closing_kernel']
        selem = morphology.rectangle(kernel_size[0], kernel_size[1])
        network_opened = morphology.opening(network_output, selem)
        return morphology.closing(network_opened, selem)


    def get_positions(self, network_output: np.ndarray):
        """Return the positions of the detected objects."""
        network_output = transform.rotate(network_output, 270)
        network_output = np.flipud(network_output)
        label_image, num_labels = measure.label(network_output, connectivity=2, return_num=True)
        # Calculate properties of labeled regions
        regions = measure.regionprops(label_image)
        #TODO: the mean intensity does not make sense yet, as it is a binary image
        positions = [{'x': region.centroid[0], 'y': region.centroid[1],'z': 0, 'score': 1,
                      'event': self.event} for region in regions]
        # FOR SIMULATION
        # positions = []
        # for _ in range(5):
        #     x, y, score = np.random.randint(0, 2304, 3)
        #     z = 0
        #     positions.append({'x': x, 'y': y, 'z': z, 'score': score, 'event': self.event})
        # x, y, z, score = [0, 0, 0, 100]
        # positions.append({'x': x, 'y': y, 'z': z, 'score': score, 'event': self.event})
        # x, y, z, score = [0, 2304, 0, 100]
        # positions.append({'x': x, 'y': y, 'z': z, 'score': score, 'event': self.event})
        # x, y, z, score = [2304, 0, 0, 100]
        # positions.append({'x': x, 'y': y, 'z': z, 'score': score, 'event': self.event})
        # x, y, z, score = [2304, 2304, 0, 100]
        # positions.append({'x': x, 'y': y, 'z': z, 'score': score, 'event': self.event})
        # x, y, z, score = [2304/2, 2304/2, 0, 100]
        # positions.append({'x': x, 'y': y, 'z': z, 'score': score, 'event': self.event})
        return positions