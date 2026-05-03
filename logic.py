import math
from collections import deque

CELL_SIZE = 10  # cm
WORK_TRIANGLE_LEG_MIN_CM = 120
WORK_TRIANGLE_LEG_MAX_CM = 270
WORK_TRIANGLE_TOTAL_MIN_CM = 400
WORK_TRIANGLE_TOTAL_MAX_CM = 790

layout_base = {
    "room": {
        "width": 400,   # cm
        "depth": 300    # cm
    },
    "door": {
        "x": 0,
        "y": 120,
        "width": 90,
        "orientation": "vertical"
    },
    "objects": [
        {
            "id": "fridge_1",
            "type": "fridge",
            "x": 0,
            "y": 0,
            "width": 60,
            "depth": 60,
            "orientation": 0,
            "access_side": "front"
        },
        {
            "id": "sink_1",
            "type": "sink",
            "x": 80,
            "y": 0,
            "width": 80,
            "depth": 60,
            "orientation": 0,
            "access_side": "front"
        },
        {
            "id": "stove_1",
            "type": "stove",
            "x": 180,
            "y": 0,
            "width": 60,
            "depth": 60,
            "orientation": 0,
            "access_side": "front"
        },
        {
            "id": "oven_1",
            "type": "oven",
            "x": 260,
            "y": 0,
            "width": 60,
            "depth": 60,
            "orientation": 0,
            "access_side": "front"
        },
        {
            "id": "table_1",
            "type": "table",
            "x": 150,
            "y": 100,
            "width": 120,
            "depth": 80,
            "orientation": 0,
            "access_side": "all"
        }
    ]
}

def create_empty_grid(layout_data, cell_size):
    room_width_cm = layout_data["room"]["width"]
    room_depth_cm = layout_data["room"]["depth"]

    cols = room_width_cm // cell_size
    rows = room_depth_cm // cell_size

    grid = []
    for _ in range(rows):
        grid.append([0] * cols)

    return grid

def place_objects_on_grid(grid, layout_data, cell_size):
    for obj in layout_data["objects"]:
        start_col = cm_to_cell(obj["x"], cell_size)
        start_row = cm_to_cell(obj["y"], cell_size)

        obj_width_cells = cm_to_cell(obj["width"], cell_size)
        obj_depth_cells = cm_to_cell(obj["depth"], cell_size)

        end_col = start_col + obj_width_cells
        end_row = start_row + obj_depth_cells

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if 0 <= row < len(grid) and 0 <= col < len(grid[0]):
                    grid[row][col] = 1

def cm_to_cell(value_cm, cell_size):
    return value_cm // cell_size

def get_occupied_cells(grid):
    occupied = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 1:
                occupied.append((row, col))
    return occupied

def compute_clearance_map(grid, cell_size):
    rows = len(grid)
    cols = len(grid[0])
    occupied_cells = get_occupied_cells(grid)

    clearance_map = []

    for row in range(rows):
        clearance_row = []
        for col in range(cols):
            if grid[row][col] == 1:
                clearance_row.append(0)
            else:
                min_distance_cells = float("inf")

                for occ_row, occ_col in occupied_cells:
                    d_row = row - occ_row
                    d_col = col - occ_col
                    distance_cells = math.sqrt(d_row ** 2 + d_col ** 2)

                    if distance_cells < min_distance_cells:
                        min_distance_cells = distance_cells

                clearance_cm = min_distance_cells * cell_size
                clearance_row.append(clearance_cm)

        clearance_map.append(clearance_row)

    return clearance_map

def compute_clearance_stats(clearance_map, grid, critical_threshold_cm=60, comfort_threshold_cm=90):
    free_clearances = []

    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 0:
                free_clearances.append(clearance_map[row][col])

    if not free_clearances:
        return None

    avg_clearance = sum(free_clearances) / len(free_clearances)

    critical_count = sum(1 for value in free_clearances if value < critical_threshold_cm)
    comfort_count = sum(1 for value in free_clearances if value >= comfort_threshold_cm)

    total_free = len(free_clearances)

    return {
        "avg_clearance_cm": avg_clearance,
        "critical_area_pct": 100 * critical_count / total_free,
        "comfortable_area_pct": 100 * comfort_count / total_free,
        "total_free_cells": total_free
    }

