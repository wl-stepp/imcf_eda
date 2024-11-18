from pymmcore_plus.mda.handlers import TensorStoreHandler
from pymmcore_plus._logger import logger
from useq import MDASequence, MDAEvent
import numpy as np


class IMCF_writer(TensorStoreHandler):
    def __init__(self, args, kwargs):
        super().__init__(self, args, kwargs)
        self.cameras = []

    def sequenceStarted(self, seq: MDASequence, meta: dict):
        super().sequenceStarted(seq, meta)
        if 'Dual' in seq.channels[0].config:
            self.cameras = [
                x["label"]
                for x in meta["devices"]
                if x["type"] == "CameraDevice" and x["name"] != "Multi Camera"
            ]
        if len(self.cameras) > 1:
            channels = []
            for channel in seq.channels:
                for idx in range(len(self.cameras)):
                    channels.append(
                        channel.replace(
                            config=channel.config.split('-')[idx+1])
                    )
            seq = seq.replace(channels=channels)
        self.current_sequence = seq

    def frameReady(self, frame: np.ndarray, event: MDAEvent, meta: dict):
        if len(self.cameras) > 1:
            new_index = {
                **event.index,
                "c": (
                    len(self.cameras) * event.index.get("c", 0)
                    + self.cameras.index(meta.get("camera_device") or "0")
                ),
            }
            new_channel = self.current_seq.channels[new_index['c']]
            event = event.replace(
                sequence=self.current_sequence, index=new_index, channel=new_channel)
        logger.info(event)
        super().frameReady(frame, event, meta)
