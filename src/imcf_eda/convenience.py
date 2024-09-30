from imcf_eda.model import ConfigSettings


def init_microscope(mmc, settings: ConfigSettings = None):
    if settings is None:
        mmc.loadSystemConfiguration()
        mmc.setProperty("Camera", "OnCameraCCDXSize", 9*256)
        mmc.setProperty("Camera", "OnCameraCCDYSize", 9*256)
        return
    elif settings is False:
        pass
    else:
        mmc.loadSystemConfiguration(settings.mm_config)
    # mmc.loadSystemConfiguration("C:/Program Files/Micro-Manager-2.0.3_June24/CSU-W1C_4dualcam_piezo.cfg")
    mmc.setConfig("1-System", "Startup-Confocal")
    mmc.setConfig("2-Camera Mode", "1-Single Camera")
    mmc.setConfig("3-Channel", "Dual-DAPI-Cy3")
    mmc.setProperty("NIDAQAO-Dev1/ao4 561", "Voltage", 1.5)
    mmc.setProperty("NIDAQAO-Dev1/ao0 405", "Voltage", 2)
    mmc.setProperty("NIDAQAO-Dev1/ao6 640", "Voltage", 2)
    mmc.setProperty("XYStage", "Speed", "2.50mm/sec")
    mmc.setChannelGroup("3-Channel")
