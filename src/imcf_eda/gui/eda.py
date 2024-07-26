from qtpy.QtWidgets import QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton
from qtpy.QtCore import Signal
from imcf_eda.gui._qt_classes import QWidgetRestore, set_eda, set_dark
from imcf_eda.gui.overview import Overview
from pymmcore_widgets import  MDAWidget
from pymmcore_widgets.mda._save_widget import SaveGroupBox
from pymmcore_plus import CMMCorePlus


class EDAGUI(QWidgetRestore):
    def __init__(self, mmc: CMMCorePlus, parent=None):
        super().__init__(parent)

        self.mmc = mmc

        self.tabs = QTabWidget()
        self.save_info = SaveGroupBox(parent=self)

        self.overview = MDAWidget(mmcore=mmc)
        self.overview.save_info.hide()
        self.overview.control_btns.hide()
        self.overview.tab_wdg.setTabEnabled(0, False)
        self.overview.tab_wdg._cboxes[0].hide() # time
        self.overview.tab_wdg.setTabEnabled(1, False)
        self.overview.tab_wdg._cboxes[1].hide() # position
        self.overview.tab_wdg.setTabEnabled(3, False)
        self.overview.tab_wdg._cboxes[3].hide() # z
        self.overview.setWindowTitle("Overview")

        self.mda_1 = MDAWidget(mmcore=mmc)
        self.mda_1.save_info.hide()
        self.mda_1.control_btns.hide()
        self.mda_1.setWindowTitle("Scan")
        self.mda_1.tab_wdg.setTabEnabled(0, False)
        self.mda_1.tab_wdg._cboxes[0].hide() # time

        self.mda_2 = MDAWidget(mmcore=mmc)
        self.mda_2.save_info.hide()
        self.mda_2.control_btns.hide()
        self.mda_2.setWindowTitle("Acquisition")
        set_eda(self.mda_2)
        self.mda_2.tab_wdg.setTabEnabled(0, False)
        self.mda_2.tab_wdg._cboxes[0].hide() # time

        self.overview_btn = QPushButton("Overview")
        self.overview_btn.pressed.connect(self.run_overview)
        self.scan_btn = QPushButton("Scan")
        self.acquisition_btn = QPushButton("Acquisition")
        self.btn_layout = QHBoxLayout()
        self.btn_layout.addWidget(self.overview_btn)
        self.btn_layout.addWidget(self.scan_btn)
        self.btn_layout.addWidget(self.acquisition_btn)

        self.tabs.addTab(self.overview, "Overview")
        self.tabs.addTab(self.mda_1, "Scan")
        self.tabs.addTab(self.mda_2, "Acquisition")

        self.lay = QVBoxLayout()
        self.setLayout(self.lay)
        self.lay.addWidget(self.save_info)
        self.lay.addWidget(self.tabs)
        self.lay.addLayout(self.btn_layout)

    def run_overview(self):
        overview_mda = self.overview.value()
        self.mmc.run_mda(overview_mda)
        self.fov_select = QOverview()
        self.fov_select.new_fovs.connect(self.rcv_fovs)

    def rcv_fovs(self, fovs):
        print("FOVs received in EDA GUI")
        scan_mda = self.mda_1.value()
        scan_mda = scan_mda.replace(stage_positions = fovs)
        self.mda_1.setValue(scan_mda)


class QOverview(QWidgetRestore):
    new_fovs = Signal(list)
    def __init__(self, data=None):
        super().__init__(data)
        self.overview = Overview()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.overview.canvas.native)
        self.super_update_fovs = getattr(self.overview, "update_fovs", None)
        self.overview.update_fovs = self.patched_update_fovs

    def patched_update_fovs(self):
        self.super_update_fovs()
        self.new_fovs.emit(self.overview.fovs)


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication([])
    from pymmcore_plus import CMMCorePlus
    set_dark(app)
    mmc = CMMCorePlus.instance()
    mmc.loadSystemConfiguration()

    eda = EDAGUI(mmc)
    eda.show()
    app.exec_()
