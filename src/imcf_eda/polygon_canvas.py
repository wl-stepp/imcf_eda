import numpy as np
from vispy import scene
from vispy.scene import visuals

CLICK_DISTANCE = 50

class InteractiveCanvas:
    def __init__(self):
        # Create a canvas
        self.canvas = scene.SceneCanvas(self, keys='interactive', show=True)
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = 'panzoom'

        # Add a scatter plot
        self.scatter = visuals.Markers(face_color='white', edge_color = 'red', size=10)
        self.view.add(self.scatter)

        # Add a polygon visual
        self.polygons = [visuals.Polygon(color=None, border_color='red', border_width=5)]
        self.view.add(self.polygons[0])
        self.current_poly = 0
        self.new_poly = False

        # List to store the points
        self.points = [[]]

        # Variable to keep track of dragging
        self.dragging_point = None

        # Connect the event handlers
        self.canvas.events.mouse_press.connect(self.on_mouse_press)
        self.canvas.events.mouse_release.connect(self.on_mouse_release)
        self.canvas.events.mouse_move.connect(self.on_mouse_move)
        self.canvas.events.mouse_double_click.connect(self.on_mouse_double_click)
        self.canvas.events.key_press.connect(self.on_key_press)

    def update_visuals(self):
        # Update scatter plot
        scatter_points = [x for xs in self.points for x in xs]
        self.scatter.set_data(np.array(scatter_points))

        # Update polygon if there are enough points to form a polygon
        for poly, points in enumerate(self.points):
            if len(points) > 2:
                self.polygons[poly].pos = np.array(points)
                self.polygons[poly].update()

    def on_mouse_press(self, event):
        if event.button == 1:  # Left mouse button
            pos = event.pos
            tr = self.canvas.scene.node_transform(self.view.scene)
            pos = tr.map(event.pos)[:2]

            # Check if the click is near an existing point
            for ind, poly in enumerate(self.points):
                for i, p in enumerate(poly):
                    if np.linalg.norm(p - pos) < CLICK_DISTANCE:
                        self.dragging_point = [ind, i]
                        self.current_poly = ind
                        # Disable camera interaction while dragging
                        self.view.camera.interactive = False
                        break

    def on_mouse_release(self, event):
        if self.dragging_point is not None:
            # Enable camera interaction after dragging
            self.view.camera.interactive = True
        self.dragging_point = None

    def on_mouse_move(self, event):
        if self.dragging_point is not None:
            pos = event.pos
            tr = self.canvas.scene.node_transform(self.view.scene)
            pos = tr.map(event.pos)[:2]
            self.points[self.dragging_point[0]][self.dragging_point[1]] = pos
            self.update_visuals()

    def on_mouse_double_click(self, event):
        if event.button == 1:  # Left mouse button
            pos = event.pos
            tr = self.canvas.scene.node_transform(self.view.scene)
            pos = tr.map(event.pos)[:2]

            self.deleted_point = False
            # Check if the double-click is near an existing point
            for ind, poly in enumerate(self.points):
                for i, p in enumerate(poly):
                    if np.linalg.norm(p - pos) < CLICK_DISTANCE and len(self.points[ind])>3:
                        del self.points[ind][i]
                        self.deleted_point = True
                        self.update_visuals()
                        break
            if not self.deleted_point:
                # If not near an existing point, find the closest edge and add the new point
                if len(self.points[self.current_poly]) > 2 and not self.new_poly:
                    poly_index, insert_index = self.find_closest_edge(pos)
                    self.points[poly_index].insert(insert_index + 1, pos)
                elif self.new_poly:
                     self.points[-1].append(pos)
                     self.current_poly = len(self.points) - 1
                     self.new_poly = False
                else:
                    self.points[self.current_poly].append(pos)
                self.update_visuals()

    def bring_to_front(self, visual):
        # Remove and re-add the visual to bring it to the front
        self.view.remove(visual)
        self.view.add(visual)

    def on_key_press(self, event):
        if event.key == "A":
            self.points.append([])
            self.polygons.append(visuals.Polygon(color=None, border_color='red', border_width=5, parent=self.view.scene))
            # self.view.add(self.polygons[-1])
            self.new_poly = True


    def find_closest_edge(self, point):
        min_distance = float('inf')
        min_index = -1
        poly_index = -1

        for p, poly in enumerate(self.points):
            num_points = len(poly)
            for i in range(num_points):
                p1 = self.points[p][i]
                p2 = self.points[p][(i + 1) % num_points]
                edge_vec = p2 - p1
                point_vec = point - p1
                edge_length = np.linalg.norm(edge_vec)
                proj_length = np.dot(point_vec, edge_vec / edge_length)
                closest_point = p1 + proj_length * edge_vec / edge_length
                distance = np.linalg.norm(point - closest_point)

                if distance < min_distance:
                    min_distance = distance
                    min_index = i
                    poly_index = p

        return poly_index, min_index


if __name__ == '__main__':
    import sys
    if sys.flags.interactive != 1:
        from vispy.app import run
        canvas = InteractiveCanvas()
        run()
