
# 0.0 for loading in napari
merge = np.zeros([int(np.sqrt(viewer.layers[0].data.shape[0]))*x for x in viewer.layers[0].data.shape][1:])
seq = list(useq.MDASequence(grid_plan={"fov_width": 1, "fov_height": 1, "height": int(np.sqrt(viewer.layers[0].data.shape[0])), "width": int(np.sqrt(viewer.layers[0].data.shape[0])), "mode": "column_wise", "relative_to": "top_left"}))
for i, img in enumerate(viewer.layers[0].data):
    x , y = int(np.sqrt(viewer.layers[0].data.shape[0])) - int(seq[i].x_pos) -1,  abs(int(seq[i].y_pos)) 
    merge[(y)*viewer.layers[0].data.shape[1]:(y+1)*viewer.layers[0].data.shape[1],
          x*viewer.layers[0].data.shape[2]:(x + 1)*viewer.layers[0].data.shape[2]] = img
viewer.add_image(merge)




# Get metadata in napari for loaded zarr storage in napari terminal
import json
from pathlib import Path
with open(Path(viewer.layers[0].source.path) / "eda_meta.json","r") as file:
    metadata = json.load(file)

from napari import Viewer
viewer = Viewer()
# Better version to distribute stuff in napari
# This should also be easier to adjust for overlap for example

#ATTENTION: Napari caches these datastores. That can become weird if data is overwritten
#SCAN

import useq, json, pathlib
from napari.experimental import link_layers
from tqdm import tqdm
import numpy as np
from qtpy.QtWidgets import QApplication


def adjust_one_array(viewer, color = "white",  offsets ={"x_offset": -44.4, "y_offset": 102.7,}):
    layer_n = len(viewer.layers) - 1
    with open(pathlib.Path(viewer.layers[layer_n].source.path) / "p0/.zattrs","r") as file:
        metadata = json.load(file)

    metadata["frame_meta"][0]["pixel_size_um"] = 1.69835
    # viewer.layers[layer_n].data = viewer.layers[layer_n].data[viewer.layers[layer_n].data.shape[0]-1, :, :]
    layers = []
    if len(viewer.layers[layer_n].data.shape) > 2:
        shape = viewer.layers[layer_n].data.shape
    else:
        shape = [1]
    for i, img in enumerate(range(shape[0])):
        if len(shape)>1:
            layer = viewer.add_image(viewer.layers[layer_n].data[img], colormap=viewer.layers[0].colormap)
            layer.translate = [metadata["frame_meta"][i]['position']['x'] + metadata["useq_MDASequence"]["grid_plan"]["fov_width"]/2,
                               metadata["frame_meta"][i]['position']['y'] + metadata["useq_MDASequence"]["grid_plan"]["fov_height"]/2]
        else:
            layer = viewer.add_image(viewer.layers[layer_n].data, colormap=viewer.layers[0].colormap)
            scale = metadata["frame_meta"][0]["pixel_size_um"]
            layer.translate = [metadata["frame_meta"][i]['position']['x'] + scale*viewer.layers[layer_n].data.shape[0]/2 + offsets["x_offset"],
                               metadata["frame_meta"][i]['position']['y'] + scale*viewer.layers[layer_n].data.shape[1]/2 + offsets["y_offset"]]        

        layer.rotate = -90
        layer.scale = [metadata["frame_meta"][0]["pixel_size_um"], -metadata["frame_meta"][0]["pixel_size_um"]]
        layer.blending = 'additive'
        layer.colormap = color
        layers.append(layer)
    print(metadata["frame_meta"][i]['position']['x'], metadata["frame_meta"][i]['position']['y'])
    print(metadata["frame_meta"][0]["pixel_size_um"])
    link_layers(layers)
    viewer.layers[layer_n].visible = False

    viewer.dims.current_step = (0, viewer.layers[layer_n].data.shape[1]-1, *viewer.dims.current_step[-2:])
    layers[-1].reset_contrast_limits()
    layers[-1].contrast_limits_range = [layers[-1].contrast_limits_range[0], layers[-1].contrast_limits[1]]

def view_eda_exp(viewer, main_folder = 'F:/eda_data_006', load_detections=False):
    try:
        folder = main_folder + '/overview.ome.zarr'
        viewer.open(folder, plugin='napari-ome-zarr')   
        adjust_one_array(viewer)
    except Exception as e:
        print(e)
        pass

    folder = main_folder + '/scan.ome.zarr'
    load_positions(viewer, folder, "white", name = "Scan", pixel_size=0.11315)
    
    if load_detections:
        folder = main_folder + '/network.ome.zarr'
        load_positions(viewer, folder, "bop orange", name = "Network", pixel_size = 0.11315)

    layer = viewer.open(main_folder + "/positions.csv", plugin='napari')[0]

    layer.size = 3

    #ACQUISITION
    folder = main_folder + '/acquisition.ome.zarr'
    load_positions(viewer, folder, "bop blue", {"x_offset": 15.2, "y_offset": 38.5,}, name = "Acq", pixel_size = 0.06766)
    viewer.dims.set_current_step(0, 0)


def load_positions(viewer, folder, color='bop blue', offsets ={"x_offset": 0, "y_offset": 0,}, name = "image", pixel_size = 0.11315):

    try:
        if (pathlib.Path(folder) / "eda_seq.json").exists():
            with open(pathlib.Path(folder) / f"eda_seq.json","r") as file:
                metadata = json.load(file)
        else:
            with open(pathlib.Path(folder) / ".zattrs","r") as file:
                metadata = json.load(file)["frame_metadatas"][0]['mda_event']['sequence']
        positions = []
        for p_pos in tqdm(metadata['stage_positions']):
            positions.append(p_pos)
    except Exception as e:
        print(e)
        with open(pathlib.Path(folder) / ".zattrs","r") as file:
            metadata = json.load(file)
        positions = []
        approx_pos = []
        for f in metadata["frame_metadatas"]:
            xy_pos = {'x': f['position']['x'], 'y': f['position']['y']}
            app_pos = {'x': round(f['position']['x']/10), 'y': round(f['position']['y']/10)}
            if app_pos not in approx_pos:
                positions.append(xy_pos)
                approx_pos.append(app_pos)
    
    print("Loaded from sequence")
    QApplication.processEvents()

    layers = []
    main_layer = viewer.open(f"{folder}")[0]
    array = main_layer.data.copy()
    print(array.shape)
    if name in ['Network', 'Scan']:
        array = array[:, :, -1:, ...]

    for p in tqdm(range(len(positions))):
        layer = viewer.add_image(array[p])
        layer.blending = 'additive'
        layer.colormap = color
        layer.name = name
        p_pos = positions[p]
        layer.translate = [p_pos['x'] + layer.data.shape[-2]*pixel_size/2 - offsets["x_offset"],
                           p_pos['y'] + layer.data.shape[-1]*pixel_size/2 - offsets["y_offset"]]
        layer.rotate = -90
        layer.scale = [pixel_size, -pixel_size]
        layers.append(layer)
        QApplication.processEvents()
    link_layers(layers)
    layers[-1].contrast_limits_range = [layers[-1].contrast_limits_range[0], layers[-1].contrast_limits[1]]
    viewer.layers.remove(main_layer)