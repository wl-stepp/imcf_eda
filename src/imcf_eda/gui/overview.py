import numpy as np
from vispy import scene, visuals
from vispy.scene.visuals import Rectangle
from imcf_eda.gui.polygon_canvas import InteractiveCanvas
from imcf_eda.gui.overview_fov import find_fovs




class Overview(InteractiveCanvas):
    def __init__(self, data:str|None = None):
        super().__init__()
        self.fovs = []
        self.images = []
        self.rects = []
        self.view.camera.aspect = 1
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
        # self.view.camera.set_range(self.image.bounds(0), self.image.bounds(1), margin=0)

    def reset_images(self):
        for image in self.images:
            image.parent.children.remove(image)
            self.view.add(image)

    def update_fovs(self):
        print("Recalculate FOVs")
        for rect in self.rects:
            rect.parent = None
        self.rects = []
        print(self.points)
        for poly in self.points:
            print("poly")
            self.fovs = find_fovs(np.array(poly), 500)
            for fov in self.fovs:
                rect = Rectangle(center=fov + (250, 250), border_color="white", width=500, height=500,
                                            parent=self.view.scene, color=None)
                self.rects.append(rect)


    def on_key_press(self, event):
        print(f"Key pressed: {event.key}")
        if event.key == 'Enter':
            self.update_fovs()
        super().on_key_press(event)
        if event.key == 'A':
            self.reset_images()


if __name__ == "__main__":
    import sys
    if sys.flags.interactive != 1:
        from vispy.app import run
        canvas = Overview()
        run()