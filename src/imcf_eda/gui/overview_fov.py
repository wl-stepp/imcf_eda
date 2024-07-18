import numpy as np
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import box

def find_fovs(polygon_points: np.ndarray, width:float, height:float|None = None):
    if height is None:
        height = width
    # Create the Shapely polygon
    if len(polygon_points) < 4:
        return []
    shapely_polygon = ShapelyPolygon(polygon_points)

    # Get the bounding box of the polygon
    min_x, min_y, max_x, max_y = shapely_polygon.bounds
    # max_x = max_x + width
    # max_y = max_y + height

    # Iterate over the grid
    rect_pos = []
    x = min_x
    while x <= max_x:
        y = min_y
        while y <= max_y:
            # Create a rectangle
            rect = box(x, y, x + width, y + height)

            # Check if the rectangle overlaps with the polygon
            if rect.intersects(shapely_polygon):
                # Add the rectangle to the plot
                rect_pos.append((x + width/2, y + width/2))

            y += height
        x += width
    return rect_pos