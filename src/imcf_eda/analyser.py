from pathlib import Path

from pymmcore_plus.metadata.schema import FrameMetaV1

import zarr
import numpy as np
from pymmcore_plus import CMMCorePlus
from pymmcore_plus.mda import handlers
from useq import MDAEvent, MDASequence
from psygnal import SignalGroup

from skimage import morphology, measure, transform
from tensorflow import keras

from imcf_eda.events import EventHub
from imcf_eda.model import AnalyserSettings


class MIPAnalyser():
    def __init__(self, mmc: CMMCorePlus, event_hub: EventHub,
                 settings: AnalyserSettings, path: Path):
        self.mmc = mmc
        self.event_hub = event_hub
        self.settings = settings

        self.analyse_channel = settings.channel
        self.save_dir = path
        self.path = path / "scan.ome.zarr"
        self.writer = handlers.OMEZarrWriter(self.path, overwrite=True)

        self.cameras = []
        self.events = []
        self.metadatas = []
        self.sizes = {}
        self.stack = np.ndarray((1, 1, 1))
        self.model = keras.models.load_model(
            settings.model_path, compile=False)
        self.model.predict(np.random.randint(100, 300, ((1, 256, 256, 1))))
        self.sequence = MDASequence()

    def frameReady(self, image: np.ndarray, event: MDAEvent,
                   metadata: FrameMetaV1):
        self.stack[event.index.get('c', 0), event.index.get('z', 0)] = image

        if len(self.cameras) > 1:
            new_index = {
                **event.index,
                "c": (
                    len(self.cameras) * event.index.get("c", 0)
                    + self.cameras.index(metadata.get("camera_device") or "0")
                ),
            }
            new_channel = self.sequence.channels[new_index['c']]
            event = event.replace(
                sequence=self.sequence, index=new_index,
                channel=dict(new_channel))
        # Check if we have a full stack
        if event.index.get('z', 0) == max(1, self.sizes.get('z', 0)) - 1:
            print("Full stack received!", self.stack.shape, "Computing MIP...")
            self.mip = np.max(self.stack[event.index.get('c', 0)], axis=0)
            self.writer.frameReady(self.mip, event, metadata)
            # Check if the frame is for analysis
            if event.channel.config == self.analyse_channel:
                self.events.append(event)
                self.metadatas.append(metadata)

    def sequenceStarted(self, sequence: MDASequence, metadata):

        if 'Dual' in sequence.channels[0].config:
            self.cameras = [
                x["label"]
                for x in metadata["devices"]
                if x["type"] == "CameraDevice" and x["name"] != "Multi Camera"
            ]
        if len(self.cameras) > 1:
            channels = []
            for channel in sequence.channels:
                for idx in range(len(self.cameras)):
                    channels.append(
                        channel.replace(
                            config=channel.config.split('-')[idx+1])
                    )
            sequence = sequence.replace(channels=channels)

        self.writer.sequenceStarted(sequence, metadata)
        self.sequence = sequence
        self.metadata = metadata
        self.sizes = sequence.sizes
        self.stack = np.zeros((max(1, self.sizes.get('c', 1)),
                               max(1, self.sizes.get('z', 1)),
                               self.mmc.getImageHeight(),
                               self.mmc.getImageWidth()), dtype=np.uint16)

    def sequenceFinished(self):
        self.writer.sequenceFinished(self.sequence)

    def analyse(self):
        self.net_writer = handlers.OMEZarrWriter(
            self.save_dir / "network.ome.zarr", overwrite=True)
        self.net_writer.sequenceStarted(self.sequence, self.metadata)
        for index, event, metadata in zip(range(len(self.events)), self.events,
                                          self.metadatas):
            print(f"{index}/{len(self.events)-1}")
            pos = event.index['p']
            mips = zarr.open(str(self.path/("p" + str(pos))), mode='r')
            index = tuple(event.index[k]
                          for k in self.writer.position_sizes[pos])
            mip = mips[(*index, slice(None), slice(None))].copy()
            worker = MIPWorker(mip, event, metadata, self.settings,
                               self.model, self.event_hub, self.net_writer)
            worker.run()
        self.net_writer.sequenceFinished(self.sequence)
        with open(self.save_dir / "network.ome.zarr/eda_seq.json", "w") as file:
            file.write(self.sequence.model_dump_json())
        self.event_hub.analysis_finished.emit()


class MIPWorker():
    def __init__(self, mip: np.ndarray, event: MDAEvent, metadata,
                 settings: AnalyserSettings,
                 model: keras.Model,
                 event_hub: SignalGroup, writer: handlers.OMEZarrWriter):
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
        network_output = self.model.predict(network_input)
        if self.model.layers[0].input_shape[0] is None:
            image = image[0, :, :, 0]
        else:
            network_output = network_output.reshape(
                (9, 9, 256, 256)).swapaxes(2, 1).reshape((2304, 2304))
        self.writer.frameReady(network_output, self.event, self.metadata)
        network_output = self.post_process_net_out(network_output)
        positions = self.get_positions(network_output)
        self.event_hub.new_positions.emit(positions)

    def prepare_image(self, image: np.ndarray):
        """Here if we need to do some preprocessing."""
        image = image.astype(np.float32, copy=False)
        image = (image - np.amin(image)) / \
            (np.amax(image) - np.amin(image) + 1e-10)
        if self.model.layers[0].input_shape[0] is None:
            image = np.expand_dims(image, [0, -1])
        else:
            image = image.reshape((9, 256, 9, 256)).swapaxes(
                1, 2).reshape((81, 256, 256))
        return image

    def post_process_net_out(self, network_output: np.ndarray):
        tile_size = 256
        border_size = 9
        # Remove the 9x9 pixel area at each intersection
        for i in range(1, 9):
            for j in range(1, 9):

                x_start = i * tile_size - border_size // 2
                y_start = j * tile_size - border_size // 2
                # Set the 9x9 region to zero (or any background value, e.g., the mean of neighbors)
                network_output[x_start:x_start + border_size,
                               y_start:y_start + border_size] = 0
        network_output[network_output <
                       self.settings.threshold] = 0
        network_output[network_output >=
                       self.settings.threshold] = 1
        kernel_size = self.settings.closing_kernel
        selem = morphology.rectangle(kernel_size, kernel_size)
        network_opened = morphology.opening(network_output, selem)
        return morphology.closing(network_opened, selem)

    def get_positions(self, network_output: np.ndarray):
        """Return the positions of the detected objects."""
        network_output = transform.rotate(network_output,
                                          self.settings.orientation.rotation)
        if self.settings.orientation.flipud:
            network_output = np.flipud(network_output)
        if self.settings.orientation.fliplr:
            network_output = np.fliplr(network_output)
        label_image, _ = measure.label(network_output, connectivity=2,
                                       return_num=True)
        # Calculate properties of labeled regions
        regions = measure.regionprops(label_image)
        # TODO: the mean intensity does not make sense yet, as it is a binary
        positions = [{'x': region.centroid[0], 'y': region.centroid[1], 'z': 0,
                      'score': 1, 'event': self.event} for region in regions]
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
