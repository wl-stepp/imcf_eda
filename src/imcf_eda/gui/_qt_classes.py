"""Customized Qt classes for overall GUI behaviour."""

from qtpy import QtWidgets, QtCore


class QMainWindowRestore(QtWidgets.QMainWindow):
    """QMainWindow that saves its last position to the registry and loads it when opened again.

    Also closes all the other windows that are open in the application.
    """

    def __init__(self, parent=None):
        """Load the settings in the registry an reset position. If no present, use default."""
        super().__init__(parent=parent)
        self.qt_settings = QtCore.QSettings("EDA", self.__class__.__name__)
        # Initial window size/pos last saved. Use default values for first time
        self.resize(self.qt_settings.value("size", QtCore.QSize(270, 225)))
        self.move(self.qt_settings.value("pos", QtCore.QPoint(50, 50)))

    def closeEvent(self, e):
        """Write window size and position to config file."""
        self.qt_settings.setValue("size", self.size())
        self.qt_settings.setValue("pos", self.pos())
        # Close all other windows too
        app = QtWidgets.QApplication.instance()
        app.closeAllWindows()
        e.accept()


class QWidgetRestore(QtWidgets.QWidget):
    """QWidget that saves its last position to the registry and loads it when opened again.

    Also closes all the other windows that are open in the application.
    """

    def __init__(self, parent=None, close_all=False):
        """Load the settings in the registry an reset position. If no present, use default."""
        super().__init__(parent=parent)
        self.close_all = close_all
        self.qt_settings = QtCore.QSettings("EDA", self.__class__.__name__)
        # Initial window size/pos last saved. Use default values for first time
        self.resize(self.qt_settings.value("size", QtCore.QSize(270, 225)))
        self.move(self.qt_settings.value("pos", QtCore.QPoint(50, 50)))

    def closeEvent(self, e):
        """Write window size and position to config file."""
        self.qt_settings.setValue("size", self.size())
        self.qt_settings.setValue("pos", self.pos())
        # Close all other windows too
        if self.close_all:
            app = QtWidgets.QApplication.instance()
            app.closeAllWindows()
            e.accept()
        else:
            super().closeEvent(e)


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

def set_eda(widget: QWidget):
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(31,53,69))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(49,89,114)) #
    dark_palette.setColor(QPalette.AlternateBase, QColor(31,53,69))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(13,23,36))
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(31,53,69))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, QColor(31,53,69)) #
    dark_palette.setColor(QPalette.Active, QPalette.Button, QColor(31,53,69))
    dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, Qt.darkGray)
    dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, Qt.darkGray)
    dark_palette.setColor(QPalette.Disabled, QPalette.Text, Qt.darkGray)
    dark_palette.setColor(QPalette.Disabled, QPalette.Light, QColor(31,53,69))
    widget.setPalette(dark_palette)