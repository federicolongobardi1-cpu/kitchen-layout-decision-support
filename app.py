from collections import deque
import heapq
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from matplotlib.patches import Arc, Circle, Ellipse, FancyBboxPatch, Rectangle


st.set_page_config(page_title="Interior Layout Audit", page_icon="▧", layout="wide")

ROOM_W_CM = 900
ROOM_H_CM = 400
CELL_CM = 10
GRID_W = ROOM_W_CM // CELL_CM
GRID_H = ROOM_H_CM // CELL_CM
WALL_CM = 18

COMPONENT_DIR = Path(__file__).parent / "grid_component"
grid_component = components.declare_component("grid_editor", path=str(COMPONENT_DIR))

TYPE_COLORS = {
    "door": "#f8fafc",
    "window": "#bfdbfe",
    "counter": "#f3f4f6",
    "storage": "#e5e7eb",
    "sink": "#e0f2fe",
    "stove": "#fee2e2",
    "dining_set": "#fef3c7",
    "sofa": "#dcfce7",
    "tv": "#ede9fe",
    "plant": "#bbf7d0",
    "fridge": "#e0e7ff",
}

st.markdown(
    """
<style>
[data-testid="stAppViewContainer"] { background: #f8fafc; }
[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e5e7eb; }
.block-container { padding-top: 1.1rem; max-width: 1580px; }
.card {
    background: white; border: 1px solid #e5e7eb; border-radius: 18px;
    padding: 18px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.045);
    margin-bottom: 16px;
}
.small-card {
    background: white; border: 1px solid #e5e7eb; border-radius: 16px;
    padding: 14px 16px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.035);
    min-height: 170px;
}
.section-title { font-size: 1.15rem; font-weight: 800; margin-bottom: 4px; color:#111827; }
.subtle { color: #64748b; font-size: 0.92rem; }
.nav-item { padding: 10px 12px; border-radius: 10px; margin-bottom: 8px; color: #475569; font-weight: 500; }
.nav-active { background: #eaf2ff; color: #1266d6; font-weight: 700; }
.progress-bg { height: 8px; background: #eef2f7; border-radius: 999px; overflow: hidden; margin-top: 12px; margin-bottom: 10px; }
.progress-fill-green { height: 8px; background: #2e9d55; border-radius: 999px; }
.progress-fill-amber { height: 8px; background: #f5b642; border-radius: 999px; }
.progress-fill-orange { height: 8px; background: #f97316; border-radius: 999px; }
.metric-name { font-weight: 800; color: #111827; font-size: 0.9rem; }
.metric-score { font-size: 2rem; font-weight: 850; color: #2e9d55; line-height: 1.1; }
.metric-score-amber { color: #f5b642; }
.metric-score-orange { color: #f97316; }
.mini-row { display: flex; justify-content: space-between; font-size: 0.78rem; color: #475569; padding: 4px 0; }
.sidebar-title { font-size: 1.45rem; font-weight: 850; color: #111827; margin-bottom: 0px; }
.sidebar-subtitle { color: #64748b; font-size: 0.9rem; margin-bottom: 28px; }
.badge {
    display: inline-block; padding: 4px 9px; border-radius: 999px;
    background: #eef2ff; color: #3444a3; font-size: 0.78rem; margin-right: 6px; margin-bottom: 5px;
}
</style>
""",
    unsafe_allow_html=True,
)


def demo_layout():
    return pd.DataFrame(
        [
            ["Door", "door", "entry", 395, 400, 80, WALL_CM],
            ["Window Top", "window", "living", 520, -15, 260, 15],
            ["Window Left", "window", "living", -15, 145, 15, 155],
            ["TV Unit", "tv", "living", 40, 25, 320, 38],
            ["Sofa 1", "sofa", "living", 55, 160, 70, 175],
            ["Sofa 2", "sofa", "living", 120, 315, 230, 60],
            ["Plant Large", "plant", "living", 455, 300, 40, 40],
            ["Plant Small", "plant", "living", 365, 95, 35, 35],
            ["Fridge", "fridge", "kitchen", 810, 55, 60, 95],
            ["Tall Storage", "storage", "kitchen", 810, 150, 60, 175],
            ["Kitchen Counter", "counter", "kitchen", 500, 325, 300, 45],
            ["Sink", "sink", "kitchen", 820, 260, 42, 48],
            ["Cooktop", "stove", "kitchen", 665, 336, 70, 28],
            ["Dining Set", "dining_set", "dining", 620, 210, 145, 185],
        ],
        columns=["name", "type", "zone", "x", "y", "w", "h"],
    )


