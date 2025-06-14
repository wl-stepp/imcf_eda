from typing import TYPE_CHECKING

from qtpy.QtCore import Signal, QObject, QThread
if TYPE_CHECKING:
    from pymmcore_plus import CMMCorePlus
    from imcf_eda.gui.eda import EDAGUI
    from imcf_eda.model import EDASettings
    from typing import List
from imcf_eda.gui.eda import QOverview
from imcf_eda.gui.progress import MDAProgress
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
from imcf_eda.writer import IMCFWriter


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
        self.actuator = None
        self.analyser = None
        self.interpreter = None

        self.fov_select = QOverview()
        self.fov_select.new_fovs.connect(self.rcv_fovs)

        settings = {"rot": 0, "mirror_x": False, "mirror_y": True}
        self.preview = Preview(mmcore=self.mmc, acq=True, settings=settings)
        # self.preview_2 = Preview(mmcore=self.mmc, acq=True, view_channel=1)

        self.view.overview.button.pressed.connect(self.run_overview)
        self.view.scan.oil_btn.pressed.connect(self.add_oil)
        self.view.scan.scan_acq_btn.pressed.connect(self.dual_scan)
        self.view.scan.cancel_btn.pressed.connect(self.mmc.mda.cancel)
        self.view.scan.scan_btn.pressed.connect(self.scan_and_analysis)
        self.view.analysis.analysis_btn.pressed.connect(self.analyse_thr)
        self.view.acquisition.acq_btn.pressed.connect(self.acquire_thr)
        self.view.acquisition.cancel_btn.pressed.connect(self.mmc.mda.cancel)
        self.analysis_finished.connect(self.update_acq_mda)
        self.mmc.mda.events.sequenceCanceled.connect(self.cancel_mda)

    def run_overview(self):
        self.mmc.stopSequenceAcquisition()
        overview_mda = self.model.overview.mda
        overview_mda = overview_mda.replace(stage_positions=())
        self.mmc.setConfig(self.model.config.objective_group,
                           self.model.overview.parameters.objective)
        self.path = Path(self.view.save_info.save_dir.text()) / \
            self.view.save_info.save_name.text().split(".")[0]
        self.path = self.increment_path(self.path, 'overview.ome.zarr')
        self.writer = handlers.OMEZarrWriter(
            self.path / "overview.ome.zarr", overwrite=True)
        self.mmc.run_mda(overview_mda, block=True, output=self.writer)
        self.fov_select.setWindowTitle("Overview")
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

    def scan_and_analysis(self):
        self.mmc.stopSequenceAcquisition()
        self.path = Path(self.view.save_info.save_dir.text()) / \
            self.model.save.save_name.split(".")[0]
        with open(self.path / "settings.yaml", "w") as yaml_file:
            yaml.dump(self.model.as_dict(), yaml_file,
                      default_flow_style=False)
        self.scan_finished.connect(self.analyse_thr)
        self.scan_thr()
        self.view.tabs.setCurrentIndex(2)

    def dual_scan(self):
        self.mmc.stopSequenceAcquisition()
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
        self.mmc.stopSequenceAcquisition()
        # prog = MDAProgress(self.mmc)
        path = Path(self.view.save_info.save_dir.text()) / \
            self.view.save_info.save_name.text().split(".")[0]
        path = self.increment_path(path, 'scan.ome.zarr')
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
        self.prog.deleteLater()

    def cancel_mda(self):
        try:
            self.scan_finished.disconnect(self.analyse_thr)
        except:
            print('Analysis was not scheduled')

    def analyse(self):
        # TODO: If we reload this, we should get the positions from the save
        self.analyser.analyse()
        self.acq_seq = self.interpreter.interpret()
        self.model.acquisition.mda = self.acq_seq
        self.analysis_finished.emit()
        self.view.tabs.setCurrentIndex(3)

    def acquire(self):
        print("ACQUIRE")
        self.mmc.stopSequenceAcquisition()
        path = Path(self.view.save_info.save_dir.text()) / \
            self.view.save_info.save_name.text().split(".")[0]
        if not self.actuator:
            self.actuator = SpatialActuator(
                self.mmc, self.event_hub, self.model, self.analyser,
                self.interpreter, path)
        self.actuator.acquire(path / "acquisition.ome.zarr")
        self.prog.deleteLater()
        self.actuator.reset_pos()
        if self.main_overview:
            self.main_overview.setWindowTitle("Preview")
        print("Acquistion Done")

    def scan_thr(self):
        self.preview.show()
        # self.preview_2.show()
        self.preview.setWindowTitle("Scan SubChannel 0")
        if self.main_overview:
            self.main_overview.setWindowTitle("Scan SubChannel 1")
        # self.preview_2.setWindowTitle("Scan Channel 1")
        self.prog = MDAProgress(self.mmc)
        self.scan_thread = Thread(target=self.scan)
        self.scan_thread.start()

    def analyse_thr(self):
        if self.main_overview:
            self.main_overview.setWindowTitle("Preview")
        self.analysis_thread = Thread(target=self.analyse)
        self.analysis_thread.start()
        try:
            self.scan_finished.disconnect(self.analyse_thr)
        except TypeError:
            pass

    def acquire_thr(self):
        self.prog = MDAProgress(self.mmc)
        self.preview.setWindowTitle("Acquisition SubChannel 0")
        if self.main_overview:
            self.main_overview.setWindowTitle("Acquisition SubChannel 1")
        # self.preview_2.setWindowTitle("Acquisition Channel 1")
        self.acquire_thread = Thread(target=self.acquire)
        self.acquire_thread.start()
        try:
            self.analysis_finished.disconnect(self.acquire_thr)
        except TypeError:
            pass

    def increment_path(self, path, sub_folder):
        print("INCREMENT PATH")
        while (path / sub_folder).is_dir():
            name = self.view.save_info.save_name.text().split(".")[0]
            n = int(self.view.save_info.save_name.text().split(".")[0][-3:])
            name = name[:-3] + str(n+1).zfill(3)
            self.view.save_info.save_name.setText(name)
            path = Path(self.view.save_info.save_dir.text()) / \
                self.view.save_info.save_name.text().split(".")[0]
        return path

    def live(self, objective, channel):
        if not self.is_acquiring:
            # Start the acquisition

            self.preview.mmc_connect()
            self.preview.show()
            # self.preview_2.mmc_connect()
            # self.preview_2.show()

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
            # self.preview_2.mmc_disconnect()
            # self.preview_2.hide()
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
