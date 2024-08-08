from pathlib import Path

from useq import MDASequence
from pymmcore_plus import CMMCorePlus
from pymmcore_plus.mda import handlers, mda_listeners_connected
from imcf_eda.events import EventHub
from imcf_eda.model import EDASettings


class SpatialActuator():
    def __init__(self, mmc: CMMCorePlus, event_hub: EventHub,
                 settings: EDASettings, analyser, interpreter):
        self.mmc = mmc
        self.event_hub = event_hub
        self.sequence: MDASequence = settings.scan.mda
        self.settings = settings
        self.analyser = analyser
        self.interpreter = interpreter

        self.orig_pos = self.mmc.getXYPosition()
        self.orig_pos_z = self.mmc.getPosition()

        self.save_dir = Path(self.settings.save.save_dir) / \
            self.settings.save.save_name

        self.sequence_2 = None
        self.writer = handlers.OMEZarrWriter(self.save_dir /
                                             "acquisition.ome.zarr",
                                             overwrite=True)
        self.event_hub.new_sequence_2.connect(self.new_sequence_2)

    def start(self):
        self.scan()
        self.disconnect_eda()
        self.acquire()
        self.mmc.setPosition(self.orig_pos_z)
        self.mmc.setXYPosition(self.orig_pos[0], self.orig_pos[1])

    def scan(self):
        self.orig_pos = self.mmc.getXYPosition()
        self.orig_pos_z = self.mmc.getPosition()
        self.mmc.setConfig(self.settings.config.objective_group,
                           self.settings.scan.parameters.objective)
        self.sequence = self.settings.scan.mda

        self.mmc.run_mda(self.sequence, block=True)
        with open(self.save_dir / "scan.ome.zarr/eda_seq.json", "w") as file:
            file.write(self.sequence.model_dump_json())

    def acquire(self):
        self.mmc.setConfig(self.settings.config.objective_group,
                           self.settings.acquisition.parameters.objective)
        while not self.sequence_2:
            pass
        with mda_listeners_connected(self.writer):
            self.mmc.mda.run(self.sequence_2)
        with open(self.save_dir / "acquisition.ome.zarr/eda_seq.json",
                  "w") as file:
            file.write(self.sequence_2.model_dump_json())
        self.sequence_2 = None

    def disconnect_eda(self):
        # Disconnect the analyser and interpreter from the first sequence
        self.mmc.mda.events.frameReady.disconnect(self.analyser.frameReady)
        self.mmc.mda.events.sequenceStarted.disconnect(
            self.analyser.sequenceStarted)
        self.mmc.mda.events.sequenceFinished.disconnect(
            self.analyser.sequenceFinished)
        self.mmc.mda.events.sequenceFinished.disconnect(
            self.interpreter.sequenceFinished)

    def new_sequence_2(self, sequence: MDASequence):
        self.sequence_2 = sequence