def clean_layout(df):
    required = ["name", "type", "zone", "x", "y", "w", "h"]
    for col in required:
        if col not in df.columns:
            df[col] = "" if col in ["name", "type", "zone"] else 0

    df = df[required].copy()
    df["name"] = df["name"].astype(str)
    df["type"] = df["type"].astype(str).str.lower().str.strip()
    df["zone"] = df["zone"].astype(str).str.lower().str.strip()
    for c in ["x", "y", "w", "h"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    df["w"] = df["w"].clip(10, ROOM_W_CM)
    df["h"] = df["h"].clip(10, ROOM_H_CM)

    wall_items = df["type"].isin(["door", "window"])
    horizontal_wall_items = wall_items & (df["w"] >= df["h"])
    vertical_wall_items = wall_items & (df["h"] > df["w"])
    df.loc[horizontal_wall_items, "h"] = df.loc[horizontal_wall_items, "h"].clip(10, WALL_CM)
    df.loc[vertical_wall_items, "w"] = df.loc[vertical_wall_items, "w"].clip(10, WALL_CM)

    def clamp_position(r, axis):
        room_size = ROOM_W_CM if axis == "x" else ROOM_H_CM
        size = int(r["w"] if axis == "x" else r["h"])
        value = int(r[axis])
        if r["type"] in {"door", "window"}:
            return min(max(value, -WALL_CM), room_size)
        return min(max(value, 0), max(0, room_size - size))

    df["x"] = df.apply(lambda r: clamp_position(r, "x"), axis=1)
    df["y"] = df.apply(lambda r: clamp_position(r, "y"), axis=1)
    return df


def load_sample_layout():
    try:
        return clean_layout(pd.read_csv("sample_layout.csv"))
    except Exception:
        return demo_layout()


def render_grid_editor(df):
    items = clean_layout(df).to_dict(orient="records")
    return grid_component(
        items=items,
        colors=TYPE_COLORS,
        roomWidth=ROOM_W_CM,
        roomHeight=ROOM_H_CM,
        default=items,
        key=f"grid_editor_v2_{len(items)}",
    )


def to_grid(df):
    occ = np.zeros((GRID_H, GRID_W), dtype=int)
    for _, r in clean_layout(df).iterrows():
        if r.type in {"door", "window"}:
            continue
        x1 = max(0, int(np.floor(r.x / CELL_CM)))
        y1 = max(0, int(np.floor(r.y / CELL_CM)))
        x2 = min(GRID_W, int(np.ceil((r.x + r.w) / CELL_CM)))
        y2 = min(GRID_H, int(np.ceil((r.y + r.h) / CELL_CM)))
        if x2 > x1 and y2 > y1:
            occ[y1:y2, x1:x2] = 1
    return occ


def clearance_map(occ):
    obstacles = np.argwhere(occ == 1)
    clear = np.zeros_like(occ, dtype=float)
    if len(obstacles) == 0:
        return np.ones_like(occ, dtype=float) * 200

    for y in range(occ.shape[0]):
        for x in range(occ.shape[1]):
            if occ[y, x] == 1:
                clear[y, x] = 0
            else:
                d = np.min(np.abs(obstacles[:, 0] - y) + np.abs(obstacles[:, 1] - x))
                clear[y, x] = d * CELL_CM
    return clear


def connected_components(mask):
    seen = np.zeros_like(mask, dtype=bool)
    sizes = []
    h, w = mask.shape
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                q = deque([(x, y)])
                seen[y, x] = True
                size = 0
                while q:
                    cx, cy = q.popleft()
                    size += 1
                    for nx, ny in [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]:
                        if 0 <= nx < w and 0 <= ny < h and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((nx, ny))
                sizes.append(size)
    return sizes


def point_to_cell(point):
    x = int(np.clip(point[0] / CELL_CM, 0, GRID_W - 1))
    y = int(np.clip(point[1] / CELL_CM, 0, GRID_H - 1))
    return x, y


def nearest_free_cell(occ, cell):
    sx, sy = cell
    if occ[sy, sx] == 0:
        return sx, sy

    seen = np.zeros_like(occ, dtype=bool)
    q = deque([(sx, sy)])
    seen[sy, sx] = True
    while q:
        cx, cy = q.popleft()
        for nx, ny in [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]:
            if 0 <= nx < GRID_W and 0 <= ny < GRID_H and not seen[ny, nx]:
                if occ[ny, nx] == 0:
                    return nx, ny
                seen[ny, nx] = True
                q.append((nx, ny))
    return None


def best_free_cell_near(occ, clear, cell, radius=14):
    sx, sy = cell
    best_cell = nearest_free_cell(occ, cell)
    best_score = -1
    for y in range(max(0, sy - radius), min(GRID_H, sy + radius + 1)):
        for x in range(max(0, sx - radius), min(GRID_W, sx + radius + 1)):
            if occ[y, x] == 1:
                continue
            distance_penalty = (abs(x - sx) + abs(y - sy)) * CELL_CM * 0.12
            score = clear[y, x] - distance_penalty
            if score > best_score:
                best_score = score
                best_cell = (x, y)
    return best_cell


def widest_path_clearance(clear, occ, start, end):
    start = best_free_cell_near(occ, clear, start)
    end = best_free_cell_near(occ, clear, end)
    if start is None or end is None:
        return 0

    best = np.full_like(clear, -1, dtype=float)
    sx, sy = start
    ex, ey = end
    best[sy, sx] = clear[sy, sx]
    heap = [(-clear[sy, sx], sx, sy)]

    while heap:
        neg_width, x, y = heapq.heappop(heap)
        width = -neg_width
        if (x, y) == (ex, ey):
            return width
        if width < best[y, x]:
            continue
        for nx, ny in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
            if 0 <= nx < GRID_W and 0 <= ny < GRID_H and occ[ny, nx] == 0:
                candidate = min(width, clear[ny, nx])
                if candidate > best[ny, nx]:
                    best[ny, nx] = candidate
                    heapq.heappush(heap, (-candidate, nx, ny))
    return 0


def path_score(width_cm):
    if width_cm >= 85:
        return 100
    if width_cm >= 55:
        return 70 + (width_cm - 55) / 30 * 30
    if width_cm >= 40:
        return 45 + (width_cm - 40) / 15 * 25
    return max(0, width_cm / 40 * 45)


def clearance_score(width_cm):
    if width_cm >= 90:
        return 100
    if width_cm >= 60:
        return 85 + (width_cm - 60) / 30 * 15
    if width_cm >= 30:
        return 55 + (width_cm - 30) / 30 * 30
    return max(0, width_cm / 30 * 35)


def rect_gap(a, b):
    ax1, ay1, ax2, ay2 = a.x, a.y, a.x + a.w, a.y + a.h
    bx1, by1, bx2, by2 = b.x, b.y, b.x + b.w, b.y + b.h
    dx = max(bx1 - ax2, ax1 - bx2, 0)
    dy = max(by1 - ay2, ay1 - by2, 0)
    if dx == 0 and dy == 0:
        return 0
    return float(np.hypot(dx, dy))


def dining_kitchen_clearance(df):
    dining = df[df.type == "dining_set"]
    kitchen_items = df[df.type.isin(["counter", "sink", "stove", "fridge", "storage"])]
    if len(dining) == 0 or len(kitchen_items) == 0:
        return 90.0
    d = dining.iloc[0]
    gaps = [rect_gap(d, item) for _, item in kitchen_items.iterrows()]
    return float(min(gaps) if gaps else 90)


def soft_distance_score(distance, ideal, tolerance, falloff):
    over = max(distance - ideal, 0)
    if over <= tolerance:
        return 100
    return float(np.clip(100 - (over - tolerance) / falloff * 100, 0, 100))


def kitchen_triangle_score(df):
    centers = {}
    for item_type in ["sink", "stove", "fridge"]:
        rows = df[df.type == item_type]
        if len(rows) == 0:
            return 62
        r = rows.iloc[0]
        centers[item_type] = np.array([r.x + r.w / 2, r.y + r.h / 2])

    pairs = [("sink", "stove"), ("stove", "fridge"), ("fridge", "sink")]
    distances = [np.linalg.norm(centers[a] - centers[b]) for a, b in pairs]
    perimeter = sum(distances)
    side_scores = [100 - min(abs(d - 180) / 2.2, 55) for d in distances]
    perimeter_score = 100 - min(abs(perimeter - 620) / 4.8, 55)
    return float(np.clip(0.65 * np.mean(side_scores) + 0.35 * perimeter_score, 0, 100))


def natural_light_score(df, occ):
    windows = df[df.type == "window"]
    if len(windows) == 0:
        return 35, 0

    free_cells = np.argwhere(occ == 0)
    if len(free_cells) == 0:
        return 35, 0

    window_points = []
    for _, r in windows.iterrows():
        if r.w >= r.h:
            samples = max(3, int(r.w // 80))
            for t in np.linspace(0.1, 0.9, samples):
                window_points.append([r.x + r.w * t, np.clip(r.y + r.h / 2, 0, ROOM_H_CM)])
        else:
            samples = max(3, int(r.h // 80))
            for t in np.linspace(0.1, 0.9, samples):
                window_points.append([np.clip(r.x + r.w / 2, 0, ROOM_W_CM), r.y + r.h * t])

    lit = 0
    soft_lit = 0
    for gy, gx in free_cells:
        point = np.array([(gx + 0.5) * CELL_CM, (gy + 0.5) * CELL_CM])
        d = min(np.linalg.norm(point - np.array(wp)) for wp in window_points)
        if d <= 320:
            lit += 1
        if d <= 480:
            soft_lit += 1

    lit_ratio = lit / len(free_cells)
    soft_ratio = soft_lit / len(free_cells)
    score = np.clip(35 + lit_ratio * 48 + soft_ratio * 22, 0, 100)
    return float(score), float(lit_ratio)


def route_comfort(df, occ, clear):
    def center_for(kind, fallback):
        zdf = df[df.zone == kind]
        if len(zdf) == 0:
            return np.array(fallback)
        return np.array([(zdf.x + zdf.w / 2).mean(), (zdf.y + zdf.h / 2).mean()])

    door_df = df[df.type == "door"]
    if len(door_df) > 0:
        door = door_df.iloc[0]
        entry = np.array([door.x + door.w / 2, max(0, door.y - 35)])
    else:
        entry = np.array([ROOM_W_CM / 2, ROOM_H_CM - 20])

    anchors = {
        "entry": entry,
        "living": center_for("living", [ROOM_W_CM * 0.25, ROOM_H_CM * 0.5]),
        "dining": center_for("dining", [ROOM_W_CM * 0.62, ROOM_H_CM * 0.5]),
        "kitchen": center_for("kitchen", [ROOM_W_CM * 0.82, ROOM_H_CM * 0.62]),
    }
    route_pairs = [("entry", "living"), ("entry", "kitchen"), ("living", "dining"), ("dining", "kitchen")]
    widths = [
        widest_path_clearance(clear, occ, point_to_cell(anchors[a]), point_to_cell(anchors[b]))
        for a, b in route_pairs
    ]
    scores = [path_score(w) for w in widths]
    return float(np.mean(scores)), float(min(widths) if widths else 0), float(np.mean(widths) if widths else 0)


def compute_scores(df, profile):
    occ = to_grid(df)
    clear = clearance_map(occ)
    density = occ.sum() / occ.size
    free_clear = clear[occ == 0]
    critical = (free_clear < 60).sum() / max(len(free_clear), 1)
    comfortable = (free_clear >= 90).sum() / max(len(free_clear), 1)
    route_score, min_route_width, avg_route_width = route_comfort(df, occ, clear)
    light_score, lit_ratio = natural_light_score(df, occ)
    dining_service_clearance = dining_kitchen_clearance(df)
    dining_service_score = clearance_score(dining_service_clearance)

    usable = (clear >= 60) & (occ == 0)
    comp = connected_components(usable)
    largest = max(comp) if comp else 0
    fragmentation = 1 - largest / max(usable.sum(), 1)

    left = occ[:, : GRID_W // 2].sum()
    right = occ[:, GRID_W // 2 :].sum()
    top = occ[: GRID_H // 2, :].sum()
    bottom = occ[GRID_H // 2 :, :].sum()
    lr = abs(left - right) / max(left + right, 1)
    tb = abs(top - bottom) / max(top + bottom, 1)

    visual_balance = np.clip(100 * (1 - 0.55 * lr - 0.45 * tb), 0, 100)
    openness = np.clip(100 * (1 - density * 1.45), 0, 100)
    spatial_coherence = np.clip(100 * (1 - fragmentation * 1.35), 0, 100)
    circulation = np.clip(route_score * 0.72 + dining_service_score * 0.18 + 100 * (1 - fragmentation) * 0.10, 0, 100)
    accessibility = np.clip(route_score * 0.70 + comfortable * 30, 0, 100)
    congestion = np.clip(route_score * 0.58 + dining_service_score * 0.25 + 100 * (1 - density * 1.4) * 0.17, 0, 100)

    def zone_center(zdf):
        if len(zdf) == 0:
            return np.array([450, 200])
        return np.array([(zdf.x + zdf.w / 2).mean(), (zdf.y + zdf.h / 2).mean()])

    kc = zone_center(df[df.zone == "kitchen"])
    dc = zone_center(df[df.zone == "dining"])
    lc = zone_center(df[df.zone == "living"])
    kd_dist = np.linalg.norm(kc - dc)
    dl_dist = np.linalg.norm(dc - lc)

    kitchen_dining_fit = soft_distance_score(kd_dist, ideal=260, tolerance=80, falloff=360)
    dining_living_fit = soft_distance_score(dl_dist, ideal=340, tolerance=120, falloff=420)
    functional_adjacency = np.clip(0.65 * kitchen_dining_fit + 0.35 * dining_living_fit, 0, 100)
    activity_interference = np.clip(
        route_score * 0.42 + dining_service_score * 0.36 + 100 * (1 - fragmentation) * 0.16 + 100 * (1 - critical) * 0.06,
        0,
        100,
    )
    zone_workflow = np.clip(100 - max((kd_dist + dl_dist) - 650, 0) / 9, 0, 100)
    triangle = kitchen_triangle_score(df)
    workflow_simplicity = np.clip(0.55 * zone_workflow + 0.45 * triangle, 0, 100)
    natural_light = light_score
    spatial_efficiency = np.clip(100 - abs(density - 0.22) * 210, 0, 100)
    clearance_compliance = np.clip(route_score * 0.58 + dining_service_score * 0.27 + 100 * (1 - critical) * 0.15, 0, 100)

    cooking_mult = {"Rarely cooks": 0.90, "Cooks sometimes": 1.0, "Cooks often": 1.15}[profile["cooking"]]
    social_mult = {"Low": 0.90, "Medium": 1.0, "High": 1.18}[profile["social"]]
    access_mult = {"Low": 0.9, "Medium": 1.0, "High": 1.20}[profile["accessibility"]]
    lifestyle = np.clip(
        0.35 * functional_adjacency * cooking_mult
        + 0.35 * circulation * access_mult
        + 0.15 * openness
        + 0.15 * dining_service_score,
        0,
        100,
    )
    social_fit = np.clip(0.55 * workflow_simplicity * social_mult + 0.25 * openness + 0.20 * spatial_coherence, 0, 100)
    maintenance = np.clip(100 - density * 95 - critical * 55, 0, 100)

    sub = {
        "Spatial Experience": {"Visual Balance": visual_balance, "Openness": openness, "Spatial Coherence": spatial_coherence},
        "Human Comfort": {"Circulation Comfort": circulation, "Accessibility": accessibility, "Congestion Risk": congestion},
        "Functional Logic": {"Functional Adjacency": functional_adjacency, "Activity Interference": activity_interference, "Workflow Simplicity": workflow_simplicity},
        "Sustainability & Compliance": {"Natural Light Usage": natural_light, "Spatial Efficiency": spatial_efficiency, "Clearance Compliance": clearance_compliance},
        "Client Fit": {"Lifestyle Compatibility": lifestyle, "Social Interaction Fit": social_fit, "Maintenance Practicality": maintenance},
    }
    sub = {k: {m: round(float(v), 0) for m, v in vals.items()} for k, vals in sub.items()}
    macro = {k: round(sum(vals.values()) / len(vals), 0) for k, vals in sub.items()}
    return macro, sub, clear, {
        "critical": critical,
        "density": density,
        "fragmentation": fragmentation,
        "comfortable": comfortable,
        "min_route_width": min_route_width,
        "avg_route_width": avg_route_width,
        "lit_ratio": lit_ratio,
        "kitchen_triangle": triangle,
        "dining_service_clearance": dining_service_clearance,
        "dining_service_score": dining_service_score,
    }


def color_class(score):
    if score >= 75:
        return "green"
    if score >= 65:
        return "amber"
    return "orange"


def status(score):
    if score >= 75:
        return "Good"
    if score >= 65:
        return "Fair"
    return "Needs work"


def list_card(title, items):
    rows = "".join(f"<li>{item}</li>" for item in items[:3])
    return f"""
    <div class="card">
        <div class="section-title">{title}</div>
        <ul class="subtle">{rows}</ul>
    </div>
    """


def layout_feedback(sub, diagnostics):
    issues = []
    tradeoffs = []
    suggestions = []

    if diagnostics["dining_service_clearance"] < 60:
        issues.append(f"Dining is too close to the kitchen work area ({diagnostics['dining_service_clearance']:.0f} cm).")
        suggestions.append("Move the dining set away from the counter/cooktop until the kitchen side has at least 60-90 cm.")
    elif diagnostics["dining_service_clearance"] < 90:
        issues.append(f"Kitchen-side dining clearance is usable but tight ({diagnostics['dining_service_clearance']:.0f} cm).")
        suggestions.append("Fine-tune dining position to protect a more comfortable kitchen working aisle.")

    if diagnostics["min_route_width"] < 55:
        issues.append(f"The narrowest key route is only {diagnostics['min_route_width']:.0f} cm.")
        suggestions.append("Keep a continuous open route from the door toward living, dining, and kitchen.")
    elif diagnostics["avg_route_width"] >= 70:
        tradeoffs.append("Main routes are comfortable, so furniture can be arranged more for use and composition.")

    if sub["Human Comfort"]["Congestion Risk"] < 65:
        issues.append("The layout still reads as congested around the main circulation paths.")
        suggestions.append("Pull bulky pieces toward walls and leave the central path more continuous.")

    if sub["Functional Logic"]["Workflow Simplicity"] >= 80:
        tradeoffs.append("Kitchen workflow is strong, especially around the sink-stove-fridge relationship.")
    elif diagnostics["kitchen_triangle"] < 65:
        issues.append("The kitchen triangle is weak or incomplete.")
        suggestions.append("Bring sink, cooktop, and fridge into a shorter, more balanced triangle.")

    if sub["Spatial Experience"]["Openness"] < 65:
        tradeoffs.append("The room gains function from furniture density, but visual openness is reduced.")
    else:
        tradeoffs.append("The room preserves good openness while keeping the main functions connected.")

    if diagnostics["lit_ratio"] < 0.45:
        issues.append("A limited share of free floor area is close to natural light.")
        suggestions.append("Keep taller storage away from window zones and leave brighter areas more open.")
    else:
        tradeoffs.append("Natural light reaches a good share of the usable floor area.")

    if not issues:
        issues.append("No major blocking issue is detected in the current layout.")
    if not suggestions:
        suggestions.append("Keep testing small shifts and rotations to improve comfort without losing adjacency.")
    return issues, tradeoffs, suggestions


def draw_sofa(ax, x, y, w, h, edge, lw):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=8", facecolor="#dcfce7", edgecolor=edge, linewidth=lw))
    if w >= h:
        n = max(2, int(w // 80))
        for i in range(n):
            cx = x + i * w / n
            ax.add_patch(Rectangle((cx + 4, y + 6), w / n - 8, h - 12, facecolor="#ecfdf5", edgecolor="#86efac", lw=0.6))
    else:
        n = max(2, int(h // 70))
        for i in range(n):
            cy = y + i * h / n
            ax.add_patch(Rectangle((x + 6, cy + 4), w - 12, h / n - 8, facecolor="#ecfdf5", edgecolor="#86efac", lw=0.6))
    ax.text(x + w / 2, y + h / 2, "SOFA", ha="center", va="center", fontsize=8, fontweight="bold", color="#166534")


def draw_dining_set(ax, x, y, w, h, edge, lw):
    ax.add_patch(FancyBboxPatch((x + w * 0.18, y + h * 0.17), w * 0.64, h * 0.66, boxstyle="round,pad=0,rounding_size=7", facecolor="#fef3c7", edgecolor=edge, linewidth=lw))
    chairs = [
        (x + w * 0.28, y, w * 0.44, h * 0.13),
        (x + w * 0.28, y + h * 0.87, w * 0.44, h * 0.13),
        (x, y + h * 0.28, w * 0.14, h * 0.22),
        (x, y + h * 0.57, w * 0.14, h * 0.22),
        (x + w * 0.86, y + h * 0.28, w * 0.14, h * 0.22),
        (x + w * 0.86, y + h * 0.57, w * 0.14, h * 0.22),
    ]
    for cx, cy, cw, ch in chairs:
        ax.add_patch(FancyBboxPatch((cx, cy), cw, ch, boxstyle="round,pad=0,rounding_size=5", facecolor="#fef9c3", edgecolor="#64748b", linewidth=0.8))
    ax.text(x + w / 2, y + h / 2, "DINING", ha="center", va="center", fontsize=8, fontweight="bold", color="#92400e")


def draw_plant(ax, x, y, w, h, edge, lw):
    ax.add_patch(Circle((x + w / 2, y + h / 2), min(w, h) * 0.42, facecolor="#dcfce7", edgecolor=edge, lw=lw))
    for angle in np.linspace(0, 2 * np.pi, 7, endpoint=False):
        ax.add_patch(
            Ellipse(
                (x + w / 2 + np.cos(angle) * w * 0.18, y + h / 2 + np.sin(angle) * h * 0.18),
                w * 0.22,
                h * 0.13,
                angle=np.degrees(angle),
                facecolor="#22c55e",
                edgecolor="none",
                alpha=0.85,
            )
        )
    ax.text(x + w / 2, y + h / 2, "P", ha="center", va="center", fontsize=8, fontweight="bold", color="#14532d")


def draw_plan(df, selected=None):
    fig, ax = plt.subplots(figsize=(12, 5.4))
    wall = WALL_CM
    ax.set_xlim(-70, ROOM_W_CM + 60)
    ax.set_ylim(ROOM_H_CM + 55, -70)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.add_patch(Rectangle((0, 0), ROOM_W_CM, ROOM_H_CM, facecolor="#f5f1ea", edgecolor="#3f3f46", lw=1.2))
    wall_color = "#6b6b65"
    wall_edge = "#2f3437"
    ax.add_patch(Rectangle((-wall, -wall), ROOM_W_CM + 2 * wall, wall, facecolor=wall_color, edgecolor=wall_edge, lw=1.2))
    ax.add_patch(Rectangle((-wall, ROOM_H_CM), ROOM_W_CM + 2 * wall, wall, facecolor=wall_color, edgecolor=wall_edge, lw=1.2))
    ax.add_patch(Rectangle((-wall, 0), wall, ROOM_H_CM, facecolor=wall_color, edgecolor=wall_edge, lw=1.2))
    ax.add_patch(Rectangle((ROOM_W_CM, 0), wall, ROOM_H_CM, facecolor=wall_color, edgecolor=wall_edge, lw=1.2))
    ax.text(28, -8, "WALL", ha="left", va="center", fontsize=7, fontweight="bold", color="#f8fafc")

    rng = np.random.default_rng(7)
    for _ in range(150):
        x = rng.uniform(25, ROOM_W_CM - 55)
        y = rng.uniform(25, ROOM_H_CM - 45)
        w = rng.uniform(18, 65)
        h = rng.uniform(5, 13)
        ax.add_patch(Rectangle((x, y), w, h, facecolor="#ded6cb", alpha=0.13, edgecolor="none"))

    ax.plot([18, ROOM_W_CM - 18], [-30, -30], color="#9ca3af", lw=0.9)
    ax.text(ROOM_W_CM / 2, -38, "900 cm", ha="center", va="bottom", fontsize=11, fontweight="bold", color="#333")
    ax.plot([-30, -30], [18, ROOM_H_CM - 18], color="#9ca3af", lw=0.9)
    ax.text(-45, ROOM_H_CM / 2, "400 cm", rotation=90, ha="center", va="center", fontsize=11, fontweight="bold", color="#333")

    for _, r in df.iterrows():
        x, y, w, h = r.x, r.y, r.w, r.h
        edge = "#2563eb" if selected == r["name"] else "#4b5563"
        lw = 2.3 if selected == r["name"] else 1.0
        color = TYPE_COLORS.get(r.type, "#ffffff")

        if r.type == "window":
            ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor=edge, lw=lw))
            continue
        if r.type == "door":
            ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor=edge, lw=lw))
            swing_y = ROOM_H_CM - 1 if y >= ROOM_H_CM - h else y + h
            ax.add_patch(Arc((x + w, swing_y), 2 * w, 2 * w, theta1=90, theta2=180, color=edge, lw=1.2))
            continue
        if r.type == "sofa":
            draw_sofa(ax, x, y, w, h, edge, lw)
            continue
        if r.type == "dining_set":
            draw_dining_set(ax, x, y, w, h, edge, lw)
            continue
        if r.type == "plant":
            draw_plant(ax, x, y, w, h, edge, lw)
            continue

        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=6", facecolor=color, edgecolor=edge, linewidth=lw))
        label = {"counter": "KITCHEN", "tv": "TV", "storage": "STORAGE", "sink": "SINK", "stove": "STOVE", "fridge": "FRIDGE"}.get(r.type, r.type.upper())
        fs = 7 if min(w, h) < 45 else 8
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=fs, fontweight="bold", color="#334155")

        if r.type == "stove":
            for i in range(4):
                cx = x + w * 0.30 + (i % 2) * w * 0.25
                cy = y + h * 0.35 + (i // 2) * h * 0.25
                ax.add_patch(plt.Circle((cx, cy), min(w, h) * 0.12, fill=False, edgecolor="#64748b", lw=0.8))
        if r.type == "sink":
            ax.add_patch(Rectangle((x + w * 0.2, y + h * 0.2), w * 0.6, h * 0.6, fill=False, edgecolor="#64748b", lw=0.8))
        if r.type == "fridge":
            ax.plot([x, x + w], [y + h * 0.5, y + h * 0.5], color="#94a3b8", lw=0.8)

    return fig


def draw_heatmap(clear):
    fig, ax = plt.subplots(figsize=(12, 5.4))
    ax.imshow(clear, cmap="YlOrRd_r", origin="upper", extent=[0, ROOM_W_CM, ROOM_H_CM, 0])
    ax.add_patch(Rectangle((0, 0), ROOM_W_CM, ROOM_H_CM, fill=False, edgecolor="#374151", lw=1.2))
    ax.set_title("Critical clearance and congestion heatmap", fontsize=12, fontweight="bold")
    ax.set_xticks([])
    ax.set_yticks([])
    return fig


def metric_card(name, score, submetrics):
    cls = color_class(score)
    score_cls = "" if cls == "green" else f"metric-score-{cls}"
    fill_cls = f"progress-fill-{cls}"
    rows = ""
    for k, v in submetrics.items():
        dot = "#2e9d55" if v >= 75 else "#f5b642" if v >= 65 else "#f97316"
        rows += f"<div class='mini-row'><span>{k}</span><span><span style='color:{dot};'>●</span> {int(v)}/100</span></div>"
    score_color = "#2e9d55" if cls == "green" else "#b7791f" if cls == "amber" else "#c75b12"
    return f"""
    <div class="small-card">
        <div class="metric-name">{name}</div>
        <div style="display:flex;align-items:baseline;gap:4px;margin-top:12px;">
            <span class="metric-score {score_cls}">{int(score)}</span><span class="subtle">/100</span>
        </div>
        <div class="subtle" style="color:{score_color};">{status(score)}</div>
        <div class="progress-bg"><div class="{fill_cls}" style="width:{int(score)}%;"></div></div>
        {rows}
    </div>
    """


if "layout_df" not in st.session_state:
    st.session_state.layout_df = load_sample_layout()

with st.sidebar:
    st.markdown('<div class="sidebar-title">▧ Interior Layout Audit</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">AI-assisted design analysis</div>', unsafe_allow_html=True)

    st.markdown('<div class="subtle">1. LAYOUT</div>', unsafe_allow_html=True)
    layout_mode = st.selectbox("Layout mode", ["Grid Editor", "Move Objects", "Add Objects"], index=0, label_visibility="collapsed")
    if layout_mode == "Grid Editor":
        st.markdown('<div class="nav-item nav-active">Grid Editor</div>', unsafe_allow_html=True)
        st.markdown('<div class="nav-item">Move Objects</div>', unsafe_allow_html=True)
        st.markdown('<div class="nav-item">Add Objects</div>', unsafe_allow_html=True)
    elif layout_mode == "Move Objects":
        st.markdown('<div class="nav-item">Grid Editor</div>', unsafe_allow_html=True)
        st.markdown('<div class="nav-item nav-active">Move Objects</div>', unsafe_allow_html=True)
        st.markdown('<div class="nav-item">Add Objects</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="nav-item">Grid Editor</div>', unsafe_allow_html=True)
        st.markdown('<div class="nav-item">Move Objects</div>', unsafe_allow_html=True)
        st.markdown('<div class="nav-item nav-active">Add Objects</div>', unsafe_allow_html=True)

    with st.expander("Upload / reset layout"):
        uploaded = st.file_uploader("CSV layout", type=["csv"])
        if uploaded:
            try:
                st.session_state.layout_df = clean_layout(pd.read_csv(uploaded))
                st.success("Layout uploaded.")
            except Exception as e:
                st.error(f"Invalid CSV: {e}")
        if st.button("Reset layout demo"):
            st.session_state.layout_df = demo_layout()

    with st.expander("Add object"):
        new_name = st.text_input("Object name", value="New Object", key="sidebar_new_name")
        new_type = st.selectbox("Type", list(TYPE_COLORS.keys()), index=0, key="sidebar_new_type")
        new_zone = st.selectbox("Zone", ["kitchen", "living", "dining", "entry"], index=0, key="sidebar_new_zone")
        if st.button("Add", key="sidebar_add_object"):
            new_row = pd.DataFrame(
                [{"name": new_name, "type": new_type, "zone": new_zone, "x": 100, "y": 100, "w": 50, "h": 50}]
            )
            st.session_state.layout_df = clean_layout(pd.concat([st.session_state.layout_df, new_row], ignore_index=True))
            st.session_state.selected_name = new_name
            st.rerun()

    with st.expander("Remove object"):
        current_layout = clean_layout(st.session_state.layout_df)
        if len(current_layout) > 0:
            remove_name = st.selectbox("Object to remove", current_layout["name"].tolist(), key="sidebar_remove_name")
            if st.button("Remove", key="sidebar_remove_object"):
                updated = current_layout[current_layout["name"] != remove_name]
                st.session_state.layout_df = clean_layout(updated)
                if len(st.session_state.layout_df) > 0:
                    st.session_state.selected_name = st.session_state.layout_df.iloc[0]["name"]
                else:
                    st.session_state.selected_name = ""
                st.rerun()
        else:
            st.write("No objects in the layout.")

    st.markdown('<br><div class="subtle">2. CLIENT PROFILE</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">Client Profile</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">Lifestyle & Habits</div>', unsafe_allow_html=True)

    st.markdown('<br><div class="subtle">3. ANALYSIS</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item nav-active">Audit Results</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">Heatmap</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">Suggestions</div>', unsafe_allow_html=True)

left, right = st.columns([0.72, 0.28], gap="large")

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Client profile</div>', unsafe_allow_html=True)
    client_type = st.selectbox("Client type", ["Couple", "Family", "Single", "Short-term rental", "Hospitality"], index=0)
    priority = st.selectbox("Main priority", ["Social interaction", "Aesthetics", "Practicality", "Comfort", "Balanced"], index=0)
    cooking = st.selectbox("Cooking habits", ["Rarely cooks", "Cooks sometimes", "Cooks often"], index=2)
    social = st.selectbox("Guests / social activity", ["Low", "Medium", "High"], index=2)
    accessibility = st.selectbox("Accessibility", ["Low", "Medium", "High"], index=1)
    style = st.selectbox("Preferred style", ["Minimal Warm", "Modern", "Natural", "Premium", "Functional"], index=0)
    st.markdown("</div>", unsafe_allow_html=True)

profile = {"priority": priority, "cooking": cooking, "social": social, "accessibility": accessibility, "style": style}

df = clean_layout(st.session_state.layout_df)
selected_name = st.session_state.get("selected_name", df.iloc[0]["name"] if len(df) > 0 else "")

if layout_mode == "Grid Editor":
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Grid Editor</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtle">Start from the sample layout, drag objects on the grid, then save the final position. The demo includes a few imperfect placements so the decision support suggestions are easier to read.</div>', unsafe_allow_html=True)
        grid_result = render_grid_editor(df)
        if grid_result is not None:
            try:
                new_df = clean_layout(pd.DataFrame(grid_result))
                if not new_df.equals(clean_layout(st.session_state.layout_df)):
                    st.session_state.layout_df = new_df
                    st.rerun()
                df = new_df
            except Exception:
                st.error("Unable to update the layout from the drag-and-drop component.")
        st.markdown("</div>", unsafe_allow_html=True)

elif layout_mode == "Move Objects":
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">1. Editable analyzed layout</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtle">Open space - 900 cm x 400 cm - select an object and edit X/Y to move it</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Move object</div>', unsafe_allow_html=True)
        if len(df) > 0:
            names = df["name"].tolist()
            selected_name = st.selectbox("Selected object", names, index=names.index(selected_name) if selected_name in names else 0)
            st.session_state.selected_name = selected_name
            idx = df.index[df["name"] == selected_name][0]
            row = df.loc[idx]
            can_wall = row.type in {"door", "window"}
            min_pos = -WALL_CM if can_wall else 0
            new_x = st.number_input("X cm", min_value=min_pos, max_value=ROOM_W_CM, value=int(row.x), step=10)
            new_y = st.number_input("Y cm", min_value=min_pos, max_value=ROOM_H_CM, value=int(row.y), step=10)
            new_w = st.number_input("Width cm", min_value=10, max_value=ROOM_W_CM, value=int(row.w), step=10)
            new_h = st.number_input("Depth / height cm", min_value=10, max_value=ROOM_H_CM, value=int(row.h), step=10)
            df.loc[idx, ["x", "y", "w", "h"]] = [int(new_x), int(new_y), int(new_w), int(new_h)]
            st.session_state.layout_df = clean_layout(df)
            st.markdown('<span class="subtle">Changes are applied automatically.</span>', unsafe_allow_html=True)
            if st.button("Remove selected object"):
                st.session_state.layout_df = clean_layout(st.session_state.layout_df[st.session_state.layout_df["name"] != selected_name])
                if len(st.session_state.layout_df) > 0:
                    st.session_state.selected_name = st.session_state.layout_df.iloc[0]["name"]
                else:
                    st.session_state.selected_name = ""
                st.rerun()
        else:
            st.write("No objects in the layout.")
        st.markdown("</div>", unsafe_allow_html=True)

elif layout_mode == "Add Objects":
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Add Object Manually</div>', unsafe_allow_html=True)
        new_name = st.text_input("Object name", value="New Object", key="page_new_name")
        new_type = st.selectbox("Type", list(TYPE_COLORS.keys()), index=0, key="page_new_type")
        new_zone = st.selectbox("Zone", ["kitchen", "living", "dining", "entry"], index=0, key="page_new_zone")
        new_x = st.number_input("X cm", min_value=-WALL_CM, max_value=ROOM_W_CM, value=100, step=10, key="page_new_x")
        new_y = st.number_input("Y cm", min_value=-WALL_CM, max_value=ROOM_H_CM, value=100, step=10, key="page_new_y")
        new_w = st.number_input("Width cm", min_value=10, max_value=ROOM_W_CM, value=50, step=10, key="page_new_w")
        new_h = st.number_input("Height cm", min_value=10, max_value=ROOM_H_CM, value=50, step=10, key="page_new_h")
        if st.button("Add", key="page_add_object"):
            new_row = pd.DataFrame(
                [{"name": new_name, "type": new_type, "zone": new_zone, "x": new_x, "y": new_y, "w": new_w, "h": new_h}]
            )
            st.session_state.layout_df = clean_layout(pd.concat([st.session_state.layout_df, new_row], ignore_index=True))
            st.session_state.selected_name = new_name
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

macro, sub, clear, diagnostics = compute_scores(df, profile)

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.pyplot(draw_plan(df, selected=selected_name), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown(
        f"""
    <div class="card">
        <div class="section-title">Client Fit Overview</div>
        <div style="font-size:2.4rem;font-weight:850;color:#111827;margin-top:10px;">{int(macro["Client Fit"])}<span class="subtle"> /100</span></div>
        <div style="color:#2e9d55;font-weight:700;">{status(macro["Client Fit"])}</div>
        <br>
        <span class="badge">{priority}</span>
        <span class="badge">{style}</span>
        <span class="badge">{cooking}</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">2. Analysis results</div>', unsafe_allow_html=True)
cols = st.columns(5)
for col, (cat, score) in zip(cols, macro.items()):
    with col:
        st.markdown(metric_card(cat, score, sub[cat]), unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

issues, tradeoffs, suggestions = layout_feedback(sub, diagnostics)
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(list_card("Main issues", issues), unsafe_allow_html=True)
with c2:
    st.markdown(list_card("Key trade-offs", tradeoffs), unsafe_allow_html=True)
with c3:
    st.markdown(list_card("Key suggestions", suggestions), unsafe_allow_html=True)

with st.expander("Advanced editor: edit all objects"):
    edited = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "type": st.column_config.SelectboxColumn("type", options=list(TYPE_COLORS.keys())),
            "zone": st.column_config.SelectboxColumn("zone", options=["entry", "kitchen", "dining", "living", "other"]),
            "x": st.column_config.NumberColumn("x", min_value=-WALL_CM, max_value=ROOM_W_CM, step=10),
            "y": st.column_config.NumberColumn("y", min_value=-WALL_CM, max_value=ROOM_H_CM, step=10),
            "w": st.column_config.NumberColumn("w", min_value=10, max_value=ROOM_W_CM, step=10),
            "h": st.column_config.NumberColumn("h", min_value=10, max_value=ROOM_H_CM, step=10),
        },
        key="layout_editor",
    )
    if st.button("Update layout from table"):
        st.session_state.layout_df = clean_layout(edited)

with st.expander("Heatmap and technical diagnostics"):
    st.pyplot(draw_heatmap(clear), use_container_width=True)
    diag = pd.DataFrame(
        [
            ["Furniture density", f"{diagnostics['density']:.1%}"],
            ["Area with critical clearance < 60 cm", f"{diagnostics['critical']:.1%}"],
            ["Comfortable area >= 90 cm", f"{diagnostics['comfortable']:.1%}"],
            ["Usable-space fragmentation", f"{diagnostics['fragmentation']:.2f}"],
            ["Narrowest key route", f"{diagnostics['min_route_width']:.0f} cm"],
            ["Average key route width", f"{diagnostics['avg_route_width']:.0f} cm"],
            ["Naturally lit free area", f"{diagnostics['lit_ratio']:.1%}"],
            ["Kitchen triangle quality", f"{diagnostics['kitchen_triangle']:.0f}/100"],
            ["Dining-kitchen clearance", f"{diagnostics['dining_service_clearance']:.0f} cm"],
        ],
        columns=["Indicator", "Value"],
    )
    st.dataframe(diag, hide_index=True, use_container_width=True)

with st.expander("Export current layout"):
    st.download_button(
        "Download modified layout CSV",
        data=clean_layout(st.session_state.layout_df).to_csv(index=False).encode("utf-8"),
        file_name="modified_layout.csv",
        mime="text/csv",
    )
