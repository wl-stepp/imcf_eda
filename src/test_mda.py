
from pymmcore_plus import CMMCorePlus
from pymmcore_plus.mda.handlers import OMEZarrWriter
from useq import MDASequence
from imcf_eda.convenience import init_microscope
from imcf_eda.model import ConfigSettings


setting = ConfigSettings()
mmc = CMMCorePlus().instance()
init_microscope(mmc, False)
writer = OMEZarrWriter('F:/data/dual_cam_01.ome.zarr', overwrite=True)
mmc.setConfig("2-Camera Mode", "2-Dual Camera")
seq = MDASequence(channels=[{"config": "Dual-DAPI-Cy3", "group": '3-Channel'}])
print(seq.sizes)
mmc.run_mda(seq, block=True, output=writer)

