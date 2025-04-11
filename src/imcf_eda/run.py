def adjust_demo_config(mmc):
    mmc.setProperty("Camera2", "OnCameraCCDXSize", str(9*256))
    mmc.setProperty("Camera", "OnCameraCCDXSize", 9*256)
    mmc.setProperty("Camera2", "OnCameraCCDYSize", 9*256)
    output = mmc.setProperty("Camera", "OnCameraCCDYSize", 9*256)
    print(output, "FROM SETTING CAMERA")
    mmc.setProperty("Camera2", "BitDepth", "16")
    mmc.setProperty("Camera", "BitDepth", "16")


if __name__ == "__main__":
    import sys
    from pymmcore_plus import CMMCorePlus
    from qtpy.QtWidgets import QApplication
    from imcf_eda.convenience import init_microscope
    app = QApplication([])
    mmc = CMMCorePlus().instance()
    mmc.setDeviceAdapterSearchPaths(["/opt/micro-manager/"] +
                                    list(mmc.getDeviceAdapterSearchPaths()))
    print("ARGUMENT", sys.argv[1])
    print(sys.argv[1] == "demo")
    if sys.argv[1] == "demo":
        init_microscope(mmc, None)

    from imcf_eda.model import EDASettings
    from imcf_eda.controller import Controller
    from imcf_eda.events import EventHub
    from imcf_eda.gui.eda import EDAGUI

    if sys.argv[1] == "demo":
        print("Loading demo settings")
        settings = EDASettings()
    else:
        settings = EDASettings()  # Config loaded here for now
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

        from pymmcore_widgets import PropertyBrowser
        pb = PropertyBrowser()
        pb.show()

        from imcf_eda.gui._preview import Preview
        preview = Preview(mmcore=mmc)
        preview.show()
        event_hub = EventHub()
        # GUI
        view = EDAGUI(mmc, settings, event_hub)
        view.scan.mda.setValue(settings.scan.mda)
        # Controller
        controller = Controller(settings, view, mmc, event_hub, preview)
        view.show()
        try:
            mmc.setExposure("HamamatsuHam_DCAM",
                            settings.overview.mda.channels[0].exposure)
            mmc.setExposure("HamamatsuHam_DCAM-1",
                            settings.overview.mda.channels[0].exposure)
        except:
            print("Exposure could not be set, set manually")
        adjust_demo_config(mmc)

    app.exec_()  # type: ignore
