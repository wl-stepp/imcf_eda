from qtpy.QtWidgets import QWidget, QProgressBar, QGridLayout, QLabel
import time
from datetime import timedelta
from imcf_eda.gui._qt_classes import QWidgetRestore

class MDAProgress(QWidgetRestore):
    def __init__(self, mmcore):
        super().__init__()
        self.mmc = mmcore
        self.lay = QGridLayout()
        self.setLayout(self.lay)

        self.pos_prog = QProgressBar()
        self.pos_label = QLabel('P')
        self.lay.addWidget(self.pos_prog, 0, 1)
        self.lay.addWidget(self.pos_label, 0, 0)

        self.c_prog = QProgressBar()
        self.c_label = QLabel('C')
        self.lay.addWidget(self.c_prog, 1, 1)
        self.lay.addWidget(self.c_label, 1, 0)

        self.z_prog = QProgressBar()
        self.z_label = QLabel('Z')
        self.lay.addWidget(self.z_prog, 2, 1)
        self.lay.addWidget(self.z_label, 2, 0)

        self.time_est = QLabel()
        self.lay.addWidget(self.time_est, 3, 0, 1, 2)

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
        self.c_prog.setMaximum(seq.sizes.get('c', 0))
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
        self.c_prog.setValue(event.index.get('c', 0))
        self.pos_prog.setValue(event.index.get('p', 0))

    def sequenceFinished(self, seq):
        self.pos_prog.setValue(self.pos_prog.maximum())
        self.c_prog.setValue(self.c_prog.maximum())
        self.z_prog.setValue(self.z_prog.maximum())
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
