import numpy as np
from vispy import scene, visuals
from vispy.visuals import transforms
from vispy.scene.visuals import Rectangle
from imcf_eda.gui.polygon_canvas import InteractiveCanvas
from imcf_eda.gui.overview_fov import find_fovs

HELP_TEXT = '''Double click: Add/delete point
Enter: Calculate FOVs
A: Add Polygon
'''


class Overview(InteractiveCanvas):
    def __init__(self, data: np.ndarray | None = None, scale: float = 1., pos: list | None = None,
                 fov_size: float = 249.59):
        super().__init__()
        self.fovs = []
        self.images = []
        self.rects = []
        self.fov_size = fov_size
        self.view.camera.aspect = 1
        # self.view.camera.
        self.text = scene.visuals.Text(HELP_TEXT, color='white', font_size=12, parent=self.canvas.scene,
                                       anchor_x="left", anchor_y="bottom")
        self.text.transform = transforms.STTransform(translate=(5, 5))

    def update_data(self, pos, data, scale):
        print("UPDATING DATA")
        for image in self.images:
            image.parent = None
        self.images = []
        for this_pos, data in zip(pos, data):
            clims = (data.min(), data.max())
            self.images.append(scene.visuals.Image(data, parent=self.view.scene,
                                                    cmap='grays', clim=clims))
            trans = transforms.linear.MatrixTransform()
            trans.rotate(-90, (0, 0, 1))
            trans.scale((-scale[0], scale[1]))
            trans.translate([this_pos[1] + data.shape[1]*scale[0]/2,
                             this_pos[0] + data.shape[0]*scale[1]/2,
                                10])
            self.images[-1].transform = trans

        min_x = min([x[1] - data.shape[0]*abs(scale[0]/2) for x in pos])
        max_x = max([x[1] + data.shape[0]*abs(scale[0]/2) for x in pos])
        min_y = min([x[0] - data.shape[1]*abs(scale[1]/2) for x in pos])
        max_y = max([x[0] + data.shape[1]*abs(scale[1]/2) for x in pos])
        self.view.camera.rect = [min_x, min_y, max_x-min_x, max_y-min_y]

    def update_fov_size(self, fov_size):
        #TODO implement this to change when the objective in the scan settings change
        self.fov_size = fov_size

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
                rect = Rectangle(center=center, border_color="white",
                                 width=self.fov_size, height=self.fov_size,
                                 parent=self.view.scene, color=None)
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
    # from ome_zarr.io import parse_url
    # from ome_zarr.reader import Reader
    import pathlib
    import json

    
    canvas = Overview()
    run()

    from useq import MDASequence
    positions = canvas.fov_positions()
    positions = [item for sublist in positions for item in sublist]
    print(positions)
    seq = MDASequence(stage_positions=positions)
    for event in seq:
        print(event)
