from qtpy.QtWidgets import (QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QWidget)
from qtpy.QtCore import Signal  # type:ignore
from qtpy.QtGui import QFont

from imcf_eda.gui._qt_classes import QWidgetRestore, set_dark
from imcf_eda.gui.overview import Overview
from pymmcore_widgets import MDAWidget
from pymmcore_widgets.mda._save_widget import SaveGroupBox
from pymmcore_plus import CMMCorePlus
from imcf_eda.model import (EDASettings, OverviewMDASettings, ScanMDASettings,
                            AcquisitionMDASettings)
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
        self.button = QPushButton("⏵ Run Overview")
        self.button.setFont(QFont('Sans Serif', 16))
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

        self.scan_btn = QPushButton("⏵ Scan Only")
        self.scan_btn.setFont(QFont('Times', 16))
        self.scan_acq_btn = QPushButton("⏵ DualScan")
        self.scan_acq_btn.setFont(QFont('Sans Serif', 16))
        self.btn_lay = QHBoxLayout()
        self.btn_lay.addWidget(self.scan_btn)
        self.btn_lay.addWidget(self.scan_acq_btn)
        self.lay.addLayout(self.btn_lay)

    def update_mda(self):
        self.settings.mda = self.mda.value()


class AcquisitionGUI(QWidget):
    def __init__(self,
                 mmc: CMMCorePlus,
                 settings: AcquisitionMDASettings | None = None):
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

        self.acq_btn = QPushButton("⏵ Acquire")
        self.acq_btn.setFont(QFont('Sans Serif', 16))
        self.lay.addWidget(self.acq_btn)

    def update_mda(self):
        self.settings.mda = self.mda.value()


class EDAGUI(QWidgetRestore):
    def __init__(self, mmc: CMMCorePlus,
                 settings: EDASettings, parent=None):
        super().__init__(parent)

        self.mmc = mmc
        self.settings = settings

        self.tabs = QTabWidget()
        self.save_info = SaveGroupBox(parent=self)
        self.save_info.setValue(asdict(settings.save))

        self.overview = OverviewGUI(mmc, settings.overview)
        self.overview.button.pressed.connect(self.run_overview)

        self.scan = ScanGUI(mmc, settings.scan)

        self.acquisition = AcquisitionGUI(mmc, settings.acquisition)

        self.print_btn = QPushButton("Print Settings")
        self.print_btn.pressed.connect(self.print_settings)

        self.tabs.addTab(self.overview, "Overview")
        self.tabs.addTab(self.scan, "Scan")
        self.tabs.addTab(self.settings.analyser.gui.native,  # type:ignore
                         "Analyser")
        self.tabs.addTab(self.acquisition, "Acquisition")

        self.lay = QVBoxLayout()
        self.setLayout(self.lay)
        self.lay.addWidget(self.save_info)
        self.lay.addWidget(self.tabs)
        self.lay.addWidget(self.print_btn)

    def print_settings(self):
        from pprint import pprint
        pprint(self.settings)

    def run_overview(self):
        overview_mda = self.overview.mda.value()
        # TODO make sure obj is set
        self.mmc.run_mda(overview_mda)
        self.fov_select = QOverview()
        self.fov_select.new_fovs.connect(self.rcv_fovs)

    def rcv_fovs(self, fovs):
        print("FOVs received in EDA GUI")
        scan_mda = self.scan.mda.value()
        scan_mda = scan_mda.replace(stage_positions=fovs)
        self.scan.mda.setValue(scan_mda)


class QOverview(QWidgetRestore):
    new_fovs = Signal(list)

    def __init__(self, data=None):
        super().__init__(data)
        self.overview = Overview()
        self.lay = QVBoxLayout()
        self.setLayout(self.lay)
        self.lay.addWidget(self.overview.canvas.native)
        self.super_update_fovs = getattr(self.overview, "update_fovs", None)
        self.overview.update_fovs = self.patched_update_fovs

    def patched_update_fovs(self):
        if self.super_update_fovs:
            self.super_update_fovs()
            self.new_fovs.emit(self.overview.fovs)


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
