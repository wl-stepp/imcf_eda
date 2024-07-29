from qtpy.QtWidgets import QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton, QWidget
from qtpy.QtCore import Signal
from qtpy.QtGui import QFont

from imcf_eda.gui._qt_classes import QWidgetRestore, set_eda, set_dark
from imcf_eda.gui.overview import Overview
from pymmcore_widgets import  MDAWidget
from pymmcore_widgets.mda._save_widget import SaveGroupBox
from pymmcore_plus import CMMCorePlus
from imcf_eda.model import OverviewSettings, ScanSettings, AcquisitionSettings, AnalyserSettings


class OverviewGUI(QWidget):
    def __init__(self, mmc: CMMCorePlus):
        super().__init__()
        self.lay = QVBoxLayout()
        self.setLayout(self.lay)
        self.mda = MDAWidget(mmcore=mmc)
        self.mda.save_info.hide()
        self.mda.control_btns.hide()
        self.mda.tab_wdg.setTabEnabled(0, False)
        self.mda.tab_wdg._cboxes[0].hide() # time
        self.mda.tab_wdg.setTabEnabled(1, False)
        self.mda.tab_wdg._cboxes[1].hide() # position
        self.mda.tab_wdg.setTabEnabled(3, False)
        self.mda.tab_wdg._cboxes[3].hide() # z
        self.mda.setWindowTitle("Overview")
        self.lay.addWidget(self.mda)

        self.settings = OverviewSettings()
        self.lay.addWidget(self.settings.gui.native)

        self.button = QPushButton("⏵ Run Overview")
        self.button.setFont(QFont('Times', 16))
        self.lay.addWidget(self.button)

class ScanGUI(QWidget):
    def __init__(self, mmc:CMMCorePlus):
        super().__init__()
        self.lay = QVBoxLayout()
        self.setLayout(self.lay)

        self.mda = MDAWidget(mmcore=mmc)
        self.mda.save_info.hide()
        self.mda.control_btns.hide()
        self.mda.setWindowTitle("Scan")
        self.mda.tab_wdg.setTabEnabled(0, False)
        self.mda.tab_wdg._cboxes[0].hide() # time
        self.lay.addWidget(self.mda)

        self.settings = ScanSettings()
        self.lay.addWidget(self.settings.gui.native)

        self.scan_btn = QPushButton("⏵ Scan Only")
        self.scan_btn.setFont(QFont('Times', 16))
        self.scan_acq_btn = QPushButton("⏵ DualScan")
        self.scan_acq_btn.setFont(QFont('Times', 16))
        self.btn_lay = QHBoxLayout()
        self.btn_lay.addWidget(self.scan_btn)
        self.btn_lay.addWidget(self.scan_acq_btn)
        self.lay.addLayout(self.btn_lay)

class AcquisitionGUI(QWidget):
    def __init__(self, mmc:CMMCorePlus):
        super().__init__()
        self.lay = QVBoxLayout()
        self.setLayout(self.lay)

        self.mda = MDAWidget(mmcore=mmc)
        self.mda.save_info.hide()
        self.mda.control_btns.hide()
        self.mda.setWindowTitle("Acquisition")
        self.mda.tab_wdg.setTabEnabled(0, False)
        self.mda.tab_wdg._cboxes[0].hide() # time
        self.lay.addWidget(self.mda)

        self.analyser = AnalyserSettings()
        self.lay.addWidget(self.analyser.gui.native)

        self.settings = AcquisitionSettings()
        self.lay.addWidget(self.settings.gui.native)

        self.acq_btn = QPushButton("⏵ Acquire")
        self.acq_btn.setFont(QFont('Times', 16))
        self.lay.addWidget(self.acq_btn)

        stylesheet = """
        QTabBar::tab:selected {background: blue;}
        QTabWidget>QWidget>QWidget{background: blue;}
        """



class EDAGUI(QWidgetRestore):
    def __init__(self, mmc: CMMCorePlus, parent=None):
        super().__init__(parent)

        self.mmc = mmc
        self.tabs = QTabWidget()
        self.save_info = SaveGroupBox(parent=self)

        self.overview = OverviewGUI(mmc)
        self.overview.button.pressed.connect(self.run_overview)

        self.scan = ScanGUI(mmc)

        self.acquisition = AcquisitionGUI(mmc)

        self.tabs.addTab(self.overview, "Overview")
        self.tabs.addTab(self.scan, "Scan")
        self.tabs.addTab(self.acquisition, "Acquisition")


        self.lay = QVBoxLayout()
        self.setLayout(self.lay)
        self.lay.addWidget(self.save_info)
        self.lay.addWidget(self.tabs)

    def run_overview(self):
        overview_mda = self.overview.mda.value()
        #TODO make sure obj is set
        self.mmc.run_mda(overview_mda)
        self.fov_select = QOverview()
        self.fov_select.new_fovs.connect(self.rcv_fovs)

    def rcv_fovs(self, fovs):
        print("FOVs received in EDA GUI")
        scan_mda = self.scan.mda.value()
        scan_mda = self.scan.mda.replace(stage_positions = fovs)
        self.scan.mda.setValue(scan_mda)


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
