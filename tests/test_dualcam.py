from imcf_eda.writer import IMCFWriter
from pymmcore_plus import CMMCorePlus
from useq import MDASequence


mmc = CMMCorePlus()
mmc.loadSystemConfiguration("C:\Program Files\Micro-Manager-2.0.3_June24\CSU-W1C_4dualcam_piezo_BF.cfg")
mmc.setConfig("1-System", "Startup-Confocal")
mmc.setConfig("2-Camera Mode", "2-Dual Camera")
mmc.setChannelGroup("3-Channel")
mmc.setConfig("3-Channel", "Dual-GFP-Cy5")
mmc.setExposure(50)
mmc.setProperty("NIDAQAO-Dev1/ao4 561", "Voltage", 1.5)
mmc.setProperty("NIDAQAO-Dev1/ao0 405", "Voltage", 2)
mmc.setProperty("NIDAQAO-Dev1/ao2 488", "Voltage", 1.5)
mmc.setProperty("NIDAQAO-Dev1/ao6 640", "Voltage", 2)
mmc.setProperty("XYStage", "Speed", "2.50mm/sec")


seq = MDASequence(channels=[{"config": "Dual-GFP-Cy5", "group": "3-Channel"}],
                  time_plan={'interval': 1, 'loops': 3})


writer = IMCFWriter(path="F:/data/imcf_writer_000.ome.zarr")

mmc.mda.events.frameReady.connect(writer.frameReady)
mmc.mda.events.sequenceStarted.connect(writer.sequenceStarted)
mmc.mda.events.sequenceFinished.connect(writer.sequenceFinished)
mmc.mda.run(seq)