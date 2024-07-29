import useq


DEMO_SETTINGS = {
    "min_border_distance": 10,
    "analyse_channel" : "FITC",
    "mm_config": False,
    "objective_1": "5-Plan Apo 60x NA 1.42 Oil",
    "objective_2": "6-Plan Apo 100x NA 1.45 Oil",
    "sequence_1": useq.MDASequence(
            # stage_positions = [(0, 0)], # This will be overwritten with the current position
            # channels = [useq.Channel(config="1-DAPI", group="3-Channel"), useq.Channel(config="3-Cy3", group="3-Channel")],
            z_plan = {"range": 5, "step": 1},
            grid_plan={"width": 1000, "height": 1000, "mode": "column_wise", "relative_to": "center"},
            channels=[{'config': 'FITC'}, {'config': 'DAPI'},]
                ),

    "sequence_2": useq.MDASequence(z_plan = {"range": 5, "step": 1},
                                   ),
    "autofocus": False,
    "save": "~/Desktop/imcf_eda"
}


SETTINGS = {
    "mm_config": "C:/Program Files/Micro-Manager-2.0.3_June24/CSU-W1C_4dualcam_piezo.cfg",
    "save": "F:/data/eda_data_027/",

    "objective_1": "5-Plan Apo 60x NA 1.42 Oil",
    "analyser": {"threshold": 0.1, "closing_kernel": (3, 3), "channel": "4-Cy5",
                 "model_path": "F:/imcf_eda/models/unet2d_vish_v4/keras_weights.hdf5"},
    "sequence_1": useq.MDASequence(
            stage_positions = [(0, 0)], # This will be overwritten with the current position
            channels = [useq.Channel(config="4-Cy5", group="3-Channel")],
            z_plan = {"range": 30, "step": 0.3},
            grid_plan={"width": 600, "height": 600, "mode": "column_wise", "relative_to": "center"},
                ),

    "objective_2": "6-Plan Apo 100x NA 1.45 Oil",
    "min_border_distance": 1,
    "z_offset": 4.875,
    "x_offset": -45,
    "y_offset": -11,
    "pixel_size_config": "100x", #('100x', '10x', '25x', '40x', '4x', '60x')
    "sequence_2": useq.MDASequence(z_plan = {"range": 30, "step": 0.3},
                                   channels = [useq.Channel(config="4-Cy5", group="3-Channel"),
                                               useq.Channel(config="3-Cy3", group="3-Channel")],
                                   ),
    "autofocus": False,

}


from magicgui.experimental import guiclass

from typing import Annotated, Literal
OBJECTIVES = Literal["5-Plan Apo 60x NA 1.42 Oil", "6-Plan Apo 100x NA 1.45 Oil"]

@guiclass
class OverviewSettings:
    objective: str = "4x"

@guiclass
class ScanSettings:
    objective: OBJECTIVES = "5-Plan Apo 60x NA 1.42 Oil"

@guiclass
class AnalyserSettings:
    threshold: float = 0.1
    closing_kernel: int = 3
    channel: str = "4-Cy5"
    model_path: str = "F:/imcf_eda/models/unet2d_vish_v4/keras_weights.hdf5"

@guiclass
class AcquisitionSettings:
    min_border_distance: float = 1.
    z_offset: float = 4.875
    x_offset: Annotated[float, {'widget_type': "LineEdit"}] = -45.
    y_offset: Annotated[float, {'widget_type': "LineEdit"}] = -11.
    pixel_size_config: str = "100x" #('100x', '10x', '25x', '40x', '4x', '60x')
    objective: OBJECTIVES = "6-Plan Apo 100x NA 1.45 Oil"
    autofocus: bool = False



# @dataclass
@guiclass
class SETTINGS:


    mm_config: str = "C:/Program Files/Micro-Manager-2.0.3_June24/CSU-W1C_4dualcam_piezo.cfg"
    save: str = "F:/data/eda_data_027/"




if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication([])
    obj = SETTINGS()
    obj.gui.show()
    app.exec_()