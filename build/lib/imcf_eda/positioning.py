from imcf_eda.model import AcquisitionSettings
from pulp import LpMinimize, LpProblem, LpVariable, lpSum, LpBinary
import numpy as np


def cover_with_squares(points, square_size):
    points = np.array(points)
    uncovered_points = set(map(tuple, points))
    squares = []

    while uncovered_points:
        best_cover = set()
        best_center = None
        max_min_distance_to_border = 0

        for point in uncovered_points:
            x, y = point
            # Calculate potential square positions to maximize the distance to the border
            candidates = [
                (x - square_size / 2, y - square_size / 2),
                (x - square_size / 2, y + square_size / 2 - square_size),
                (x + square_size / 2 - square_size, y - square_size / 2),
                (x + square_size / 2 - square_size,
                 y + square_size / 2 - square_size)
            ]

            for cx, cy in candidates:
                current_cover = set((px, py) for px, py in uncovered_points
                                    if cx <= px < cx + square_size and cy <= py < cy + square_size)
                if current_cover:
                    min_distance_to_border = min(
                        min(px - cx, cx + square_size - px,
                            py - cy, cy + square_size - py)
                        for px, py in current_cover)

                    if min_distance_to_border > max_min_distance_to_border:
                        max_min_distance_to_border = min_distance_to_border
                        best_cover = current_cover
                        best_center = (cx, cy)

        # Place the square at the best position found
        squares.append(best_center)
        uncovered_points -= best_cover
    plot_squares(points, square_size, squares)
    return squares


def cover_with_squares_max_distance(points, square_size):
    points = np.array(points)
    uncovered_points = set(map(tuple, points))
    squares = []

    while uncovered_points:
        print("Running max dis")
        best_cover = set()
        best_center = None
        max_min_distance_to_border = 0

        for point in uncovered_points:
            x, y = point
            # Calculate the center of the square to maximize distance to the border
            center_x = x - (x % square_size) + square_size / 2
            center_y = y - (y % square_size) + square_size / 2

            # Calculate the bottom-left corner of the square based on the center
            cx, cy = center_x - square_size / 2, center_y - square_size / 2

            current_cover = set((px, py) for px, py in uncovered_points
                                if cx <= px < cx + square_size and cy <= py < cy + square_size)
            if current_cover:
                min_distance_to_border = min(
                    min(px - cx, cx + square_size - px,
                        py - cy, cy + square_size - py)
                    for px, py in current_cover)

                if min_distance_to_border > max_min_distance_to_border:
                    max_min_distance_to_border = min_distance_to_border
                    best_cover = current_cover
                    best_center = (cx, cy)

        # Place the square at the best position found
        if best_center:
            squares.append(best_center)
            uncovered_points -= best_cover
    plot_squares(points, square_size, squares)
    return squares


def cover_with_squares_min_distance(points, square_size):
    points = np.array(points)
    uncovered_points = set(map(tuple, points))
    squares = []

    while uncovered_points:
        # Find the point that covers the most other points when a square is placed around it
        best_cover = set()
        best_point = None

        for point in uncovered_points:
            x, y = point
            current_cover = set((px, py) for px, py in uncovered_points
                                if x <= px < x + square_size and y <= py < y + square_size)

            if len(current_cover) > len(best_cover):
                best_cover = current_cover
                best_point = point

        # Place the square around the best point found
        squares.append(best_point)
        uncovered_points -= best_cover
    plot_squares(points, square_size, squares)

    return squares

import time
def cover_with_squares_ilp(points, square_size, plot=False):
    t0 = time.perf_counter()
    if len(points) == 0:
        print("WARNING: NO DETECTIONS")
        return[(0, 0)]
    # Convert points to numpy array for vectorized operations
    points = np.array(points)
    
    # Determine the bounding box for the points
    min_x, min_y = np.min(points, axis=0)
    max_x, max_y = np.max(points, axis=0)
    
    print("Time to compute bounds:", time.perf_counter() - t0)
    
    # Define the ILP problem
    print("Defining problem...")
    prob = LpProblem("MinimizeSquares", LpMinimize)
    
    print("Time after defining problem:", time.perf_counter() - t0)
    
    # Define the grid of potential square positions, but only within the bounds of the points with some padding
    padding = square_size  # You can adjust the padding as needed
    grid_x = np.arange(min_x - padding, max_x + padding, square_size)
    grid_y = np.arange(min_y - padding, max_y + padding, square_size)
    
    print("Time after making grid:", time.perf_counter() - t0)
    
    # Create binary variables for each potential square position, but only include squares within the padded bounds
    square_vars = LpVariable.dicts("Square", (grid_x, grid_y), cat=LpBinary)
    
    # Objective: minimize the number of squares used, but only include squares near the points
    prob += lpSum(square_vars[x][y] for x in grid_x for y in grid_y)
    
    print("Time after defining objective:", time.perf_counter() - t0)
    
    # Constraints: each point must be covered by at least one square
    for px, py in points:
        # Precompute the potential grid squares that could cover the point (px, py)
        possible_x = grid_x[(grid_x <= px) & (grid_x + square_size > px)]
        possible_y = grid_y[(grid_y <= py) & (grid_y + square_size > py)]
        
        # Add a constraint that the point must be covered by at least one square
        prob += lpSum(square_vars[x][y] for x in possible_x for y in possible_y) >= 1
    print(time.perf_counter() - t0)
    # Solve the problem
    print("Solve...")
    prob.solve()
    print(time.perf_counter() - t0)
    print("Squares to positions...")
    # Extract the positions of the placed squares
    solution = [(x, y)
                for x in grid_x for y in grid_y if square_vars[x][y].varValue == 1]
    print(time.perf_counter() - t0)
    if plot:
        plot_squares(points, square_size, solution)
    return solution


def plot_squares(points, square_size, squares):
    import matplotlib.pyplot as plt
    plt.scatter(*zip(*points), c='blue', label='Points')
    offset = AcquisitionSettings().min_border_distance
    for (x, y) in squares:
        plt.gca().add_patch(plt.Rectangle((x-offset, y-offset),
                                          square_size + offset*2, square_size + offset*2,
                                          fill=None, edgecolor='red', linewidth=2))

    plt.xlabel('X')
    plt.ylabel('Y')
    plt.legend()
    plt.title('Points and Covering Squares')
    plt.axis('equal')
    plt.show()
