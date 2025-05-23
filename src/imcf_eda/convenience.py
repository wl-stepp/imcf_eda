from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from imcf_eda.model import ConfigSettings


def init_microscope(mmc, settings: ConfigSettings | None = None):
    print("settings: ", settings)
    if settings is None:
        mmc.loadSystemConfiguration('/opt/micro-manager/MMConfig_demo.cfg')
        mmc.setProperty("Camera", "OnCameraCCDXSize", 9*256)
        mmc.setProperty("Camera", "OnCameraCCDYSize", 9*256)
        print("camera set to 9*256 pixel")
        return
    elif settings is False:
        pass
    else:
        pass
        # mmc.loadSystemConfiguration(settings.mm_config)
    # mmc.loadSystemConfiguration("C:/Program Files/Micro-Manager-2.0.3_June24/CSU-W1C_4dualcam_piezo_BF.cfg")
    mmc.setConfig("1-System", "Startup-Confocal")
    mmc.setConfig("2-Camera Mode", "1-Single Camera")
    mmc.setProperty("NIDAQAO-Dev1/ao4 561", "Voltage", 1.5)
    mmc.setProperty("NIDAQAO-Dev1/ao0 405", "Voltage", 2)
    mmc.setProperty("NIDAQAO-Dev1/ao2 488", "Voltage", 1.5)
    mmc.setProperty("NIDAQAO-Dev1/ao6 640", "Voltage", 2)
    mmc.setProperty("XYStage", "Speed", "2.50mm/sec")
    mmc.setConfig("5-Z Device", "Piezo Z Stage")
    mmc.setChannelGroup("3-Channel")
    mmc.setConfig("3-Channel", "Brightfield")
    # mmc.setExposure(50.0) does not work somehow, sets to 1000 ms

from qtpy.QtWidgets import QApplication, QWidget
from qtpy.QtGui import QPalette, QColor
from qtpy.QtCore import Qt

def set_dark(app: QApplication):
    app.setStyle("Fusion")
    #
    # # Now use a palette to switch to dark colors:
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.Active, QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, Qt.darkGray)
    dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, Qt.darkGray)
    dark_palette.setColor(QPalette.Disabled, QPalette.Text, Qt.darkGray)
    dark_palette.setColor(QPalette.Disabled, QPalette.Light, QColor(53, 53, 53))
    app.setPalette(dark_palette)
