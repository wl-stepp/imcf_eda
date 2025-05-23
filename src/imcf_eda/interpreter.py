from threading import Timer
from pathlib import Path
import csv

import numpy as np
import json

from pymmcore_plus import CMMCorePlus
from psygnal import SignalGroup
# For solving the positions
from imcf_eda.positioning import cover_with_squares_ilp
from imcf_eda.model import AcquisitionMDASettings, AnalyserSettings


class PositionInterpreter():
    def __init__(self, mmc: CMMCorePlus, event_hub: SignalGroup,
                 acq_settings: AcquisitionMDASettings, path: Path):
        self.mmc = mmc
        self.mda = acq_settings.mda
        self.settings = acq_settings.parameters
        self.save_dir = path

        self.positions = []
        self.is_analysis_finished = False

        self.event_hub = event_hub
        self.event_hub.new_positions.connect(self.new_positions)
        # self.event_hub.analysis_finished.connect(self.analysis_finished)

    def new_positions(self, positions: list, pixel_size: float):
        for position in positions:
            position['x'] = (position['x']*pixel_size +
                             position['event'].x_pos -
                             self.mmc.getImageWidth() *
                             pixel_size/2)
            position['y'] = (position['y']*pixel_size +
                             position['event'].y_pos -
                             self.mmc.getImageHeight() *
                             pixel_size/2)
            self.positions.append(position)

    def interpret(self):
        #     if not self.is_analysis_finished:
        #         t = Timer(5, self.sequenceFinished)
        #         t.start()
        print("Sequence finished, analysis finished")
        with open(self.save_dir / "positions.csv", "w", newline='') as file:
            csv_pos = [[i, pos['x'],  pos['y']]
                       for i, pos in enumerate(self.positions)]
            write = csv.writer(file)
            write.writerow(['index', 'axis-0', 'axis-1'])
            write.writerows(csv_pos)
        print("OPTIMIZING POSITIONS...")
        pos = [[i['x'] + float(self.settings.x_offset) for i in self.positions],
                [i['y'] - float(self.settings.y_offset)for i in self.positions]]
        print("Positions:", len(pos[0]))
        fov_size = self.mmc.getPixelSizeUmByID(
            self.settings.pixel_size_config)*self.mmc.getImageWidth()
        print("FOV", fov_size)
        squares = cover_with_squares_ilp(np.asarray(pos).T,
                                         fov_size,
                                         padding = self.settings.min_border_distance,
                                         plot=False)

        z = self.mmc.getPosition() + self.settings.z_offset
        squares = [[pos[0] + fov_size/2 - self.settings.min_border_distance,
                    pos[1] + fov_size/2 - self.settings.min_border_distance]
                   for pos in squares]

        with open(self.save_dir / "imaging_positions.csv",
                  "w", newline='') as file:
            csv_squares = [(i, pos[0], pos[1])
                           for i, pos in enumerate(squares)]
            write = csv.writer(file)
            write.writerow(['index', 'axis-0', 'axis-1'])
            write.writerows(csv_squares)

        squares = [(i[0] , i[1], z) for i in squares]
        print(f"IMAGING AT {len(squares)} positions:", squares)
        print(self.mda.model_dump_json())
        new_sequence = self.mda.replace(stage_positions=squares)
        with open(self.save_dir / "imaging_sequence.json", "w") as file:
            json.dump(new_sequence.model_dump(), file)
        return new_sequence

    # def analysis_finished(self):
    #     self.is_analysis_finished = True
