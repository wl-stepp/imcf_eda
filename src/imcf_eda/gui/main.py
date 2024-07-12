from qtpy.QtWidgets import  QWidget, QGridLayout, QPushButton, QLabel
from imcf_eda.gui._qt_classes import QWidgetRestore, QMainWindowRestore, set_dark, set_eda
from pymmcore_widgets import (LiveButton, StageWidget, MDAWidget, GroupPresetTableWidget,
                              ExposureWidget)
OBJECTIVES = {
    "100x": "6-Plan Apo 100x NA 1.45 Oil",
    "60x":  "5-Plan Apo 60x NA 1.42 Oil",
    "40x":  "4-Apo 40x NA 1.15 Water",
    "25x":  "3-Plan Apo 25x NA 1.05 Sil",
    "10x":  "2-Plan Apo 10x NA 0.45",
    "4x":   "1-Plan Apo 4x NA 0.2",
}


class MainWindow(QMainWindowRestore):
    def __init__(self, mmc):
        super().__init__()
        self.main = QWidget()
        self.setCentralWidget(self.main)
        self.setWindowTitle("IMCF_EDA")

        self.live_button = LiveButton()
        self.exposure_lbl = QLabel("Exposure")
        self.exposure = ExposureWidget()

        self.dual_scan_lbl = QLabel("DualScan")
        self.overview_button = QPushButton("Overview")
        self.scan_button = QPushButton("Start")
        self.scan_button.pressed.connect(self.scan_acquisition)

        try:
            self.psf_offset = StageWidget("PFSOffset")
            self.xy = StageWidget("XYStage")
        except RuntimeError:
            self.psf_offset = StageWidget("Z")
            self.xy = StageWidget("XY")

        self.group_presets = GroupPresetTableWidget(mmcore=mmc)
        self.overview = MDAWidget(mmcore=mmc)
        self.overview.control_btns.hide()
        self.overview.setWindowTitle("Overview")
        self.overview.show()

        self.group_presets = GroupPresetTableWidget(mmcore=mmc)
        self.mda_1 = MDAWidget(mmcore=mmc)
        self.mda_1.control_btns.hide()
        self.mda_1.setWindowTitle("Scan")
        self.mda_1.show()

        self.mda_2 = MDAWidget(mmcore=mmc)
        self.mda_2.control_btns.hide()
        self.mda_2.setWindowTitle("Acquisition")
        set_eda(self.mda_2)
        self.mda_2.show()

        self.main.setLayout(QGridLayout())
        self.main.layout().addWidget(self.live_button, 0, 0)
        self.main.layout().addWidget(self.exposure_lbl, 1, 0)
        self.main.layout().addWidget(self.exposure, 2, 0)
        self.main.layout().addWidget(self.dual_scan_lbl, 3, 0)
        self.main.layout().addWidget(self.overview_button, 4, 0)
        self.main.layout().addWidget(self.scan_button, 5, 0)

        #Stages
        self.main.layout().addWidget(self.psf_offset, 0, 1, 3, 1)
        self.main.layout().addWidget(self.xy, 0, 2, 3, 1)

        self.main.layout().addWidget(self.group_presets, 6, 0, 1, 3)

    def scan_acquisition(self):
        self._acquisition.settings["sequence"] = self.mda.value()
        self._acquisition.scan_acquisition()


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication([]) 
    set_dark(app)
    from pymmcore_plus import CMMCorePlus
    
    mmc = CMMCorePlus.instance()

    # try:
    from imcf_eda.convenience import init_microscope
    from imcf_eda.model import SETTINGS
    init_microscope(mmc, SETTINGS)

    # mmc.loadSystemConfiguration()

    window = MainWindow(mmc)
    window.show()

    from imcf_eda.gui._preview import Preview
    preview = Preview(mmcore=mmc)
    preview.show()

    app.exec_()