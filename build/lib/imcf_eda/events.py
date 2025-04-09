import numpy as np
from psygnal import Signal, SignalGroup
from useq import MDASequence

class EventHub(SignalGroup):
    new_positions = Signal(list, float)
    analysis_finished = Signal()
    new_sequence_2 = Signal(MDASequence)