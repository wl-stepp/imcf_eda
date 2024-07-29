import numpy as np
from vispy import scene, visuals
from vispy.scene.visuals import Rectangle
from imcf_eda.gui.polygon_canvas import InteractiveCanvas
from imcf_eda.gui.overview_fov import find_fovs

HELP_TEXT = '''Double click: Add point
Enter: calculate FOVs
A: Add Polygon
'''


class Overview(InteractiveCanvas):
    def __init__(self, data:np.ndarray|None = None, scale:float = 1., pos:list|None = None,
                 fov_size:float = 100.):
        super().__init__()
        self.fovs = []
        self.images = []
        self.rects = []
        self.fov_size = fov_size
        self.view.camera.aspect = 1

        if data is None or pos is None:
            for pos, cmap in [[[0,0], 'grays'], [[0,2048], 'grays'], [[2048,2048], 'grays']]:
            # for pos, cmap in [[[0,0], 'grays'], [[0,2048], 'Reds'], [[2048,2048], 'viridis']]:
                print(pos)
                print(cmap)
                # image = np.random.randint(100, 2000, (2048, 2048))
                image = np.ones((2048, 2048)).astype(np.uint8) * 150
                image[0, 0] = 1
                self.images.append(scene.visuals.Image(image, parent=self.view.scene,
                                                    cmap=cmap, clim= [0, 256]))
                trans = visuals.transforms.linear.MatrixTransform()
                trans.translate([*pos, 10])
                self.images[-1].transform = trans

            self.view.camera.rect = [0, 0, 4096, 4096]
        else:
            for this_pos, data in zip(pos, data):
                self.images.append(scene.visuals.Image(data, parent=self.view.scene,
                                                    cmap='grays', clim= [0, 256]))
                trans = visuals.transforms.linear.MatrixTransform()
                trans.scale((scale, scale))
                trans.translate([this_pos[0] - data.shape[0]*scale/2,
                                 this_pos[1] - data.shape[1]*scale/2,
                                 10])
                self.images[-1].transform = trans

            min_x = min([x[0] - data.shape[0]*scale/2 for x in pos])
            max_x = max([x[0] + data.shape[0]*scale/2 for x in pos])
            min_y = min([x[1] - data.shape[1]*scale/2 for x in pos])
            max_y = max([x[1] + data.shape[1]*scale/2 for x in pos])
            print([min_x, min_y, max_x, max_y])
            self.view.camera.rect = [min_x, min_y, max_x-min_x, max_y-min_y]
            print(data.shape[0]*scale)


        self.text = scene.visuals.Text(HELP_TEXT, color='white', font_size=12, parent=self.canvas.scene,
                                       anchor_x="left", anchor_y="bottom")
        self.text.transform = visuals.transforms.STTransform(translate=(5, 5))

    def reset_images(self):
        for image in self.images:
            image.parent.children.remove(image)
            self.view.add(image)

    def update_fovs(self):
        print("Recalculate FOVs")
        for rect in self.rects:
            rect.parent = None
        self.rects = []
        self.fovs = []
        print(self.points)
        for poly in self.points:
            print("poly")
            fovs = find_fovs(np.array(poly), self.fov_size)
            for fov in fovs:
                center = fov + (self.fov_size/2, self.fov_size/2)
                rect = Rectangle(center=center, border_color="white", width=self.fov_size,
                                 height=self.fov_size, parent=self.view.scene, color=None)
                self.rects.append(rect)
            self.fovs.append(fovs)

    def on_key_press(self, event):
        print(f"Key pressed: {event.key}")
        if event.key == 'Enter':
            self.update_fovs()
        super().on_key_press(event)
        if event.key == 'A':
            self.reset_images()

    def fov_positions(self):
        return self.fovs


if __name__ == "__main__":
    import sys
    if sys.flags.interactive != 1:
        from vispy.app import run
    from ome_zarr.io import parse_url
    from ome_zarr.reader import Reader
    import pathlib
    import json

    url = "/mnt/c/Users/stepp/Downloads/Basel_data/data/eda_data_024/scan.ome.zarr/"
    # url = "https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0062A/6001240.zarr"
    store = parse_url(url, mode="r")
    reader = Reader(store)
    # nodes may include images, labels etc
    nodes = list(reader())
    # first node will be the image pixel data
    image_node = nodes[0]

    with open(pathlib.Path(url) / "p0/.zattrs","r") as file:
        metadata = json.load(file)
    scale = metadata["frame_meta"][0]["PixelSizeUm"]
    pos = []
    for g_pos in metadata["frame_meta"]:
        pos.append([g_pos["Event"]["x_pos"], g_pos["Event"]["y_pos"]])
    data = image_node.data[0][:, 0, 100, :, :]
    for i in range(data.shape[0]):
        data[i] = np.rot90(data[i], 2)
    canvas = Overview(data, scale, pos)
    run()

    from useq import MDASequence
    positions = canvas.fov_positions()
    positions = [item for sublist in positions for item in sublist]
    print(positions)
    seq = MDASequence(stage_positions = positions)
    for event in seq:
        print(event)

    import pymmcore_plus
    import pymmcore_widgets
