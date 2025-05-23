from pymmcore_plus import CMMCorePlus
from typing import Annotated, Literal
from dataclasses import dataclass, field, asdict
from magicgui.experimental import guiclass
import useq
import time
import yaml
from datetime import datetime
from pathlib import Path


@guiclass
class DisplaySettings:
    rotation: int = 270
    flipud: bool = True
    fliplr: bool = False


class ConfigSettings:
    # "C:/Program Files/Micro-Manager-2.0.3_June24/CSU-W1C_4dualcam_piezo.cfg"
    # IMCF
    # mm_config: str | None = "C:\Program Files\Micro-Manager-2.0.3_June24\CSU-W1C_4dualcam_piezo_BF.cfg"
    # objective_group: str = "4-Objective"
    # channel_group: str = "3-Channel"
    # corse_z_stage: str = "ZDrive (Nosepiece)"
    # default_analyser_channel_idx = 8
    # DEMO
    mm_config: str | None = "/opt/micro-manager/MMConfig_imcf.cfg"
    objective_group: str = "Objective"
    channel_group: str = "Channel"
    corse_z_stage: str = "Z"
    objectives: tuple[str, ...] = ()
    channels: tuple[str, ...] = ()
    pixel_sizes: tuple[str, ...] = ()
    display: DisplaySettings = field(default_factory=DisplaySettings)
    default_analyser_channel_idx = 0

    camera_setting: str = "2-Camera Mode"
    camera_single: str = "1-Single Camera"
    camera_dual: str = "2-Dual Camera"

    def __init__(self):
        mmc = CMMCorePlus().instance()
        loaded = False
        t0 = time.perf_counter()
        while not loaded:
            try:
                mmc.loadSystemConfiguration(self.mm_config)
                loaded = True
            except Exception as e:
                print(e)
                time.sleep(3)
                print("microscope not ready, retry",
                      round(time.perf_counter() - t0))
        self.objectives = mmc.getAvailableConfigs(self.objective_group)
        self.channels = mmc.getAvailableConfigs(self.channel_group)
        self.pixel_sizes = mmc.getAvailablePixelSizeConfigs()

        self.analyser_channels = []
        # for the analyser, the dual channels will be split up
        for channel in self.channels:
            if 'Dual' in channel:
                self.analyser_channels.append(channel.split('-')[1])
                self.analyser_channels.append(channel.split('-')[2])
            else:
                self.analyser_channels.append(channel)
        self.analyser_channels = tuple(self.analyser_channels)


settings = ConfigSettings()
objectives = settings.objectives
pixel_sizes = settings.pixel_sizes
channels = settings.channels
analyser_channels = settings.analyser_channels


@guiclass
class OverviewSettings:
    fov_size: float = 260.7
    x_offset: Annotated[float, {'widget_type': "LineEdit"}] = -44.4
    y_offset: Annotated[float, {'widget_type': "LineEdit"}] = 102.7
    objective:  Literal[
        objectives  # type:ignore
    ] = settings.objectives[0]


@dataclass
class OverviewMDASettings:
    parameters: OverviewSettings = field(default_factory=OverviewSettings)
    mda: useq.MDASequence = useq.MDASequence(
        channels=[{"config": "Brightfield", "exposure": 50.0, "group": settings.channel_group}])


@guiclass
class ScanSettings:
    objective: Literal[
        objectives  # type:ignore
    ] = settings.objectives[-2]


@dataclass
class ScanMDASettings:
    parameters: ScanSettings = field(default_factory=ScanSettings)
    mda: useq.MDASequence = useq.MDASequence(z_plan={"range": 2.55, "step": 0.3},  # 25.5
                                             channels=[
                                                 {"config": "Dual-GFP-Cy5", "exposure": 200, "group": settings.channel_group}],
                                             axis_order='pcz',
                                             keep_shutter_open_across=['z'])


@guiclass
class AnalyserSettings:
    mode: bool = settings.corse_z_stage == "Z"
    threshold: float = 0.6
    closing_kernel: int = 3
    channel: Literal[analyser_channels] = settings.analyser_channels[settings.default_analyser_channel_idx]
    model_path: str = ("F:/imcf_eda/models/"
                       # "unet2d_vish_v8/weights_best.hdf5"
                       # "unet2d_vish_v4/keras_weights.hdf5"
                       # "stardist2D_vish_v3/keras.h5"
                       "saures_stardist2D_v17/saures_stardist2D_v17_keras.h5"
                       #    "unet2d_vish_v8\weights_best.hdf5"
                       )
    tile_size: int = 128

    def __post_init__(self):
        self.orientation: DisplaySettings = DisplaySettings()


@guiclass
class AcquisitionSettings:
    min_border_distance: float = 1.
    z_offset: Annotated[float, {'widget_type': "LineEdit"}] = 0  # 77.9
    x_offset: Annotated[float, {'widget_type': "LineEdit"}] = 13.2
    y_offset: Annotated[float, {'widget_type': "LineEdit"}] = 33.7
    # ('100x', '10x', '25x', '40x', '4x', '60x')
    pixel_size_config: Literal[
        pixel_sizes  # type:ignore
    ] = settings.pixel_sizes[0]

    objective: Literal[
        objectives  # type:ignore
    ] = settings.objectives[-1]
    autofocus: bool = False

    def __init__(self):
        try:
            with open(Path(__file__).parents[-2] / 'mic_settings.yaml', 'r') as file:
                settings = yaml.safe_load(file)
            self.z_offset = settings['offsets']['100x']['z']
            self.x_offset = settings['offsets']['100x']['x']
            self.y_offset = settings['offsets']['100x']['y']
        except:
            print('Could not load offsets from mic_settings.yaml file')


@dataclass
class AcquisitionMDASettings:
    parameters: AcquisitionSettings = field(
        default_factory=AcquisitionSettings)
    mda: useq.MDASequence = useq.MDASequence(
        z_plan={"range": 4, "step": 1},  # 30.5
        channels=[{"config": "Dual-GFP-Cy5", "exposure": 200, "group": settings.channel_group},
                  {"config": "Dual-DAPI-Cy3", "exposure": 200, "group": settings.channel_group}],
        axis_order='pcz',
        keep_shutter_open_across=['z'])


@dataclass
class SaveInfo:
    save_dir: str = "F:/data"
    save_name: str = datetime.now().strftime("%y%m%d") + '_000'
    format: str = "ome-zarr"
    should_save: bool = True


@dataclass
class EDASettings:
    config: ConfigSettings = field(default_factory=ConfigSettings)

    overview: OverviewSettings = field(default_factory=OverviewMDASettings)
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
