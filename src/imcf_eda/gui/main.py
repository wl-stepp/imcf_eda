from qtpy.QtWidgets import QWidget, QGridLayout, QPushButton, QLabel
from imcf_eda.gui._qt_classes import (QMainWindowRestore,
                                      set_dark, set_eda)
from imcf_eda.gui.calibrate_obj import CalibrationCanvas
from pymmcore_widgets import (LiveButton, StageWidget, MDAWidget,
                              GroupPresetTableWidget, ExposureWidget)


class MainWindow(QMainWindowRestore):
    def __init__(self, mmc):
        super().__init__()
        self.main = QWidget()
        self.mmc = mmc
        self.setCentralWidget(self.main)
        self.setWindowTitle("IMCF_EDA")

        self.live_button = LiveButton()
        self.exposure_lbl = QLabel("Exposure")
        self.exposure = ExposureWidget()
        self.calibrate = None
        self.calibrate_btn = QPushButton('Calibrate')
        self.calibrate_btn.pressed.connect(self.start_calibration)
        try:
            self.psf_offset = StageWidget("ZDrive (Nosepiece)")
            self.xy = StageWidget("XYStage")
        except RuntimeError:
            self.psf_offset = StageWidget("Z")
            self.xy = StageWidget("XY")

        self.group_presets = GroupPresetTableWidget(mmcore=mmc)

        self.main.setLayout(QGridLayout())
        self.main.layout().addWidget(self.live_button, 0, 0)
        self.main.layout().addWidget(self.exposure_lbl, 1, 0)
        self.main.layout().addWidget(self.exposure, 2, 0)

        # Stages
        self.main.layout().addWidget(self.psf_offset, 0, 1, 3, 1)
        self.main.layout().addWidget(self.xy, 0, 2, 3, 1)

        self.main.layout().addWidget(self.group_presets, 6, 0, 1, 3)
        self.main.layout().addWidget(self.calibrate_btn, 7, 0)

    def start_calibration(self):
        self.calibrate = CalibrationCanvas(self.mmc)


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication([])
    set_dark(app)
    from pymmcore_plus import CMMCorePlus

    mmc = CMMCorePlus.instance()

    try:
        from imcf_eda.convenience import init_microscope
        from imcf_eda.model import SETTINGS
        init_microscope(mmc, SETTINGS)
    except:
        mmc.loadSystemConfiguration()

    window = MainWindow(mmc)
    window.show()

    from imcf_eda.gui._preview import Preview
    preview = Preview(mmcore=mmc)
    preview.show()

    app.exec_()
