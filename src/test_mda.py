from pymmcore_widgets import MDAWidget
from pymmcore_plus import CMMCorePlus
from qtpy.QtWidgets import QApplication
from useq import MDASequence
from useq import Position

mmc = CMMCorePlus().loadSystemConfiguration()
app = QApplication([])
mda = MDAWidget(mmcore=mmc)
seq = MDASequence(stage_positions=((0, 0), (1, 1), (2, 2)),
                  channels=[{"config": "Cy5"}])

seq = seq.replace(stage_positions=[Position(
    x=12.157285381112786, y=114.4050000000002, z=7.875, name=None, sequence=None), Position(
    x=2.157285381112786, y=14.4050000000002, z=7.875, name=None, sequence=None)])
mda.setValue(seq)
mda.show()
print(mda.value())
app.exec_()  # type: ignore
