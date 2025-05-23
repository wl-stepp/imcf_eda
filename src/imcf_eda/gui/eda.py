import json
import pathlib
import numpy as np
import zarr
from qtpy.QtWidgets import (QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QWidget, QCheckBox)
from qtpy.QtCore import Signal  # type:ignore
from qtpy.QtGui import QFont

from imcf_eda.gui._qt_classes import QWidgetRestore, set_dark
from imcf_eda.gui.overview import Overview
from pymmcore_widgets import MDAWidget
from pymmcore_widgets import LiveButton
from pymmcore_widgets.mda._save_widget import SaveGroupBox
from pymmcore_plus import CMMCorePlus
from imcf_eda.model import (EDASettings, OverviewMDASettings, ScanMDASettings,
                            AcquisitionMDASettings, AnalyserSettings, OverviewSettings)
from imcf_eda.events import EventHub
from dataclasses import asdict


class OverviewGUI(QWidget):
    def __init__(self, mmc: CMMCorePlus,
                 settings: OverviewMDASettings):
        super().__init__()
        self.lay = QVBoxLayout()
        self.setLayout(self.lay)
        self.mda = MDAWidget(mmcore=mmc)
        self.mda.valueChanged.connect(self.update_mda)
        self.mda.save_info.hide()
        self.mda.control_btns.hide()
        self.mda.tab_wdg.setTabEnabled(0, False)
        self.mda.tab_wdg._cboxes[0].hide()  # time
        self.mda.tab_wdg.setTabEnabled(1, False)
        self.mda.tab_wdg._cboxes[1].hide()  # position
        self.mda.tab_wdg.setTabEnabled(3, False)
        self.mda.tab_wdg._cboxes[3].hide()  # z
        self.mda.setWindowTitle("Overview")
        self.lay.addWidget(self.mda)

        self.settings = settings or OverviewMDASettings()
        self.mda.setValue(self.settings.mda)
        self.lay.addWidget(self.settings.parameters.gui.native)  # type:ignore
        # self.prev_btn = QPushButton("Preview")
        self.button = QPushButton("Run Overview")
        self.button.setFont(QFont('Sans Serif', 14))
        # self.lay.addWidget(self.prev_btn)
        self.lay.addWidget(self.button)

    def update_mda(self):
        self.settings.mda = self.mda.value()


class ScanGUI(QWidget):
    def __init__(self, mmc: CMMCorePlus,
                 settings: ScanMDASettings | None = None):
        super().__init__()
        self.lay = QVBoxLayout()
        self.setLayout(self.lay)

        self.mda = MDAWidget(mmcore=mmc)
        self.mda.valueChanged.connect(self.update_mda)
        self.mda.save_info.hide()
        self.mda.control_btns.hide()
        self.mda.setWindowTitle("Scan")
        self.mda.tab_wdg.setTabEnabled(0, False)
        self.mda.tab_wdg._cboxes[0].hide()  # time
        self.lay.addWidget(self.mda)

        self.settings = settings or ScanMDASettings()
        self.lay.addWidget(self.settings.parameters.gui.native)  # type:ignore

        self.oil_btn = QPushButton("Add Oil")
        self.live_button = LiveButton()
        self.live_button.setText("Focus")

        # self.btn_lay.addWidget(self.scan_btn)
        self.prep_btn_lay = QHBoxLayout()
        self.prep_btn_lay.addWidget(self.oil_btn)
        self.prep_btn_lay.addWidget(self.live_button)
        # self.btn_lay.addWidget(self.focus_btn)

        self.lay.addLayout(self.prep_btn_lay)

    def update_mda(self):
        self.settings.mda = self.mda.value()


class AcquisitionGUI(QWidget):
    def __init__(self,
                 mmc: CMMCorePlus, event_hub: EventHub,
                 settings: AcquisitionMDASettings | None = None,
                 ):
        super().__init__()
        self.setObjectName("AcquisitionTab")
        self.lay = QVBoxLayout()
        self.setLayout(self.lay)

        self.settings = settings or AcquisitionMDASettings()

        self.mda = MDAWidget(mmcore=mmc)
        self.mda.save_info.hide()
        self.mda.control_btns.hide()
        self.mda.setWindowTitle("Acquisition")
        self.mda.tab_wdg.setTabEnabled(0, False)
        self.mda.tab_wdg._cboxes[0].hide()  # time
        self.mda.valueChanged.connect(self.update_mda)

        self.lay.addWidget(self.mda)
        self.mda.setValue(self.settings.mda)
        self.lay.addWidget(self.settings.parameters.gui.native)  # type:ignore

        self.event_hub = event_hub

    def update_mda(self):
        self.settings.mda = self.mda.value()


