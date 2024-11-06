from imcf_eda.controller import Controller
from imcf_eda.events import EventHub
from imcf_eda.gui.eda import EDAGUI

if __name__ == "__main__":
    import sys
    from pymmcore_plus import CMMCorePlus

    from imcf_eda.model import EDASettings
    from imcf_eda.convenience import init_microscope
    from qtpy.QtWidgets import QApplication
    app = QApplication([])
    mmc = CMMCorePlus().instance()
    if sys.argv[1] == "demo":
        print("Loading demo settings")
        settings = EDASettings()
        init_microscope(mmc, None)
    else:
        settings = EDASettings() # Config loaded here for nows
        init_microscope(mmc, False)  # Only set values don't load config

    if len(sys.argv) == 1:
        event_hub = EventHub()
        # GUI
        view = EDAGUI(mmc, settings, event_hub)
        view.scan.mda.setValue(settings.scan.mda)
        # Controller
        controller = Controller(settings, view, mmc, event_hub)
        view.show()
    elif sys.argv[1] == "no_eda":
        from imcf_eda.gui.main import MainWindow
        window = MainWindow(mmc)
        window.show()

        from imcf_eda.gui._preview import Preview
        preview = Preview(mmcore=mmc)
        preview.show()
    elif sys.argv[1] == "all" or sys.argv[1] == "demo":
        
        from imcf_eda.gui.main import MainWindow
        window = MainWindow(mmc)
        window.show()

        from imcf_eda.gui._preview import Preview
        preview = Preview(mmcore=mmc)
        preview.show()
        event_hub = EventHub()
        # GUI
        view = EDAGUI(mmc, settings, event_hub)
        view.scan.mda.setValue(settings.scan.mda)
        # Controller
        controller = Controller(settings, view, mmc, event_hub)  #, preview)
        view.show()

    app.exec_()  # type: ignore
