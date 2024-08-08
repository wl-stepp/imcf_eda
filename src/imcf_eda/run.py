from pathlib import Path

from useq import MDASequence

if __name__ == "__main__":

    from pymmcore_plus import CMMCorePlus

    from imcf_eda.actuator import SpatialActuator
    from imcf_eda.analyser import MIPAnalyser
    from imcf_eda.interpreter import PositionInterpreter
    from imcf_eda.events import EventHub
    from imcf_eda.model import EDASettings
    from imcf_eda.convenience import init_microscope

    event_hub = EventHub()
    mmc = CMMCorePlus()
    settings = EDASettings()
    settings.scan.mda = MDASequence(stage_positions=((0, 0), (1, 1), (2, 2)),
                                    channels=[{"config": "Cy5"}])
    init_microscope(mmc, settings.config)

    path = Path(settings.save.save_dir) / settings.save.save_name

    # Analyser
    analyser = MIPAnalyser(mmc, event_hub, settings.analyser, path)
    mmc.mda.events.frameReady.connect(analyser.frameReady)
    mmc.mda.events.sequenceStarted.connect(analyser.sequenceStarted)
    mmc.mda.events.sequenceFinished.connect(analyser.sequenceFinished)

    # Interpreter
    interpreter = PositionInterpreter(mmc, event_hub, settings.acquisition,
                                      path)
    mmc.mda.events.sequenceFinished.connect(interpreter.sequenceFinished)

    # actuator
    actuator = SpatialActuator(mmc, event_hub, settings, analyser, interpreter)

    actuator.start()

