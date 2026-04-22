import math
from collections import deque

CELL_SIZE = 10  # cm per cella


layout_a = {
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
layout_b = {
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
            "x": 120,
            "y": 150,
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

def cm_to_cell(value_cm, cell_size):
    return value_cm // cell_size

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

def print_grid(grid):
    for row in grid:
        line = ""
        for cell in row:
            if cell == 0:
                line += "."
            else:
                line += "#"
        print(line)

def print_grid_info(grid):
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    print(f"Grid size: {rows} rows x {cols} cols")
    print(f"Cell size: {CELL_SIZE} cm")

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

def print_clearance_stats(stats):
    if stats is None:
        print("No free space available.")
        return

    print("CLEARANCE STATS")
    print(f"  Average clearance: {stats['avg_clearance_cm']:.2f} cm")
    print(f"  Critical area (< 60 cm): {stats['critical_area_pct']:.2f}%")
    print(f"  Comfortable area (>= 90 cm): {stats['comfortable_area_pct']:.2f}%")
    print(f"  Free cells: {stats['total_free_cells']}")

def analyze_layout(layout_data):
    grid = create_empty_grid(layout_data, CELL_SIZE)
    place_objects_on_grid(grid, layout_data, CELL_SIZE)

    clearance_map = compute_clearance_map(grid, CELL_SIZE)
    clearance_stats = compute_clearance_stats(clearance_map, grid)

    usable_space_map = create_usable_space_map(grid, clearance_map, min_clearance_cm=60)
    usable_fragmentation_stats = compute_fragmentation_from_binary_map(usable_space_map)

    walkability_stats = compute_walkability_score(clearance_map, grid)

    workflow_path_stats = compute_workflow_path_stats(layout_data, grid, CELL_SIZE)

    workflow_score_stats = compute_workflow_score(workflow_path_stats)

    space_score_stats = compute_space_score(
    clearance_stats,
    walkability_stats,
    usable_fragmentation_stats
)

    return {
        "grid": grid,
        "clearance_map": clearance_map,
        "clearance_stats": clearance_stats,
        "usable_space_map": usable_space_map,
        "usable_fragmentation_stats": usable_fragmentation_stats,
        "walkability_stats": walkability_stats,
        "workflow_path_stats": workflow_path_stats,
        "workflow_score_stats": workflow_score_stats,
        "space_score_stats": space_score_stats
    }

def compare_clearance(stats_a, stats_b):
    print("COMPARISON (CLEARANCE ONLY)")

    score = 0

    if stats_a["avg_clearance_cm"] > stats_b["avg_clearance_cm"]:
        print("- A has higher average clearance")
        score += 1
    else:
        print("- B has higher average clearance")
        score -= 1

    if stats_a["critical_area_pct"] < stats_b["critical_area_pct"]:
        print("- A has less critical area")
        score += 1
    else:
        print("- B has less critical area")
        score -= 1

    if stats_a["comfortable_area_pct"] > stats_b["comfortable_area_pct"]:
        print("- A has more comfortable area")
        score += 1
    else:
        print("- B has more comfortable area")
        score -= 1

    print()
    if score > 0:
        print("→ Layout A is better (clearance)")
    elif score < 0:
        print("→ Layout B is better (clearance)")
    else:
        print("→ Tie")

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

def compute_fragmentation_stats(grid):
    rows = len(grid)
    cols = len(grid[0])

    visited = [[False for _ in range(cols)] for _ in range(rows)]
    component_sizes = []

    for row in range(rows):
        for col in range(cols):
            if grid[row][col] == 0 and not visited[row][col]:
                stack = [(row, col)]
                visited[row][col] = True
                component_size = 0

                while stack:
                    current_row, current_col = stack.pop()
                    component_size += 1

                    neighbors = get_neighbors_4(current_row, current_col, rows, cols)
                    for neigh_row, neigh_col in neighbors:
                        if grid[neigh_row][neigh_col] == 0 and not visited[neigh_row][neigh_col]:
                            visited[neigh_row][neigh_col] = True
                            stack.append((neigh_row, neigh_col))

                component_sizes.append(component_size)

    total_free_cells = sum(component_sizes)

    if total_free_cells == 0:
        return None

    largest_component = max(component_sizes)
    num_components = len(component_sizes)
    fragmentation_index = 1 - (largest_component / total_free_cells)

    return {
        "num_components": num_components,
        "largest_component_cells": largest_component,
        "total_free_cells": total_free_cells,
        "fragmentation_index": fragmentation_index
    }

def print_fragmentation_stats(stats):
    if stats is None:
        print("No free space available.")
        return

    print("FRAGMENTATION STATS")
    print(f"  Number of free-space components: {stats['num_components']}")
    print(f"  Largest component: {stats['largest_component_cells']} cells")
    print(f"  Total free cells: {stats['total_free_cells']}")
    print(f"  Fragmentation index: {stats['fragmentation_index']:.4f}")

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

def print_usable_fragmentation_stats(stats):
    if stats is None:
        print("USABLE-SPACE FRAGMENTATION STATS")
        print("  No usable space available.")
        return

    print("USABLE-SPACE FRAGMENTATION STATS")
    print(f"  Number of usable-space components: {stats['num_components']}")
    print(f"  Largest usable component: {stats['largest_component_cells']} cells")
    print(f"  Total usable cells: {stats['total_usable_cells']}")
    print(f"  Fragmentation index: {stats['fragmentation_index']:.4f}")

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

def print_walkability_stats(stats):
    if stats is None:
        print("WALKABILITY STATS")
        print("  No free space available.")
        return

    print("WALKABILITY STATS")
    print(f"  Walkability score: {stats['walkability_score']:.4f}")
    print(f"  Poor area (< 60 cm): {stats['poor_pct']:.2f}%")
    print(f"  Medium area (60-90 cm): {stats['medium_pct']:.2f}%")
    print(f"  Good area (>= 90 cm): {stats['good_pct']:.2f}%")
    print(f"  Free cells: {stats['total_free_cells']}")

def get_object_by_id(layout_data, object_id):
    for obj in layout_data["objects"]:
        if obj["id"] == object_id:
            return obj
    return None

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

def point_cm_to_cell(point_cm, cell_size):
    x_cm, y_cm = point_cm
    col = cm_to_cell(x_cm, cell_size)
    row = cm_to_cell(y_cm, cell_size)
    return (row, col)

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

def print_workflow_path_stats(stats):
    if stats is None:
        print("WORKFLOW PATH STATS")
        print("  No valid workflow paths found.")
        return

    print("WORKFLOW PATH STATS")
    for path in stats["paths"]:
        if path["length_cm"] is None:
            print(f"  {path['from']} -> {path['to']}: unreachable")
        else:
            print(f"  {path['from']} -> {path['to']}: {path['length_cm']} cm")

    print(f"  Average workflow path length: {stats['avg_workflow_path_cm']:.2f} cm")

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

def score_distance_with_ideal_range(distance_cm, ideal_min, ideal_max):
    if distance_cm is None:
        return 0.0

    if ideal_min <= distance_cm <= ideal_max:
        return 1.0

    if distance_cm < ideal_min:
        return max(0.0, distance_cm / ideal_min)

    return max(0.0, ideal_max / distance_cm)

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
            score = 0.0

        scored_paths.append({
            "from": path["from"],
            "to": path["to"],
            "length_cm": distance_cm,
            "score": score
        })

        scores.append(score)

    if not scores:
        return None

    avg_score = sum(scores) / len(scores)

    return {
        "scored_paths": scored_paths,
        "workflow_score": avg_score
    }

def print_workflow_score_stats(stats):
    if stats is None:
        print("WORKFLOW SCORE STATS")
        print("  No workflow score available.")
        return

    print("WORKFLOW SCORE STATS")
    for path in stats["scored_paths"]:
        if path["length_cm"] is None:
            print(f"  {path['from']} -> {path['to']}: unreachable, score = 0.0000")
        else:
            print(f"  {path['from']} -> {path['to']}: {path['length_cm']} cm, score = {path['score']:.4f}")

    print(f"  Average workflow score: {stats['workflow_score']:.4f}")

def compare_layouts(result_a, result_b):
    space_a = result_a["space_score_stats"]["space_score"]
    space_b = result_b["space_score_stats"]["space_score"]

    workflow_a = result_a["workflow_score_stats"]["workflow_score"]
    workflow_b = result_b["workflow_score_stats"]["workflow_score"]

    reasons_space = []
    reasons_workflow = []

    if space_a > space_b:
        space_winner = "A"
        reasons_space.append(f"A has a better overall space score ({space_a:.4f} vs {space_b:.4f})")
    elif space_b > space_a:
        space_winner = "B"
        reasons_space.append(f"B has a better overall space score ({space_b:.4f} vs {space_a:.4f})")
    else:
        space_winner = "tie"
        reasons_space.append("Both layouts have the same space score")

    if workflow_a > workflow_b:
        workflow_winner = "A"
        reasons_workflow.append(f"A has a better workflow score ({workflow_a:.4f} vs {workflow_b:.4f})")
    elif workflow_b > workflow_a:
        workflow_winner = "B"
        reasons_workflow.append(f"B has a better workflow score ({workflow_b:.4f} vs {workflow_a:.4f})")
    else:
        workflow_winner = "tie"
        reasons_workflow.append("Both layouts have the same workflow score")

    if space_winner == workflow_winner and space_winner != "tie":
        final_recommendation = f"Layout {space_winner} is the overall better option."
    elif space_winner == "tie" and workflow_winner != "tie":
        final_recommendation = f"Space quality is tied, but Layout {workflow_winner} has the better workflow."
    elif workflow_winner == "tie" and space_winner != "tie":
        final_recommendation = f"Workflow is tied, but Layout {space_winner} has the better spatial quality."
    else:
        final_recommendation = (
            f"Trade-off detected: Layout {space_winner} is better for space, "
            f"while Layout {workflow_winner} is better for workflow."
        )

    return {
        "space_winner": space_winner,
        "workflow_winner": workflow_winner,
        "space_score_a": space_a,
        "space_score_b": space_b,
        "workflow_score_a": workflow_a,
        "workflow_score_b": workflow_b,
        "reasons_space": reasons_space,
        "reasons_workflow": reasons_workflow,
        "final_recommendation": final_recommendation
    }

def print_comparison_summary(comparison):
    print("FINAL COMPARISON")
    print(f"  Space winner: {comparison['space_winner']}")
    print(f"  Workflow winner: {comparison['workflow_winner']}")
    print(f"  Space score -> A: {comparison['space_score_a']:.4f}, B: {comparison['space_score_b']:.4f}")
    print(f"  Workflow score -> A: {comparison['workflow_score_a']:.4f}, B: {comparison['workflow_score_b']:.4f}")
    print()

    print("  Space reasons:")
    for reason in comparison["reasons_space"]:
        print(f"   - {reason}")

    print("  Workflow reasons:")
    for reason in comparison["reasons_workflow"]:
        print(f"   - {reason}")

    print()
    print(f"  Recommendation: {comparison['final_recommendation']}")

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
        "clearance_score": clearance_score,
        "critical_area_score": critical_area_score,
        "walkability_score": walkability_score,
        "usable_area_score": usable_area_score,
        "space_score": final_space_score
    }

def print_space_score_stats(stats):
    if stats is None:
        print("SPACE SCORE STATS")
        print("  No space score available.")
        return

    print("SPACE SCORE STATS")
    print(f"  Clearance score: {stats['clearance_score']:.4f}")
    print(f"  Critical area score: {stats['critical_area_score']:.4f}")
    print(f"  Walkability score: {stats['walkability_score']:.4f}")
    print(f"  Usable area score: {stats['usable_area_score']:.4f}")
    print(f"  Final space score: {stats['space_score']:.4f}")

if __name__ == "__main__":
    result_a = analyze_layout(layout_a)
    result_b = analyze_layout(layout_b)

    print("LAYOUT A")
    print_clearance_stats(result_a["clearance_stats"])
    print_usable_fragmentation_stats(result_a["usable_fragmentation_stats"])
    print_walkability_stats(result_a["walkability_stats"])
    print_workflow_path_stats(result_a["workflow_path_stats"])
    print_workflow_score_stats(result_a["workflow_score_stats"])
    print()

    print("LAYOUT B")
    print_clearance_stats(result_b["clearance_stats"])
    print_usable_fragmentation_stats(result_b["usable_fragmentation_stats"])
    print_walkability_stats(result_b["walkability_stats"])
    print_workflow_path_stats(result_b["workflow_path_stats"])
    print_workflow_score_stats(result_b["workflow_score_stats"])
    print()
    comparison = compare_layouts(result_a, result_b)
    print()
    print_comparison_summary(comparison)