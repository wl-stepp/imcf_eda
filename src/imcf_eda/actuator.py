from pathlib import Path
import json

from useq import MDASequence
from pymmcore_plus import CMMCorePlus
from pymmcore_plus.mda import handlers, mda_listeners_connected
from imcf_eda.events import EventHub


class SpatialActuator():
    def __init__(self, mmc:CMMCorePlus, event_hub: EventHub,
                       settings: dict, analyser, interpreter, **kwargs):
        self.mmc = mmc
        self.event_hub = event_hub
        self.sequence: MDASequence = settings['sequence_1']
        self.settings = settings
        self.analyser = analyser
        self.interpreter = interpreter

        self.sequence_2 = None
        self.writer = handlers.OMEZarrWriter(Path(self.settings["save"]) / "acquisition.ome.zarr", overwrite=True)
        self.event_hub.new_sequence_2.connect(self.new_sequence_2)

    def start(self):
        # try:
        self.mmc.setConfig("4-Objective", self.settings["objective_1"])
        orig_pos = self.mmc.getXYPosition()
        orig_pos_z = self.mmc.getPosition()

        self.sequence = self.settings["sequence_1"].replace(stage_positions = [(*orig_pos, orig_pos_z)])
        # self.sequence = MDASequence().model_validate(position_sequence.model_copy(update=self.settings["sequence_1"].model_dump(exclude="stage_positions")).model_dump())
        # except:
        #     print("Acquisition setup failed!!!")
        self.mmc.run_mda(self.sequence, block=True)
        with open(Path(self.settings['save']) / "scan.ome.zarr/eda_seq.json", "w") as file:
            file.write(self.sequence.model_dump_json())

        while not self.sequence_2:
            pass
        # Disconnect the analyser and interpreter from the first sequence
        self.mmc.mda.events.frameReady.disconnect(self.analyser.frameReady)
        self.mmc.mda.events.sequenceStarted.disconnect(self.analyser.sequenceStarted)
        self.mmc.mda.events.sequenceFinished.disconnect(self.analyser.sequenceFinished)
        self.mmc.mda.events.sequenceFinished.disconnect(self.interpreter.sequenceFinished)

        try:
            self.mmc.setConfig("4-Objective", self.settings["objective_2"])
        except:
            print("Objective switch failed!!!")

        self.mmc.setPosition(orig_pos_z)
        self.mmc.setXYPosition(orig_pos[0], orig_pos[1])


        with mda_listeners_connected(self.writer):
            self.mmc.mda.run(self.sequence_2)
        with open(Path(self.settings['save']) / "acquisition.ome.zarr/eda_seq.json", "w") as file:
            file.write(self.sequence_2.model_dump_json())
        self.mmc.setPosition(orig_pos_z)
        self.mmc.setXYPosition(orig_pos[0], orig_pos[1])

    def new_sequence_2(self, sequence: MDASequence):
        self.sequence_2 = sequence
