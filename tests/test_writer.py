from imcf_eda.writer import IMCFWriter
from pymmcore_plus import CMMCorePlus
from useq import MDASequence


core = CMMCorePlus()
core.loadSystemConfiguration()

mc = "YoMulti"
core.loadDevice("Camera2", "DemoCamera", "DCam")
core.loadDevice(mc, "Utilities", "Multi Camera")
core.initializeDevice(mc)
core.initializeDevice("Camera2")
core.setProperty("Camera2", "BitDepth", "16")
core.setProperty(mc, "Physical Camera 1", "Camera")
core.setProperty(mc, "Physical Camera 2", "Camera2")
core.setCameraDevice(mc)

seq = MDASequence(channels=['Dual-GFP-Cy5'])


writer = IMCFWriter()


core.mda.run(seq, output=writer)
