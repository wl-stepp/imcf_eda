

if __name__ == "__main__":

    from pymmcore_plus import CMMCorePlus

    from imcf_eda.actuator import SpatialActuator
    from imcf_eda.analyser import MIPAnalyser
    from imcf_eda.interpreter import PositionInterpreter
    from imcf_eda.events import EventHub
    from imcf_eda.model import SETTINGS
    from imcf_eda.convenience import init_microscope

    event_hub = EventHub()
    mmc = CMMCorePlus()
    init_microscope(mmc, SETTINGS)

    #Analyser
    analyser = MIPAnalyser(mmc, event_hub)
    mmc.mda.events.frameReady.connect(analyser.frameReady)
    mmc.mda.events.sequenceStarted.connect(analyser.sequenceStarted)
    mmc.mda.events.sequenceFinished.connect(analyser.sequenceFinished)

    #Interpreter
    interpreter = PositionInterpreter(mmc, event_hub)
    mmc.mda.events.sequenceFinished.connect(interpreter.sequenceFinished)

    #actuator
    actuator = SpatialActuator(mmc, event_hub, SETTINGS, analyser, interpreter)

    actuator.start()