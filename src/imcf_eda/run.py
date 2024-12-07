def adjust_demo_config(mmc):
    mc = "YoMulti"
    mmc.loadDevice("Camera2", "DemoCamera", "DCam")
    mmc.loadDevice(mc, "Utilities", "Multi Camera")
    mmc.initializeDevice(mc)
    mmc.initializeDevice("Camera2")
    mmc.setProperty("Camera2", "OnCameraCCDXSize", 9*256)
    mmc.setProperty("Camera2", "OnCameraCCDYSize", 9*256)
    mmc.setProperty("Camera2", "BitDepth", "16")
    mmc.setProperty(mc, "Physical Camera 1", "Camera")
    mmc.setProperty(mc, "Physical Camera 2", "Camera2")
    mmc.setCameraDevice(mc)
    configs = mmc.getConfigState("Channel", "DAPI")
    for config in configs:
        device = config[0]
        property = config[1]
        value = config[2]
        mmc.defineConfig("Channel", "Dual-GFP-Cy5",
                         device, property, value)
    mmc.setConfig("Channel", "Dual-GFP-Cy5")
    print('Dual config added')


if __name__ == "__main__":
    import sys
    from pymmcore_plus import CMMCorePlus
    from qtpy.QtWidgets import QApplication
    from imcf_eda.convenience import init_microscope
    app = QApplication([])
    mmc = CMMCorePlus().instance()
    if sys.argv[1] == "demo":
        init_microscope(mmc, None)
        adjust_demo_config(mmc)
        print(mmc.getConfigState("Channel", "Dual-GFP-Cy5"))

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
            mmc.setExposure("HamamatsuHam_DCAM", settings.overview.mda.channels[0].exposure)
            mmc.setExposure("HamamatsuHam_DCAM-1", settings.overview.mda.channels[0].exposure)
        except:
            print("Exposure could not be set, set manually")

    app.exec_()  # type: ignore