def create_usable_space_map(grid, clearance_map, min_clearance_cm=60):
    rows = len(grid)
    cols = len(grid[0])

    usable_map = []

    for row in range(rows):
        usable_row = []
        for col in range(cols):
            if grid[row][col] == 0 and clearance_map[row][col] >= min_clearance_cm:
                usable_row.append(1)
            else:
                usable_row.append(0)
        usable_map.append(usable_row)

    return usable_map

def compute_fragmentation_from_binary_map(binary_map):
    rows = len(binary_map)
    cols = len(binary_map[0])

    visited = [[False for _ in range(cols)] for _ in range(rows)]
    component_sizes = []

    for row in range(rows):
        for col in range(cols):
            if binary_map[row][col] == 1 and not visited[row][col]:
                stack = [(row, col)]
                visited[row][col] = True
                component_size = 0

                while stack:
                    current_row, current_col = stack.pop()
                    component_size += 1

                    neighbors = get_neighbors_4(current_row, current_col, rows, cols)
                    for neigh_row, neigh_col in neighbors:
                        if binary_map[neigh_row][neigh_col] == 1 and not visited[neigh_row][neigh_col]:
                            visited[neigh_row][neigh_col] = True
                            stack.append((neigh_row, neigh_col))

                component_sizes.append(component_size)

    total_usable_cells = sum(component_sizes)

    if total_usable_cells == 0:
        return None

    largest_component = max(component_sizes)
    num_components = len(component_sizes)
    fragmentation_index = 1 - (largest_component / total_usable_cells)

    return {
        "num_components": num_components,
        "largest_component_cells": largest_component,
        "total_usable_cells": total_usable_cells,
        "fragmentation_index": fragmentation_index
    }

def get_neighbors_4(row, col, rows, cols):
    neighbors = []

    if row > 0:
        neighbors.append((row - 1, col))   # up
    if row < rows - 1:
        neighbors.append((row + 1, col))   # down
    if col > 0:
        neighbors.append((row, col - 1))   # left
    if col < cols - 1:
        neighbors.append((row, col + 1))   # right

    return neighbors

def compute_walkability_score(clearance_map, grid, critical_threshold_cm=60, comfort_threshold_cm=90):
    scores = []

    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 0:  # only free cells
                clearance = clearance_map[row][col]

                if clearance < critical_threshold_cm:
                    score = 0.0
                elif clearance < comfort_threshold_cm:
                    score = 0.5
                else:
                    score = 1.0

                scores.append(score)

    if not scores:
        return None

    avg_score = sum(scores) / len(scores)

    num_poor = sum(1 for s in scores if s == 0.0)
    num_medium = sum(1 for s in scores if s == 0.5)
    num_good = sum(1 for s in scores if s == 1.0)

    total = len(scores)

    return {
        "walkability_score": avg_score,
        "poor_pct": 100 * num_poor / total,
        "medium_pct": 100 * num_medium / total,
        "good_pct": 100 * num_good / total,
        "total_free_cells": total
    }

def get_interaction_point(obj, cell_size=10):
    x = obj["x"]
    y = obj["y"]
    width = obj["width"]
    depth = obj["depth"]
    access_side = obj["access_side"]
    orientation = obj["orientation"]

    offset = cell_size

    if access_side == "front":
        if orientation == 0:
            interaction_x = x + width // 2
            interaction_y = y + depth + offset
        elif orientation == 90:
            interaction_x = x - offset
            interaction_y = y + depth // 2
        elif orientation == 180:
            interaction_x = x + width // 2
            interaction_y = y - offset
        elif orientation == 270:
            interaction_x = x + width + offset
            interaction_y = y + depth // 2
        else:
            interaction_x = x + width // 2
            interaction_y = y + depth + offset

    elif access_side == "all":
        # per ora scegliamo un punto semplice davanti al lato superiore del tavolo
        interaction_x = x + width // 2
        interaction_y = y - offset

    else:
        interaction_x = x + width // 2
        interaction_y = y + depth + offset

    return (interaction_x, interaction_y)

