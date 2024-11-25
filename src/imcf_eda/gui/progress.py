from qtpy.QtWidgets import QWidget, QProgressBar, QVBoxLayout, QLabel
import time
from datetime import timedelta


class MDAProgress(QWidget):
    def __init__(self, mmcore):
        super().__init__()
        self.mmc = mmcore
        self.lay = QVBoxLayout()
        self.setLayout(self.lay)

        self.pos_prog = QProgressBar()
        self.lay.addWidget(self.pos_prog)

        self.z_prog = QProgressBar()
        self.lay.addWidget(self.z_prog)

        self.time_est = QLabel()
        self.lay.addWidget(self.time_est)

        self.mmc.mda.events.sequenceStarted.connect(self.sequenceStarted)
        self.mmc.mda.events.frameReady.connect(self.frameReady)
        self.mmc.mda.events.sequenceFinished.connect(self.sequenceFinished)

        self.pos_timer = 0
        self.pos_time = 0
        self.timer_stopped = True

    def sequenceStarted(self, seq, metadata):
        self.show()
        self.pos_prog.setMaximum(seq.sizes.get('p', 0))
        self.z_prog.setMaximum(seq.sizes.get('z', 0))
        self.time_est.setText('')

    def frameReady(self, frame, event, meta):
        if sum(event.index.values()) == 0:
            self.pos_timer = time.perf_counter()
            self.timer_stopped = False
        elif event.index.get('p', 0) > 0:
            if not self.timer_stopped:
                self.pos_time = time.perf_counter() - self.pos_timer
                self.timer_stopped = True
            seq_time = self.pos_time * \
                (event.sequence.sizes.get('p', 1) - event.index.get('p'))
            rem_time = self.custom_format_time(seq_time)
            self.time_est.setText("Time Remaining:" + rem_time)
        self.z_prog.setValue(event.index.get('z', 0))
        self.pos_prog.setValue(event.index.get('p', 0))

    def sequenceFinished(self, seq):
        self.pos_prog.setValue(self.pos_prog.maximum())
        self.time_est.setText("Time Remaining: 0s")

    def custom_format_time(self, seconds):
        td = timedelta(seconds=seconds)
        days, seconds = divmod(td.total_seconds(), 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        parts = []
        if days > 0:
            parts.append(f"{int(days)}d")
        if hours > 0:
            parts.append(f"{int(hours)}h")
        if minutes > 0:
            parts.append(f"{int(minutes)}m")
        parts.append(f"{int(seconds)}s")

        return " ".join(parts)


if __name__ == '__main__':
    from pymmcore_plus import CMMCorePlus
    from useq import MDASequence
    from qtpy.QtWidgets import QApplication

    app = QApplication([])

    mmc = CMMCorePlus.instance()
    mmc.loadSystemConfiguration()

    seq = MDASequence(stage_positions=[(0, 0, 0), (1, 1, 0), (2, 2, 0), (3, 3, 0),
                                       (0, 0, 0), (1, 1, 0), (2, 2, 0), (3, 3, 0),
                                       # (0, 0, 0), (1, 1, 0), (2, 2, 0), (3, 3, 0),
                                       # (0, 0, 0), (1, 1, 0), (2, 2, 0), (3, 3, 0),
                                       # (0, 0, 0), (1, 1, 0), (2, 2, 0), (3, 3, 0),
                                       # (0, 0, 0), (1, 1, 0), (2, 2, 0), (3, 3, 0),
                                       # (0, 0, 0), (1, 1, 0), (2, 2, 0), (3, 3, 0),
                                       ],
                      channels=[{'config': 'DAPI', 'exposure': 100}, ],
                      z_plan={'range': 100, 'step': 1})
    prog = MDAProgress(mmc)
    mmc.run_mda(seq)

    app.exec_()