class AnalyserGUI(QWidget):
    def __init__(self, settings: AnalyserSettings):
        super().__init__()
        self.setObjectName("AnalysisTab")
        self.lay = QVBoxLayout()
        self.setLayout(self.lay)

        self.settings = settings or AnalyserSettings()
        self.analysis_gui = self.settings.gui.native
        self.lay.addWidget(self.analysis_gui)


class EDAGUI(QWidgetRestore):
    def __init__(self, mmc: CMMCorePlus,
                 settings: EDASettings, event_hub: EventHub,
                 parent=None):
        super().__init__(parent)

        self.mmc = mmc
        self.settings = settings

        self.setWindowTitle("EDA - Smart Imaging")

        self.tabs = QTabWidget()
        self.save_info = SaveGroupBox(parent=self)
        self.save_info.setValue(asdict(settings.save))

        self.load_btn = QPushButton("Load Positions")

        self.overview = OverviewGUI(mmc, settings.overview)
        self.scan = ScanGUI(mmc, settings.scan)
        self.analysis = AnalyserGUI(settings.analyser)
        self.acquisition = AcquisitionGUI(mmc, event_hub, settings.acquisition)

        self.print_btn = QPushButton("Print Settings")
        self.print_btn.pressed.connect(self.print_settings)

        self.tabs.addTab(self.overview, "Overview")
        self.tabs.addTab(self.scan, "Scan")
        self.tabs.addTab(self.analysis,  # type:ignore
                         "Analyser")
        self.tabs.addTab(self.acquisition, "Acquisition")

        self.start_btn = QPushButton("Start")
        self.cancel_btn = QPushButton("Cancel")

        self.acq_btn_lay = QHBoxLayout()
        self.acq_btn_lay.addWidget(self.start_btn)
        self.acq_btn_lay.addWidget(self.cancel_btn)

        self.modes_lay = QVBoxLayout()
        self.do_scan = QCheckBox('Scan')
        self.do_scan.setChecked(True)
        self.modes_lay.addWidget(self.do_scan)
        self.do_analyse = QCheckBox('Analyse')
        self.do_analyse.setChecked(True)
        self.modes_lay.addWidget(self.do_analyse)
        self.do_acquire = QCheckBox('Acquire')
        self.do_acquire.setChecked(True)
        self.modes_lay.addWidget(self.do_acquire)

        self.lay = QVBoxLayout()
        self.setLayout(self.lay)
        self.lay.addWidget(self.save_info)
        self.lay.addWidget(self.load_btn)
        self.lay.addWidget(self.tabs)
        self.lay.addLayout(self.acq_btn_lay)
        self.lay.addLayout(self.modes_lay)
        self.lay.addWidget(self.print_btn)

    def print_settings(self):
        from pprint import pprint
        pprint(self.settings)


# TODO: the loading here might have to go somewhere else


class QOverview(QWidgetRestore):
    new_fovs = Signal(list)

    def __init__(self, data_dir=None, fov_size: float = 260.7):
        super().__init__()
        self.overview = Overview(fov_size=fov_size)
        self.lay = QVBoxLayout()
        self.setLayout(self.lay)
        self.lay.addWidget(self.overview.canvas.native)
        self.super_update_fovs = getattr(self.overview, "update_fovs", None)
        self.overview.update_fovs = self.patched_update_fovs

    def patched_update_fovs(self):
        if self.super_update_fovs:
            self.super_update_fovs()
            self.new_fovs.emit(self.overview.fovs)

    def load_data(self, data_dir: pathlib.Path, settings: OverviewSettings):
        with open(pathlib.Path(data_dir) / ".zattrs", "r") as file:
            metadata = json.load(file)
        zarr_data = zarr.open(data_dir, mode='r')
        # Convert to numpy array (if needed, this will depend on how the Zarr array is structured)
        data = np.array(zarr_data)
        print(metadata)
        print(data.shape)
        scale = [metadata["frame_metadatas"][0]["pixel_size_um"],
                 metadata["frame_metadatas"][0]["pixel_size_um"]]
        print(scale)
        if len(data.shape) == 4:
            shape = data.shape
        else:
            shape = [1]
        # The offset directions here might be wrong
        pos = [(metadata["frame_metadatas"][i]['position']['x'] + settings.x_offset,
                metadata["frame_metadatas"][i]['position']['y'] + settings.y_offset) for i in range(shape[0])]
        print(pos)
        if len(data.shape) == 4:
            data = data[:, 0, :, :]
        elif len(data.shape) == 2:
            data = np.expand_dims(data, 0)
        self.overview.update_data(pos, data, scale)


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication([])
    from pymmcore_plus import CMMCorePlus

    set_dark(app)
    mmc = CMMCorePlus.instance()
    mmc.loadSystemConfiguration()
    settings = EDASettings()
    eda = EDAGUI(mmc, settings)
    eda.show()
    app.exec_()  # type: ignore
