from pymmcore_plus import CMMCorePlus
from typing import Annotated, Literal
from dataclasses import dataclass, field
from magicgui.experimental import guiclass
import useq


@dataclass
class DisplaySettings:
    rotation: int = 270
    flipud: bool = True
    fliplr: bool = False


class ConfigSettings:
    # "C:/Program Files/Micro-Manager-2.0.3_June24/CSU-W1C_4dualcam_piezo.cfg"
    mm_config: str | None = None
    objective_group: str = "Objective"
    objectives: tuple[str, ...] = ()
    pixel_sizes: tuple[str, ...] = ()
    display: DisplaySettings = field(default_factory=DisplaySettings)

    def __init__(self):
        mmc = CMMCorePlus().instance()
        if self.mm_config:
            mmc.loadSystemConfiguration(self.mm_config)
        else:
            mmc.loadSystemConfiguration()
        self.objectives = mmc.getAvailableConfigs(self.objective_group)
        self.pixel_sizes = mmc.getAvailablePixelSizeConfigs()


@guiclass
class OverviewSettings:
    objective:  Literal[
        *ConfigSettings().objectives  # type:ignore
    ] = ConfigSettings().objectives[-1]


@dataclass
class OverviewMDASettings:
    parameters: OverviewSettings = field(default_factory=OverviewSettings)
    mda: useq.MDASequence = field(default_factory=useq.MDASequence)


@guiclass
class ScanSettings:
    objective: Literal[
        *ConfigSettings().objectives  # type:ignore
    ] = ConfigSettings().objectives[-1]


@dataclass
class ScanMDASettings:
    parameters: ScanSettings = field(default_factory=ScanSettings)
    mda: useq.MDASequence = field(default_factory=useq.MDASequence)


@guiclass
class AnalyserSettings:
    threshold: float = 0.1
    closing_kernel: int = 3
    channel: str = "Cy5"
    model_path: str = ("/home/stepp/Documents/Data/models_basel/"
                       "unet2d_vish_v4/keras_weights.hdf5")
    orientation: DisplaySettings = field(default_factory=DisplaySettings)


@guiclass
class AcquisitionSettings:
    min_border_distance: float = 1.
    z_offset: float = 4.875
    x_offset: Annotated[float, {'widget_type': "LineEdit"}] = -45.
    y_offset: Annotated[float, {'widget_type': "LineEdit"}] = -11.
    # ('100x', '10x', '25x', '40x', '4x', '60x')
    pixel_size_config: Literal[
        *ConfigSettings().pixel_sizes  # type:ignore
    ] = ConfigSettings().pixel_sizes[-1]

    objective: Literal[
        *ConfigSettings().objectives  # type:ignore
    ] = ConfigSettings().objectives[-1]
    autofocus: bool = False


@dataclass
class AcquisitionMDASettings:
    parameters: AcquisitionSettings = field(
        default_factory=AcquisitionSettings)
    mda: useq.MDASequence = field(default_factory=useq.MDASequence)


@dataclass
class SaveInfo:
    save_dir: str = "/home/stepp/Desktop/"
    save_name: str = "eda_000"
    format: str = "ome-zarr"
    should_save: bool = True


@dataclass
class EDASettings:
    config: ConfigSettings = field(default_factory=ConfigSettings)

    overview: OverviewMDASettings = field(default_factory=OverviewMDASettings)
    scan: ScanMDASettings = field(default_factory=ScanMDASettings)
    analyser: AnalyserSettings = field(default_factory=AnalyserSettings)
    acquisition: AcquisitionMDASettings = field(
        default_factory=AcquisitionMDASettings)

    save: SaveInfo = field(default_factory=SaveInfo)


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication([])
    app.exec_()  # type:ignore
