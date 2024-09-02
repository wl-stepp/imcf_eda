from imcf_eda.controller import Controller
from imcf_eda.events import EventHub
from imcf_eda.gui.eda import EDAGUI
from useq import MDASequence

if __name__ == "__main__":

    from pymmcore_plus import CMMCorePlus

    from imcf_eda.model import EDASettings
    from imcf_eda.convenience import init_microscope

    from qtpy.QtWidgets import QApplication
    app = QApplication([])
    mmc = CMMCorePlus()
    settings = EDASettings()
    settings.scan.mda = MDASequence(stage_positions=((0, 0), (1, 1)),
                                    channels=[{"config": "Cy5"}])
    init_microscope(mmc, settings.config)

    event_hub = EventHub()
    # GUI
    view = EDAGUI(mmc, settings, event_hub)
    view.scan.mda.setValue(settings.scan.mda)
    # Controller
    controller = Controller(settings, view, mmc, event_hub)

    view.show()
    app.exec_()  # type: ignore
