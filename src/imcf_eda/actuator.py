from pathlib import Path

from useq import MDASequence
from pymmcore_plus import CMMCorePlus
from pymmcore_plus.mda import handlers, mda_listeners_connected
from imcf_eda.events import EventHub
from imcf_eda.model import EDASettings
from imcf_eda.writer import IMCFWriter
import time
import os
import json


class SpatialActuator():
    def __init__(self, mmc: CMMCorePlus, event_hub: EventHub,
                 settings: EDASettings, analyser, interpreter, path):
        self.mmc = mmc
        self.event_hub = event_hub
        self.sequence: MDASequence = settings.scan.mda
        self.settings = settings
        self.analyser = analyser
        self.interpreter = interpreter
        self.save_dir = path
        self.path = None

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
        if 'Dual' in self.settings.scan.mda.channels[0].config:
            self.mmc.setConfig(self.settings.config.camera_setting,
                               self.settings.config.camera_dual)
        print("SAVE NAME", self.save_dir)
        self.orig_pos = self.mmc.getXYPosition()
        self.orig_pos_z = self.mmc.getPosition()

        positions = self.settings.scan.mda.stage_positions
        new_positions = []
        for position in positions:
            new_positions.append({'x': position.x, 'y': position.y, 'z': self.orig_pos_z})
        self.settings.scan.mda.replace(stage_positions=new_positions)
        
        self.mmc.setConfig(self.settings.config.objective_group,
                           self.settings.scan.parameters.objective)
        time.sleep(0.5)
        self.mmc.mda.events.sequenceFinished.connect(self.scan_cleanup)

        self.mmc.run_mda(self.settings.scan.mda, output=self.analyser)


    def scan_cleanup(self, _):
        self.mmc.mda.events.sequenceFinished.disconnect(self.scan_finished)
        with open(self.save_dir / "scan.ome.zarr/eda_seq.json", "w") as file:
            json.dump(self.settings.scan.mda.model_dump(), file)
        print("Going back to z", self.orig_pos_z)
        self.mmc.setPosition(self.orig_pos_z)
    

    def acquire(self, path=None):
        self.path = path
        if path is None:
            self.path = self.save_dir / "acquisition.ome.zarr"
        if 'Dual' in self.settings.acquisition.mda.channels[0].config:
            self.mmc.setConfig(self.settings.config.camera_setting,
                               self.settings.config.camera_dual)

        self.acq_writer = IMCFWriter(self.path)
        self.mmc.setConfig(self.settings.config.objective_group,
                           self.settings.acquisition.parameters.objective)
        time.sleep(1)
        self.mmc.mda.events.sequenceFinished.connect(self.acquire_cleanup)
        self.mmc.mda.events.sequenceCanceled.connect(self.acquire_cleanup)
        self.mmc.run_mda(self.settings.acquisition.mda, output=self.acq_writer)

    def acquire_cleanup(self, _):
        self.mmc.mda.events.sequenceFinished.disconnect(self.acquire_cleanup)
        self.mmc.mda.events.sequenceCanceled.disconnect(self.acquire_cleanup)
        with open(self.path / "eda_seq.json", "w") as file:
            file.write(self.settings.acquisition.mda.model_dump_json())
        self.acq_writer.finalize_metadata()
        self.analysis_done = False


    def reset_pos(self):
        self.mmc.setPosition(self.orig_pos_z)
        self.mmc.setXYPosition(self.orig_pos[0], self.orig_pos[1])

    # def new_sequence_2(self, sequence: MDASequence):
    #     self.settings.acquisition.mda = sequence
    #     self.analysis_done = True
    # 2129.2200000000003
