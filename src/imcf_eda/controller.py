from typing import TYPE_CHECKING

from qtpy.QtCore import Signal, QObject, QThread
if TYPE_CHECKING:
    from pymmcore_plus import CMMCorePlus
    from imcf_eda.gui.eda import EDAGUI
    from imcf_eda.model import EDASettings
    from typing import List
from imcf_eda.gui.eda import QOverview
import numpy as np
from threading import Thread
from pathlib import Path
import yaml

from imcf_eda.actuator import SpatialActuator
from imcf_eda.analyser import MIPAnalyser
from imcf_eda.interpreter import PositionInterpreter
import time
from imcf_eda.events import EventHub

from pymmcore_plus.mda import handlers

from imcf_eda.gui._preview import Preview
from imcf_eda.gui._qt_classes import PromptWindow


class Controller(QObject):
    scan_finished = Signal()
    analysis_finished = Signal()

    def __init__(self, model: 'EDASettings', view: 'EDAGUI',
                 mmc: 'CMMCorePlus', event_hub: 'EventHub', main_overview: 'Preview' = None
                 ):
        super().__init__()
        self.model = model
        self.view = view
        self.mmc = mmc
        self.event_hub = event_hub
        self.is_acquiring = False
        self.prompt = None
        self.main_overview = main_overview

        self.fov_select = QOverview()
        self.fov_select.new_fovs.connect(self.rcv_fovs)

        self.preview = Preview(mmcore=self.mmc, acq=True)

        self.view.overview.button.pressed.connect(self.run_overview)
        self.view.scan.oil_btn.pressed.connect(self.add_oil)
        self.view.scan.scan_acq_btn.pressed.connect(self.dual_scan)
        self.view.scan.cancel_btn.pressed.connect(self.mmc.mda.cancel)
        self.view.scan.scan_btn.pressed.connect(self.scan_thr)
        self.view.analysis.analysis_btn.pressed.connect(self.analyse_thr)
        self.view.acquisition.acq_btn.pressed.connect(self.acquire_thr)
        self.view.acquisition.cancel_btn.pressed.connect(self.mmc.mda.cancel)
        self.analysis_finished.connect(self.update_acq_mda)

    def run_overview(self):
        overview_mda = self.model.overview.mda
        self.mmc.setConfig(self.model.config.objective_group,
                           self.model.overview.parameters.objective)
        self.path = Path(self.view.save_info.save_dir.text()) / \
            self.model.save.save_name.split(".")[0]
        self.writer = handlers.OMEZarrWriter(self.path /
                                             "overview.ome.zarr",
                                             overwrite=True)
        self.mmc.run_mda(overview_mda, block=True, output=self.writer)
        self.fov_select.load_data(self.path/"overview.ome.zarr")
        self.fov_select.show()

    def rcv_fovs(self, fovs: 'List[List[np.ndarray]]'):
        print("FOVs received in EDA GUI")
        scan_mda = self.model.scan.mda
        all_fovs = [item for sublist in fovs for item in sublist]
        all_fovs = [(item[1], item[0]) for item in all_fovs]
        scan_mda = scan_mda.replace(stage_positions=all_fovs)
        self.view.scan.mda.setValue(scan_mda)
        self.model.scan.mda = scan_mda

    def update_acq_mda(self):
        self.view.tabs.setCurrentIndex(3)
        self.view.acquisition.mda.setValue(self.acq_seq)

    def dual_scan(self):
        self.path = Path(self.view.save_info.save_dir.text()) / \
            self.model.save.save_name.split(".")[0]
        with open(self.path / "settings.yaml", "w") as yaml_file:
            yaml.dump(self.model.as_dict(), yaml_file,
                      default_flow_style=False)
        self.scan_finished.connect(self.analyse_thr)
        self.analysis_finished.connect(self.acquire_thr)
        self.scan_thr()
        self.view.tabs.setCurrentIndex(2)

    def scan(self):
        if self.main_overview:
            self.main_overview.mmc_disconnect()
        path = Path(self.view.save_info.save_dir.text()) / \
            self.view.save_info.save_name.text().split(".")[0]
        print("PATH", path)
        self.analyser = MIPAnalyser(self.mmc, self.event_hub,
                                    self.model.analyser, path)
        self.interpreter = PositionInterpreter(self.mmc, self.event_hub,
                                               self.model.acquisition, path)
        self.actuator = SpatialActuator(
            self.mmc, self.event_hub, self.model, self.analyser,
            self.interpreter, path)
        self.actuator.scan()
        time.sleep(1)
        self.scan_finished.emit()

    def analyse(self):
        self.analyser.analyse()
        self.acq_seq = self.interpreter.interpret()
        self.model.acquisition.mda = self.acq_seq
        self.analysis_finished.emit()
        self.view.tabs.setCurrentIndex(3)

    def acquire(self):
        print("ACQUIRE")
        print(self.model.acquisition.mda)
        self.actuator.acquire()
        self.actuator.reset_pos()
        if self.main_overview:
            self.main_overview.mmc_connect()

    def scan_thr(self):
        self.preview.show()
        self.preview.setWindowTitle("DualScan")
        self.scan_thread = Thread(target=self.scan)
        self.scan_thread.start()

    def analyse_thr(self):
        self.analysis_thread = Thread(target=self.analyse)
        self.analysis_thread.start()
        self.scan_finished.disconnect(self.analyse_thr)

    def acquire_thr(self):
        self.acquire_thread = Thread(target=self.acquire)
        self.acquire_thread.start()
        self.analysis_finished.disconnect(self.acquire_thr)

    def live(self, objective, channel):
        if not self.is_acquiring:
            # Start the acquisition

            self.preview.mmc_connect()
            self.preview.show()

            # Set configuration based on model settings
            self.mmc.setConfig(self.model.config.objective_group, objective)
            self.mmc.setConfig(self.model.config.channel_group, channel)

            # Start acquisition
            self.mmc.startContinuousSequenceAcquisition()
            self.is_acquiring = True

        else:
            # Stop the acquisition
            self.mmc.stopSequenceAcquisition()
            self.preview.mmc_disconnect()
            self.preview.hide()
            self.is_acquiring = False

    def add_oil(self):
        self.prompt = PromptWindow()
        self.prompt.show()
        self.oil_orig_z = self.mmc.getPosition(self.model.config.corse_z_stage)
        self.oil_orig_pos = self.mmc.getXYPosition()

        self.mmc.setPosition(self.model.config.corse_z_stage, 0)
        self.mmc.setXYPosition(self.oil_orig_pos[0], 24000)
        self.mmc.setConfig(self.model.config.objective_group,
                           self.model.scan.parameters.objective)
        self.prompt.okButton.clicked.connect(self.reset_position_thr)

    def reset_position_thr(self):
        self.prompt.okButton.setEnabled(False)
        self.reset_thread = Thread(target=self.reset_position)
        self.prompt.close()
        self.reset_thread.start()

    def reset_position(self):
        pos = self.model.scan.mda.stage_positions[0]
        # check here if there are actually positions in the mda, otherwise use the original position
        self.mmc.setXYPosition(pos.x, pos.y)
        time.sleep(1)
        self.mmc.setPosition(self.model.config.corse_z_stage, self.oil_orig_z)
