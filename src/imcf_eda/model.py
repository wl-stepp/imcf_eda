from pymmcore_plus import CMMCorePlus
from typing import Annotated, Literal
from dataclasses import dataclass, field, asdict
from magicgui.experimental import guiclass
import useq


@guiclass
class DisplaySettings:
    rotation: int = 270
    flipud: bool = True
    fliplr: bool = False


class ConfigSettings:
    # "C:/Program Files/Micro-Manager-2.0.3_June24/CSU-W1C_4dualcam_piezo.cfg"
    # mm_config: str | None = "C:\Program Files\Micro-Manager-2.0.3_June24\CSU-W1C_4dualcam_piezo_BF.cfg"
    # objective_group: str = "4-Objective"
    # channel_group: str = "3-Channel"
    # corse_z_stage: str = "ZDrive"
    mm_config: str | None = None 
    objective_group: str = "Objective"
    channel_group: str = "Channel"
    corse_z_stage: str = "Z"
    objectives: tuple[str, ...] = ()
    channels: tuple[str, ...] = ()
    pixel_sizes: tuple[str, ...] = ()
    display: DisplaySettings = field(default_factory=DisplaySettings)

    def __init__(self):
        mmc = CMMCorePlus().instance()
        if self.mm_config:
            try:
                mmc.loadSystemConfiguration(self.mm_config)
            except FileNotFoundError:
                mmc.loadSystemConfiguration()
        else:
            mmc.loadSystemConfiguration()
        self.objectives = mmc.getAvailableConfigs(self.objective_group)
        self.channels = mmc.getAvailableConfigs(self.channel_group)
        self.pixel_sizes = mmc.getAvailablePixelSizeConfigs()


settings = ConfigSettings()
objectives = settings.objectives
pixel_sizes = settings.pixel_sizes
channels = settings.channels

@guiclass
class OverviewSettings:
    objective:  Literal[
        objectives  # type:ignore
    ] = settings.objectives[0]



@dataclass
class OverviewMDASettings:
    parameters: OverviewSettings = field(default_factory=OverviewSettings)
    mda: useq.MDASequence = field(default_factory=useq.MDASequence)


@guiclass
class ScanSettings:
    objective: Literal[
        objectives  # type:ignore
    ] = settings.objectives[-2]
    preview_channel: Literal[channels] = settings.channels[0]


@dataclass
class ScanMDASettings:
    parameters: ScanSettings = field(default_factory=ScanSettings)
    mda: useq.MDASequence = useq.MDASequence(z_plan={"range": 4, "step": 0.3}, channels=["4-Cy5", "3-Cy3"],)


@guiclass
class AnalyserSettings:
    threshold: float = 0.5
    closing_kernel: int = 3
    channel: Literal[channels] = settings.channels[3]
    model_path: str = ("F:/imcf_eda/models/"
                       #"unet2d_vish_v8/weights_best.hdf5"
                       "unet2d_vish_v4/keras_weights.hdf5")

    def __post_init__(self):
        self.orientation: DisplaySettings = DisplaySettings()


@guiclass
class AcquisitionSettings:
    min_border_distance: float = 1.
    z_offset: float = 2.42
    x_offset: Annotated[float, {'widget_type': "LineEdit"}] = -7
    y_offset: Annotated[float, {'widget_type': "LineEdit"}] = 16
    # ('100x', '10x', '25x', '40x', '4x', '60x')
    pixel_size_config: Literal[
        pixel_sizes  # type:ignore
    ] = settings.pixel_sizes[0]

    objective: Literal[
        objectives  # type:ignore
    ] = settings.objectives[-1]
    autofocus: bool = False


@dataclass
class AcquisitionMDASettings:
    parameters: AcquisitionSettings = field(
        default_factory=AcquisitionSettings)
    mda: useq.MDASequence = useq.MDASequence(z_plan={"range": 4, "step": 0.5}, channels=["4-Cy5", "3-Cy3"])


@dataclass
class SaveInfo:
    save_dir: str = "F:/data"
    save_name: str = "2410_005"
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

    def as_dict(self):
        return asdict(self)


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication([])
    app.exec_()  # type:ignore