def get_table_candidate_points(obj, cell_size=10):
    x = obj["x"]
    y = obj["y"]
    width = obj["width"]
    depth = obj["depth"]
    offset = cell_size

    candidates = [
        (x + width // 2, y - offset),           # top
        (x + width // 2, y + depth + offset),   # bottom
        (x - offset, y + depth // 2),           # left
        (x + width + offset, y + depth // 2)    # right
    ]

    return candidates

def compute_shortest_path_length(grid, start_cell, end_cell):
    rows = len(grid)
    cols = len(grid[0])

    start_row, start_col = start_cell
    end_row, end_col = end_cell

    if not (0 <= start_row < rows and 0 <= start_col < cols):
        return None
    if not (0 <= end_row < rows and 0 <= end_col < cols):
        return None

    if grid[start_row][start_col] == 1 or grid[end_row][end_col] == 1:
        return None

    visited = [[False for _ in range(cols)] for _ in range(rows)]
    queue = deque()

    queue.append((start_row, start_col, 0))
    visited[start_row][start_col] = True

    while queue:
        row, col, dist = queue.popleft()

        if (row, col) == (end_row, end_col):
            return dist

        for neigh_row, neigh_col in get_neighbors_4(row, col, rows, cols):
            if not visited[neigh_row][neigh_col] and grid[neigh_row][neigh_col] == 0:
                visited[neigh_row][neigh_col] = True
                queue.append((neigh_row, neigh_col, dist + 1))

    return None

def compute_shortest_path_to_any(grid, start_cell, end_cells):
    valid_lengths = []

    for end_cell in end_cells:
        path_length = compute_shortest_path_length(grid, start_cell, end_cell)
        if path_length is not None:
            valid_lengths.append((path_length, end_cell))

    if not valid_lengths:
        return None, None

    best_length, best_end_cell = min(valid_lengths, key=lambda x: x[0])
    return best_length, best_end_cell

def get_door_point(layout_data):
    door = layout_data["door"]

    x = door["x"]
    y = door["y"]
    width = door["width"]
    orientation = door["orientation"]

    if orientation == "vertical":
        point_x = x
        point_y = y + width // 2
    else:
        point_x = x + width // 2
        point_y = y

    return (point_x, point_y)

def get_object_by_id(layout_data, object_id):
    for obj in layout_data["objects"]:
        if obj["id"] == object_id:
            return obj
    return None

def get_workflow_points(layout_data):
    points = {}

    points["door"] = get_door_point(layout_data)

    fridge = get_object_by_id(layout_data, "fridge_1")
    sink = get_object_by_id(layout_data, "sink_1")
    stove = get_object_by_id(layout_data, "stove_1")
    table = get_object_by_id(layout_data, "table_1")

    points["fridge"] = get_interaction_point(fridge, CELL_SIZE)
    points["sink"] = get_interaction_point(sink, CELL_SIZE)
    points["stove"] = get_interaction_point(stove, CELL_SIZE)
    points["table"] = get_interaction_point(table, CELL_SIZE)

    return points

def point_cm_to_cell(point_cm, cell_size):
    x_cm, y_cm = point_cm
    col = cm_to_cell(x_cm, cell_size)
    row = cm_to_cell(y_cm, cell_size)
    return (row, col)

def compute_workflow_path_stats(layout_data, grid, cell_size):
    points_cm = get_workflow_points(layout_data)

    workflow_pairs = [
        ("door", "fridge"),
        ("fridge", "sink"),
        ("sink", "stove")
    ]

    path_results = []
    valid_lengths = []

    for start_name, end_name in workflow_pairs:
        start_cm = points_cm[start_name]
        end_cm = points_cm[end_name]

        start_cell = point_cm_to_cell(start_cm, cell_size)
        end_cell = point_cm_to_cell(end_cm, cell_size)

        path_length_cells = compute_shortest_path_length(grid, start_cell, end_cell)

        if path_length_cells is not None:
            path_length_cm = path_length_cells * cell_size
            valid_lengths.append(path_length_cm)
        else:
            path_length_cm = None

        path_results.append({
            "from": start_name,
            "to": end_name,
            "length_cm": path_length_cm
        })

    # special handling for stove -> table
    stove_cm = points_cm["stove"]
    stove_cell = point_cm_to_cell(stove_cm, cell_size)

    table_obj = get_object_by_id(layout_data, "table_1")
    table_candidate_points_cm = get_table_candidate_points(table_obj, cell_size)
    table_candidate_cells = [point_cm_to_cell(p, cell_size) for p in table_candidate_points_cm]

    best_length_cells, best_table_cell = compute_shortest_path_to_any(grid, stove_cell, table_candidate_cells)

    if best_length_cells is not None:
        best_length_cm = best_length_cells * cell_size
        valid_lengths.append(best_length_cm)
    else:
        best_length_cm = None

    path_results.append({
        "from": "stove",
        "to": "table",
        "length_cm": best_length_cm
    })

    if not valid_lengths:
        return None

    avg_length_cm = sum(valid_lengths) / len(valid_lengths)

    return {
        "paths": path_results,
        "avg_workflow_path_cm": avg_length_cm
    }

def compute_work_triangle_stats(layout_data, grid, cell_size):
    points_cm = get_workflow_points(layout_data)

    triangle_pairs = [
        ("fridge", "sink"),
        ("sink", "stove"),
        ("stove", "fridge")
    ]

    legs = []
    leg_scores = []
    leg_lengths = []

    for start_name, end_name in triangle_pairs:
        start_cell = point_cm_to_cell(points_cm[start_name], cell_size)
        end_cell = point_cm_to_cell(points_cm[end_name], cell_size)
        path_length_cells = compute_shortest_path_length(grid, start_cell, end_cell)

        if path_length_cells is None:
            length_cm = None
        else:
            length_cm = path_length_cells * cell_size
            leg_lengths.append(length_cm)

        score = score_distance_with_ideal_range(
            length_cm,
            WORK_TRIANGLE_LEG_MIN_CM,
            WORK_TRIANGLE_LEG_MAX_CM
        )
        leg_scores.append(score)

        legs.append({
            "from": start_name,
            "to": end_name,
            "length_cm": length_cm,
            "ideal_min_cm": WORK_TRIANGLE_LEG_MIN_CM,
            "ideal_max_cm": WORK_TRIANGLE_LEG_MAX_CM,
            "score": score
        })

    if len(leg_lengths) == len(triangle_pairs):
        total_cm = sum(leg_lengths)
        total_score = score_distance_with_ideal_range(
            total_cm,
            WORK_TRIANGLE_TOTAL_MIN_CM,
            WORK_TRIANGLE_TOTAL_MAX_CM
        )
    else:
        total_cm = None
        total_score = 0.0

    triangle_score = (sum(leg_scores) + total_score) / (len(leg_scores) + 1)

    return {
        "legs": legs,
        "total_cm": total_cm,
        "total_ideal_min_cm": WORK_TRIANGLE_TOTAL_MIN_CM,
        "total_ideal_max_cm": WORK_TRIANGLE_TOTAL_MAX_CM,
        "total_score": total_score,
        "triangle_score": triangle_score
    }

def compute_workflow_score(workflow_path_stats):
    if workflow_path_stats is None:
        return None

    ideal_ranges = {
        ("door", "fridge"): (80, 200),
        ("fridge", "sink"): (60, 180),
        ("sink", "stove"): (60, 180),
        ("stove", "table"): (80, 180)
    }

    scored_paths = []
    scores = []

    for path in workflow_path_stats["paths"]:
        pair = (path["from"], path["to"])
        distance_cm = path["length_cm"]

        if pair in ideal_ranges:
            ideal_min, ideal_max = ideal_ranges[pair]
            score = score_distance_with_ideal_range(distance_cm, ideal_min, ideal_max)
        else:
            ideal_min = None
            ideal_max = None
            score = 0.0

        scored_paths.append({
            "from": path["from"],
            "to": path["to"],
            "length_cm": distance_cm,
            "ideal_min_cm": ideal_min,
            "ideal_max_cm": ideal_max,
            "score": score
        })

        scores.append(score)

    if not scores:
        return None

    avg_score = sum(scores) / len(scores)

    return {
        "scored_paths": scored_paths,
        "workflow_route_score": avg_score
    }

def score_distance_with_ideal_range(distance_cm, ideal_min, ideal_max):
    if distance_cm is None:
        return 0.0

    if ideal_min <= distance_cm <= ideal_max:
        return 1.0

    if distance_cm < ideal_min:
        return max(0.0, distance_cm / ideal_min)

    return max(0.0, ideal_max / distance_cm)

def normalize_value(value, min_value, max_value):
    if value <= min_value:
        return 0.0
    if value >= max_value:
        return 1.0
    return (value - min_value) / (max_value - min_value)

def compute_space_score(clearance_stats, walkability_stats, usable_fragmentation_stats):
    if clearance_stats is None or walkability_stats is None or usable_fragmentation_stats is None:
        return None

    avg_clearance_cm = clearance_stats["avg_clearance_cm"]
    critical_area_pct = clearance_stats["critical_area_pct"]
    total_free_cells = clearance_stats["total_free_cells"]

    walkability_score = walkability_stats["walkability_score"]
    total_usable_cells = usable_fragmentation_stats["total_usable_cells"]

    clearance_score = normalize_value(avg_clearance_cm, 40, 120)
    critical_area_score = 1.0 - (critical_area_pct / 100.0)
    usable_area_score = total_usable_cells / total_free_cells

    final_space_score = (
        clearance_score +
        critical_area_score +
        walkability_score +
        usable_area_score
    ) / 4.0

    return {
        "space_score": final_space_score,
        "components": {
            "clearance_score": clearance_score,
            "critical_area_score": critical_area_score,
            "walkability_score": walkability_score,
            "usable_area_score": usable_area_score
        }
    }

def analyze_layout(layout_data):
    grid = create_empty_grid(layout_data, CELL_SIZE)
    place_objects_on_grid(grid, layout_data, CELL_SIZE)

    clearance_map = compute_clearance_map(grid, CELL_SIZE)
    clearance_stats = compute_clearance_stats(clearance_map, grid)

    usable_space_map = create_usable_space_map(grid, clearance_map, 60)
    usable_fragmentation_stats = compute_fragmentation_from_binary_map(usable_space_map)

    walkability_stats = compute_walkability_score(clearance_map, grid)

    workflow_path_stats = compute_workflow_path_stats(layout_data, grid, CELL_SIZE)
    workflow_score_stats = compute_workflow_score(workflow_path_stats)
    work_triangle_stats = compute_work_triangle_stats(layout_data, grid, CELL_SIZE)
    workflow_score = (
        workflow_score_stats["workflow_route_score"] +
        work_triangle_stats["triangle_score"]
    ) / 2.0

    space_score_stats = compute_space_score(
        clearance_stats,
        walkability_stats,
        usable_fragmentation_stats
    )

    return {
        "space_score": space_score_stats["space_score"],
        "workflow_score": workflow_score,
        "workflow_route_score": workflow_score_stats["workflow_route_score"],
        "work_triangle": work_triangle_stats,
        "space_components": space_score_stats["components"],
        "clearance_stats": clearance_stats,
        "walkability_stats": walkability_stats,
        "usable_fragmentation_stats": usable_fragmentation_stats,
        "workflow_paths": workflow_score_stats["scored_paths"]
    }

def compare_layouts(result_a, result_b):
    space_a = result_a["space_score"]
    space_b = result_b["space_score"]

    workflow_a = result_a["workflow_score"]
    workflow_b = result_b["workflow_score"]

    if space_a > space_b:
        space_winner = "A"
    elif space_b > space_a:
        space_winner = "B"
    else:
        space_winner = "tie"

    if workflow_a > workflow_b:
        workflow_winner = "A"
    elif workflow_b > workflow_a:
        workflow_winner = "B"
    else:
        workflow_winner = "tie"

    if space_winner == workflow_winner and space_winner != "tie":
        recommendation = f"Layout {space_winner} is better overall"
    elif space_winner == workflow_winner and space_winner == "tie":
        recommendation = "Both layouts are similar in terms of space and workflow"
    else:
        recommendation = (
            f"Trade-off: {space_winner} better for space, {workflow_winner} better for workflow"
        )

    return {
        "space_winner": space_winner,
        "workflow_winner": workflow_winner,
        "recommendation": recommendation
    }

def check_overlap(obj1, obj2):
    return not (
        obj1["x"] + obj1["width"] <= obj2["x"] or
        obj2["x"] + obj2["width"] <= obj1["x"] or
        obj1["y"] + obj1["depth"] <= obj2["y"] or
        obj2["y"] + obj2["depth"] <= obj1["y"]
    )

def layout_is_valid(objects):
    for i in range(len(objects)):
        for j in range(i + 1, len(objects)):
            if check_overlap(objects[i], objects[j]):
                return False
    return True

