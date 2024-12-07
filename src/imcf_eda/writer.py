from __future__ import annotations
from pymmcore_plus.mda.handlers import TensorStoreHandler
from pymmcore_plus._logger import logger
import numpy as np

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pymmcore_plus.metadata import FrameMetaV1, SummaryMetaV1
    from useq._mda_sequence import MDASequence
    from useq._mda_event import MDAEvent

_NULL = object()

class IMCFWriter(TensorStoreHandler):
    def __init__(self, path):
        super().__init__(path=path)
        self.cameras = []

    def sequenceStarted(self, seq: MDASequence, meta: SummaryMetaV1 | object = _NULL):
        if 'Dual' in seq.channels[0].config:
            self.cameras = [
                x["label"]
                for x in meta["devices"]
                if x["type"] == "CameraDevice" and x["name"] != "Multi Camera"
            ]
        print(self.cameras)
        if len(self.cameras) > 1:
            channels = []
            for channel in seq.channels:
                for idx in range(len(self.cameras)):
                    channels.append(
                        channel.replace(
                            config=channel.config.split('-')[idx+1])
                    )
            seq = seq.replace(channels=channels)
        super().sequenceStarted(seq, meta)
        self.current_sequence = seq

    def frameReady(self, frame: np.ndarray, event: MDAEvent, meta: FrameMetaV1 = _NULL):
        if len(self.cameras) > 1:
            new_index = {
                **event.index,
                "c": (
                    len(self.cameras) * event.index.get("c", 0)
                    + self.cameras.index(meta.get("camera_device") or "0")
                ),
            }
            new_channel = self.current_sequence.channels[new_index['c']]
            event = event.replace(
                sequence=self.current_sequence, index=new_index, channel={'config': new_channel.config})
        if len(self.cameras) > 1 and event.index.get('c', 0)%2 == 1:
            frame = np.flip(frame, -2)
        super().frameReady(frame, event, meta)

    def sequenceFinished(self, seq: MDASequence = _NULL) -> None:
        super().sequenceFinished(seq)