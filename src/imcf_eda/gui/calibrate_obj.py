import numpy as np
from vispy import scene
from vispy.scene import visuals
from vispy.visuals import transforms
from pymmcore_plus import CMMCorePlus
from imcf_eda.convenience import init_microscope
import time
CLICK_DISTANCE = 3


class CalibrationCanvas:
    def __init__(self, mmc: CMMCorePlus):
        self.mmc = mmc
        # Create a canvas
        self.canvas = scene.SceneCanvas(self, keys='interactive', show=True, size=(512, 512))
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = 'panzoom'
        self.view.camera.aspect = 1

        # Add a scatter plot
        self.scatter = visuals.Markers(
            face_color='red', edge_color='red', size=10)
        self.view.add(self.scatter)

        self.scatter_2 = visuals.Markers(
            face_color='cyan', edge_color='red', size=10)
        self.view.add(self.scatter_2)

        self.labels = []
        # List to store the points
        self.points = [[]]
        self.labels_2 = []
        self.points_2 = [[]]
        self.images = []
        self.objective = 1
        self.label_state = 1

        # Connect the event handlers
        self.canvas.events.mouse_double_click.connect(
            self.on_mouse_double_click)
        self.canvas.events.key_press.connect(self.on_key_press)

    def update_visuals(self):
        # Update scatter plot
        if self.label_state == 1:
            scatter_points = [x for xs in self.points for x in xs]
            self.scatter.set_data(np.array(scatter_points), face_color='c')
            labels = self.labels
        else:
            scatter_points = [x for xs in self.points_2 for x in xs]
            self.scatter_2.set_data(np.array(scatter_points), face_color='m')
            labels = self.labels_2
        for label in labels:
            label.parent = None
        labels = []
        for i, canvas_pos in enumerate(scatter_points):
            label = visuals.Text(str(i), font_size=12, color='white', pos=(
                canvas_pos[0] + 10, canvas_pos[1]))
            # Store the text visuals for future updates
            labels.append(label)
            self.view.add(label)

    def on_mouse_double_click(self, event):
        if event.button == 1:  # Left mouse button
            pos = event.pos
            tr = self.canvas.scene.node_transform(self.view.scene)
            pos = tr.map(event.pos)[:2]

            self.deleted_point = False
            points = self.points if self.label_state == 1 else self.points_2
            # Check if the double-click is near an existing point
            for ind, poly in enumerate(points):
                for i, p in enumerate(poly):
                    if np.linalg.norm(p - pos) < CLICK_DISTANCE:
                        del points[ind][i]
                        self.deleted_point = True
                        self.update_visuals()
                        break
            if not self.deleted_point:
                # If not near an existing point, find the closest edge and add the new point
                points[-1].append(pos)
                self.update_visuals()

    def bring_to_front(self, visual):
        # Remove and re-add the visual to bring it to the front
        self.view.remove(visual)
        self.view.add(visual)

    def update_data(self, data, scale, cmap, offset=(0, 0)):
        clims = (data.min(), data.max())
        self.images.append(scene.visuals.Image(data, parent=self.view.scene,
                                               cmap=cmap, clim=clims))
        trans = transforms.linear.MatrixTransform()
        trans.translate([-data.shape[0]//2 + offset[0], -
                        data.shape[1]//2 + offset[1], 10])
        trans.scale((scale[0], scale[1]))
        self.images[-1].transform = trans

    def on_key_press(self, event):
        if event.key == 'Enter':
            self.mmc.snapImage()
            time.sleep(1)
            img = self.mmc.getImage()
            scale = self.mmc.getPixelSizeUm()
            print("SCALE", scale)
            if self.objective == 1:
                # img = image
                self.update_data(img, (scale, scale), 'grays')
                self.z0 = self.mmc.getPosition()
                self.objective = 2
            elif self.objective == 2 and self.label_state == 1:
                # img = cropped_image
                self.update_data(img, (scale, scale), 'viridis')
                self.images[-1].set_gl_state("additive", depth_test=False)
                self.z1 = self.mmc.getPosition()
                self.label_state = 2
            else:
                self.calculate_offset()

    def calculate_offset(self):
        x, y = [], []
        for points in zip(self.points[:len(self.points_2)], self.points_2):
            x.append(points[1][0][0] - points[0][0][0])
            y.append(points[1][0][1] - points[0][0][1])
        print(f'OFFSETS: x {np.mean(x)}, y {np.mean(y)}'
              f', z {self.z1 - self.z0}')


if __name__ == '__main__':
    import sys
    from scipy.ndimage import zoom
    if sys.flags.interactive != 1:
        print('running')
        from vispy.app import run
        mmc = CMMCorePlus()
        init_microscope(mmc, None)

        canvas = CalibrationCanvas(mmc)
        height, width = 512, 512

        # Create a blank image (greyscale, so 2D array)
        image = np.zeros((height, width))

        # Calculate the new positions for the shapes to be in the middle of the 512x512 image

        # Horizontal line in the middle
        image[height // 2, :] = 150

        # Vertical line in the middle
        image[:, width // 2] = 200

        # Rectangle in the center
        rect_top = height // 2 + 60
        rect_bottom = height // 2 + 90
        rect_left = width // 2 - 40
        rect_right = width // 2 + 40
        image[rect_top:rect_bottom, rect_left:rect_right] = 100

        # Circle in the center
        y, x = np.ogrid[:height, :width]
        center_y, center_x = height // 2 + 150, width // 2 + 150
        radius = 40
        mask = (x - center_x)**2 + (y - center_y)**2 <= radius**2
        image[mask] = 150

        # Zooming in by a factor of 1/0.6 (~1.67x)
        zoom_factor = 1 / 0.6
        zoomed_image = zoom(image, zoom_factor)

        # Since zoom will create an image larger than 512x512, we need to crop it back to 512x512
        center_y_zoomed, center_x_zoomed = zoomed_image.shape[0] // 2, zoomed_image.shape[1] // 2
        cropped_image = zoomed_image[center_y_zoomed - height // 2: center_y_zoomed + height // 2,
                                     center_x_zoomed - width // 2: center_x_zoomed + width // 2]
        import vispy
        print(vispy.color.colormap.get_colormaps())
        run()
