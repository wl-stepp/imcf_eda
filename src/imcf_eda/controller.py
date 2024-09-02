from typing import TYPE_CHECKING

from qtpy.QtCore import Signal, QObject
if TYPE_CHECKING:
    from pymmcore_plus import CMMCorePlus
    from imcf_eda.gui.eda import EDAGUI
    from imcf_eda.model import EDASettings
    from typing import List
from imcf_eda.gui.eda import QOverview
import numpy as np
from threading import Thread
from pathlib import Path

from imcf_eda.actuator import SpatialActuator
from imcf_eda.analyser import MIPAnalyser
from imcf_eda.interpreter import PositionInterpreter

from imcf_eda.events import EventHub


class Controller(QObject):
    scan_finished = Signal()
    analysis_finished = Signal()

    def __init__(self, model: 'EDASettings', view: 'EDAGUI',
                 mmc: 'CMMCorePlus', event_hub: 'EventHub'
                 ):
        super().__init__()
        self.model = model
        self.view = view
        self.mmc = mmc
        self.event_hub = event_hub

        self.view.overview.button.pressed.connect(self.run_overview)
        self.view.scan.scan_acq_btn.pressed.connect(self.dual_scan)
        self.analysis_finished.connect(self.update_acq_mda)

    def run_overview(self):
        overview_mda = self.model.overview.mda
        self.mmc.setConfig(self.model.config.objective_group,
                           self.model.overview.parameters.objective)
        # writer = handlers
        self.mmc.run_mda(overview_mda, block=True)
        self.fov_select = QOverview()
        self.fov_select.new_fovs.connect(self.rcv_fovs)
        self.fov_select.show()

    def rcv_fovs(self, fovs: 'List[List[np.ndarray]]'):
        print("FOVs received in EDA GUI")
        scan_mda = self.model.scan.mda
        all_fovs = [item for sublist in fovs for item in sublist]
        scan_mda = scan_mda.replace(stage_positions=all_fovs)
        self.view.scan.mda.setValue(scan_mda)

    def update_acq_mda(self):
        self.view.tabs.setCurrentIndex(3)
        self.view.acquisition.mda.setValue(self.acq_seq)

    def dual_scan(self):
        self.scan_finished.connect(self.analyse_thr)
        self.analysis_finished.connect(self.acquire_thr)
        self.scan_thr()

        self.view.tabs.setCurrentIndex(2)

    def scan(self):
        path = Path(self.model.save.save_dir) / self.model.save.save_name
        self.analyser = MIPAnalyser(self.mmc, self.event_hub,
                                    self.model.analyser, path)
        self.interpreter = PositionInterpreter(self.mmc, self.event_hub,
                                               self.model.acquisition, path)
        self.actuator = SpatialActuator(
            self.mmc, self.event_hub, self.model, self.analyser,
            self.interpreter)
        self.actuator.scan()
        self.scan_finished.emit()

    def analyse(self):
        self.analyser.analyse()
        self.acq_seq = self.interpreter.interpret()
        self.model.acquisition.mda = self.acq_seq
        self.analysis_finished.emit()

    def acquire(self):
        print("ACQUIRE")
        print(self.model.acquisition.mda)
        self.actuator.acquire()
        self.actuator.reset_pos()

    def scan_thr(self):
        self.scan_thread = Thread(target=self.scan)
        self.scan_thread.start()

    def analyse_thr(self):
        self.analysis_thread = Thread(target=self.analyse)
        self.analysis_thread.start()

    def acquire_thr(self):
        self.acquire_thread = Thread(target=self.acquire)
        self.acquire_thread.start()
