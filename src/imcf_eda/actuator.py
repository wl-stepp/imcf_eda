from pathlib import Path

from useq import MDASequence
from pymmcore_plus import CMMCorePlus
from pymmcore_plus.mda import handlers, mda_listeners_connected
from imcf_eda.events import EventHub
from imcf_eda.model import EDASettings
import time

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
        self.sequence_2: MDASequence = settings.acquisition.mda
        self.analysis_done: bool = False
        # Scan does not need a writer, as the analyser that does the mips will write that
        # self.event_hub.new_sequence_2.connect(self.new_sequence_2)

    def start(self):
        self.scan()
        self.acquire()
        self.reset_pos()

    def scan(self):
        self.save_dir = Path(self.settings.save.save_dir) / \
            self.settings.save.save_name.split(".")[0]
        print("SAVE NAME", self.save_dir)
        self.orig_pos = self.mmc.getXYPosition()
        self.orig_pos_z = self.mmc.getPosition()
        self.mmc.setConfig(self.settings.config.objective_group,
                           self.settings.scan.parameters.objective)
        self.sequence = self.settings.scan.mda
        with mda_listeners_connected(self.analyser, self.interpreter,
                                     mda_events=self.mmc.mda.events):
            self.mmc.run_mda(self.sequence, block=True)
        with open(self.save_dir / "scan.ome.zarr/eda_seq.json", "w") as file:
            file.write(self.sequence.model_dump_json())
        print("Going back to z", self.orig_pos_z)
        self.mmc.setPosition(self.orig_pos_z)
        #  while not self.analysis_done:
        #     pass

    def acquire(self):
        self.save_dir = Path(self.settings.save.save_dir) / \
            self.settings.save.save_name.split(".")[0]
        self.acq_writer = handlers.OMEZarrWriter(self.save_dir /
                                             "acquisition.ome.zarr",
                                             overwrite=True)
        self.mmc.setConfig(self.settings.config.objective_group,
                           self.settings.acquisition.parameters.objective)
        time.sleep(1)
        with mda_listeners_connected(self.acq_writer,
                                     mda_events=self.mmc.mda.events):
            self.mmc.mda.run(self.settings.acquisition.mda)
        with open(self.save_dir / "acquisition.ome.zarr/eda_seq.json",
                  "w") as file:
            file.write(self.settings.acquisition.mda .model_dump_json())
        self.analysis_done = False

    def reset_pos(self):
        self.mmc.setPosition(self.orig_pos_z)
        self.mmc.setXYPosition(self.orig_pos[0], self.orig_pos[1])

    # def new_sequence_2(self, sequence: MDASequence):
    #     self.settings.acquisition.mda = sequence
    #     self.analysis_done = True
    # 2129.2200000000003
