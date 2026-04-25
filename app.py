import copy
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st
import streamlit.components.v1 as components
from matplotlib.patches import Rectangle

from logic import analyze_layout, compare_layouts, layout_base, layout_is_valid


st.set_page_config(page_title="Kitchen Layout Decision Support", layout="wide")


OBJECT_COLORS = {
    "fridge": "#5B8DEF",
    "sink": "#2FB7A7",
    "stove": "#F28C52",
    "oven": "#B06AB3",
    "table": "#D9A441",
}

DRAGGABLE_LAYOUT = components.declare_component(
    "draggable_layout",
    path=str(Path(__file__).parent / "components" / "draggable_layout"),
)
def hex_to_rgb(color):
    color = color.lstrip("#")
    if len(color) == 3:
        color = "".join(ch * 2 for ch in color)
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def mix_colors(base_color, overlay_color, ratio):
    base_rgb = hex_to_rgb(base_color)
    overlay_rgb = hex_to_rgb(overlay_color)
    mixed = tuple(
        round(base * (1 - ratio) + overlay * ratio)
        for base, overlay in zip(base_rgb, overlay_rgb)
    )
    return rgb_to_hex(mixed)


def resolve_theme():
    primary = st.get_option("theme.primaryColor") or "#5B8DEF"
    background = st.get_option("theme.backgroundColor") or "#ffffff"
    secondary_background = st.get_option("theme.secondaryBackgroundColor") or "#f0f2f6"
    text = st.get_option("theme.textColor") or "#262730"
    base = (st.get_option("theme.base") or "light").lower()
    is_dark = base == "dark"

    return {
        "app_bg": background,
        "text": text,
        "sidebar_bg": secondary_background,
        "panel_bg": background,
        "panel_border": mix_colors(secondary_background, text, 0.16 if is_dark else 0.12),
        "subtitle": mix_colors(text, background, 0.38 if is_dark else 0.45),
        "muted": mix_colors(text, background, 0.28 if is_dark else 0.35),
        "progress_bg": mix_colors(primary, background, 0.78 if is_dark else 0.84),
        "progress_fill": primary,
        "button_bg": primary,
        "button_border": mix_colors(primary, text, 0.18),
        "button_hover": mix_colors(primary, text, 0.12),
        "button_hover_border": mix_colors(primary, text, 0.28),
        "button_disabled_bg": mix_colors(secondary_background, text, 0.12 if is_dark else 0.06),
        "button_disabled_text": mix_colors(text, background, 0.52),
        "room_bg": mix_colors(background, secondary_background, 0.38 if is_dark else 0.5),
        "grid": mix_colors(background, text, 0.14 if is_dark else 0.08),
        "plot_text": text,
        "door": text,
        "fallback_object": mix_colors(secondary_background, text, 0.32 if is_dark else 0.24),
    }


def apply_custom_style(theme):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {theme["app_bg"]};
            color: {theme["text"]};
        }}

        [data-testid="stSidebar"] {{
            background: {theme["sidebar_bg"]};
            border-right: 1px solid {theme["panel_border"]};
        }}

        .app-header {{
            padding: 1.1rem 1.25rem;
            border: 1px solid {theme["panel_border"]};
            background: {theme["panel_bg"]};
            border-radius: 8px;
            margin-bottom: 1rem;
        }}

        .app-title {{
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.1;
            margin: 0 0 0.35rem 0;
            color: {theme["text"]};
        }}

        .app-subtitle {{
            font-size: 1rem;
            margin: 0;
            color: {theme["subtitle"]};
        }}

        .score-panel {{
            border: 1px solid {theme["panel_border"]};
            background: {theme["panel_bg"]};
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }}

        .score-panel-title {{
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
            color: {theme["text"]};
        }}

        .score-progress {{
            width: 100%;
            height: 0.95rem;
            background: {theme["progress_bg"]};
            border-radius: 999px;
            overflow: hidden;
            margin-top: 0.85rem;
        }}

        .score-progress-fill {{
            height: 100%;
            background: {theme["progress_fill"]};
            border-radius: 999px;
        }}

        .score-label {{
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            font-size: 0.9rem;
            color: {theme["muted"]};
            margin: 0.3rem 0;
        }}

        div[data-testid="stExpander"] {{
            background: {theme["panel_bg"]};
            border: 1px solid {theme["panel_border"]};
            border-radius: 8px;
        }}

        .layout-legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem 0.85rem;
            align-items: center;
            color: {theme["muted"]};
            font-size: 0.9rem;
            margin: 0.35rem 0 1rem 0;
        }}

        .legend-item {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }}

        .legend-swatch {{
            width: 0.85rem;
            height: 0.85rem;
            border-radius: 3px;
            border: 1px solid {theme["text"]};
            display: inline-block;
        }}

        [data-testid="stSidebar"] div.stButton > button {{
            background: {theme["button_bg"]};
            color: #ffffff;
            border: 1px solid {theme["button_border"]};
            border-radius: 8px;
            font-weight: 700;
            width: 100%;
        }}

        [data-testid="stSidebar"] div.stButton > button:hover {{
            background: {theme["button_hover"]};
            color: #ffffff;
            border-color: {theme["button_hover_border"]};
        }}

        [data-testid="stSidebar"] div.stButton > button:disabled {{
            background: {theme["button_disabled_bg"]};
            color: {theme["button_disabled_text"]};
            border-color: {theme["button_disabled_bg"]};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_object_by_id(layout_data, object_id):
    for obj in layout_data["objects"]:
        if obj["id"] == object_id:
            return obj
    return None


def plot_layout(layout_data, title, theme):
    room_width = layout_data["room"]["width"]
    room_depth = layout_data["room"]["depth"]

    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor(theme["panel_bg"])
    ax.set_facecolor(theme["room_bg"])
    ax.set_axisbelow(True)

    room_rect = Rectangle(
        (0, 0),
        room_width,
        room_depth,
        fill=False,
        linewidth=2.2,
        edgecolor=theme["text"],
        zorder=3,
    )
    ax.add_patch(room_rect)

    for obj in layout_data["objects"]:
        color = OBJECT_COLORS.get(obj["type"], theme["fallback_object"])
        rect = Rectangle(
            (obj["x"], obj["y"]),
            obj["width"],
            obj["depth"],
            fill=True,
            facecolor=color,
            edgecolor=theme["text"],
            linewidth=1.4,
            alpha=0.78,
            zorder=3,
        )
        ax.add_patch(rect)

        center_x = obj["x"] + obj["width"] / 2
        center_y = obj["y"] + obj["depth"] / 2
        ax.text(
            center_x,
            center_y,
            obj["type"],
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold",
            color=theme["plot_text"],
            zorder=4,
        )

    door = layout_data["door"]
    if door["orientation"] == "vertical":
        ax.plot(
            [door["x"], door["x"]],
            [door["y"], door["y"] + door["width"]],
            linewidth=5,
            color=theme["door"],
            solid_capstyle="round",
            zorder=4,
        )
    else:
        ax.plot(
            [door["x"], door["x"] + door["width"]],
            [door["y"], door["y"]],
            linewidth=5,
            color=theme["door"],
            solid_capstyle="round",
            zorder=4,
        )

    ax.set_xlim(0, room_width)
    ax.set_ylim(0, room_depth)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.set_title(title)
    ax.set_xlabel("x (cm)")
    ax.set_ylabel("y (cm)")
    ax.grid(True, color=theme["grid"], linewidth=0.6, zorder=0)
    ax.tick_params(colors=theme["subtitle"], labelsize=8)
    ax.title.set_color(theme["text"])
    ax.xaxis.label.set_color(theme["subtitle"])
    ax.yaxis.label.set_color(theme["subtitle"])
    for spine in ax.spines.values():
        spine.set_visible(False)

    return fig


def update_object_position(layout_data, object_id, new_x, new_y):
    obj = get_object_by_id(layout_data, object_id)
    if obj is not None:
        obj["x"] = new_x
        obj["y"] = new_y


def ensure_base_dimensions(obj):
    if "base_width" not in obj or "base_depth" not in obj:
        if obj["orientation"] in (90, 270):
            obj["base_width"] = obj["depth"]
            obj["base_depth"] = obj["width"]
        else:
            obj["base_width"] = obj["width"]
            obj["base_depth"] = obj["depth"]


def get_base_dimensions(obj):
    ensure_base_dimensions(obj)
    return obj["base_width"], obj["base_depth"]


def initialize_object_dimensions(layout_data):
    for obj in layout_data["objects"]:
        ensure_base_dimensions(obj)


def rotate_object(obj, orientation):
    base_width, base_depth = get_base_dimensions(obj)
    obj["orientation"] = orientation

    if orientation in (90, 270):
        obj["width"] = base_depth
        obj["depth"] = base_width
    else:
        obj["width"] = base_width
        obj["depth"] = base_depth


def clamp_session_position(object_id, obj, room_width, room_depth):
    max_x = room_width - obj["width"]
    max_y = room_depth - obj["depth"]

    x_key = f"{object_id}_x"
    y_key = f"{object_id}_y"

    if x_key in st.session_state:
        st.session_state[x_key] = min(st.session_state[x_key], max_x)
    if y_key in st.session_state:
        st.session_state[y_key] = min(st.session_state[y_key], max_y)


def render_draggable_layout(layout_data, editable_ids, theme):
    return DRAGGABLE_LAYOUT(
        layout_data=layout_data,
        editable_ids=editable_ids,
        object_colors=OBJECT_COLORS,
        theme=theme,
        default=None,
        key="candidate_drag_layout",
    )




def format_cm(value):
    if value is None:
        return "not reachable"
    return f"{value:.0f} cm"


def describe_workflow_path(path):
    distance = path["length_cm"]
    ideal_min = path["ideal_min_cm"]
    ideal_max = path["ideal_max_cm"]

    if distance is None:
        return "blocked path"
    if ideal_min is not None and distance < ideal_min:
        return "too close"
    if ideal_max is not None and distance > ideal_max:
        return "too far"
    return "ideal"


def build_workflow_rows(result):
    workflow_paths = result.get("workflow_paths", [])
    if not workflow_paths:
        return [
            {
                "Path": "-",
                "Distance": "-",
                "Ideal range": "-",
                "Score": "-",
                "Effect": "workflow details unavailable",
            }
        ]

    rows = []
    for path in workflow_paths:
        rows.append(
            {
                "Path": f"{path['from']} -> {path['to']}",
                "Distance": format_cm(path["length_cm"]),
                "Ideal range": (
                    f"{path['ideal_min_cm']:.0f}-{path['ideal_max_cm']:.0f} cm"
                    if path["ideal_min_cm"] is not None
                    else "-"
                ),
                "Score": f"{path['score']:.4f}",
                "Effect": describe_workflow_path(path),
            }
        )
    return rows


def build_space_rows(result):
    required_keys = [
        "clearance_stats",
        "walkability_stats",
        "usable_fragmentation_stats",
        "space_components",
    ]
    if any(key not in result for key in required_keys):
        return [
            {
                "Component": "-",
                "Score": "-",
                "Detail": "space details unavailable",
            }
        ]

    clearance_stats = result["clearance_stats"]
    walkability_stats = result["walkability_stats"]
    fragmentation_stats = result["usable_fragmentation_stats"]
    components = result["space_components"]

    return [
        {
            "Component": "Average clearance",
            "Score": f"{components['clearance_score']:.4f}",
            "Detail": f"{clearance_stats['avg_clearance_cm']:.0f} cm average free clearance",
        },
        {
            "Component": "Critical area",
            "Score": f"{components['critical_area_score']:.4f}",
            "Detail": f"{clearance_stats['critical_area_pct']:.1f}% of free cells under 60 cm",
        },
        {
            "Component": "Walkability",
            "Score": f"{components['walkability_score']:.4f}",
            "Detail": (
                f"{walkability_stats['good_pct']:.1f}% good, "
                f"{walkability_stats['medium_pct']:.1f}% medium, "
                f"{walkability_stats['poor_pct']:.1f}% poor"
            ),
        },
        {
            "Component": "Usable area",
            "Score": f"{components['usable_area_score']:.4f}",
            "Detail": (
                f"{fragmentation_stats['total_usable_cells']} usable cells, "
                f"{fragmentation_stats['num_components']} connected areas"
            ),
        },
    ]


def build_suggestion_rows(result):
    suggestions = []

    workflow_paths = result.get("workflow_paths", [])
    for path in workflow_paths:
        effect = describe_workflow_path(path)
        if path["score"] < 0.75:
            if effect == "too far":
                suggestion = "Move these two elements closer or reduce obstacles between them."
            elif effect == "too close":
                suggestion = "Add more working distance between these two elements."
            elif effect == "blocked path":
                suggestion = "Move blocking objects to restore a reachable walking path."
            else:
                suggestion = "Review this workflow segment."

            suggestions.append(
                {
                    "Area": "Workflow",
                    "Issue": f"{path['from']} -> {path['to']} is {effect}",
                    "Score": f"{path['score']:.4f}",
                    "Suggestion": suggestion,
                }
            )

    required_keys = [
        "space_components",
        "clearance_stats",
        "walkability_stats",
        "usable_fragmentation_stats",
    ]
    if any(key not in result for key in required_keys):
        suggestions.append(
            {
                "Area": "Details",
                "Issue": "Score details are unavailable",
                "Score": "-",
                "Suggestion": (
                    "Restart Streamlit or redeploy with the updated logic.py so "
                    "the app can explain score components."
                ),
            }
        )
        return suggestions

    components = result["space_components"]
    clearance_stats = result["clearance_stats"]
    walkability_stats = result["walkability_stats"]
    fragmentation_stats = result["usable_fragmentation_stats"]

    if components["clearance_score"] < 0.65:
        suggestions.append(
            {
                "Area": "Space",
                "Issue": "Average clearance is low",
                "Score": f"{components['clearance_score']:.4f}",
                "Suggestion": (
                    f"Increase free passage width; current average is "
                    f"{clearance_stats['avg_clearance_cm']:.0f} cm."
                ),
            }
        )

    if components["critical_area_score"] < 0.75:
        suggestions.append(
            {
                "Area": "Space",
                "Issue": "Too much critical area",
                "Score": f"{components['critical_area_score']:.4f}",
                "Suggestion": (
                    f"Reduce zones below 60 cm clearance; currently "
                    f"{clearance_stats['critical_area_pct']:.1f}% of free cells."
                ),
            }
        )

    if components["walkability_score"] < 0.65:
        suggestions.append(
            {
                "Area": "Space",
                "Issue": "Walkability is weak",
                "Score": f"{components['walkability_score']:.4f}",
                "Suggestion": (
                    f"Open wider walking corridors; poor cells are "
                    f"{walkability_stats['poor_pct']:.1f}%."
                ),
            }
        )

    if components["usable_area_score"] < 0.65:
        suggestions.append(
            {
                "Area": "Space",
                "Issue": "Usable area is limited",
                "Score": f"{components['usable_area_score']:.4f}",
                "Suggestion": (
                    f"Try reducing fragmentation; usable space is split into "
                    f"{fragmentation_stats['num_components']} connected areas."
                ),
            }
        )

    if not suggestions:
        suggestions.append(
            {
                "Area": "Overall",
                "Issue": "No major weak component detected",
                "Score": "-",
                "Suggestion": "The current candidate has no component below the warning thresholds.",
            }
        )

    return suggestions


def render_score_panel(title, result):
    st.markdown(
        f"""
        <div class="score-panel">
            <div class="score-panel-title">{title}</div>
            <div class="score-label">
                <span>Space score</span>
                <strong>{result['space_score']:.4f}</strong>
            </div>
            <div class="score-progress">
                <div class="score-progress-fill" style="width:{result['space_score'] * 100:.1f}%"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="score-panel">
            <div class="score-label">
                <span>Workflow score</span>
                <strong>{result['workflow_score']:.4f}</strong>
            </div>
            <div class="score-progress">
                <div class="score-progress-fill" style="width:{result['workflow_score'] * 100:.1f}%"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_layout_legend():
    items = []
    for object_type, color in OBJECT_COLORS.items():
        items.append(
            f'<span class="legend-item">'
            f'<span class="legend-swatch" style="background:{color};"></span>'
            f"{object_type}</span>"
        )

    st.markdown(
        f"<div class='layout-legend'>{''.join(items)}</div>",
        unsafe_allow_html=True,
    )

theme = resolve_theme()
apply_custom_style(theme)

st.markdown(
    """
    <div class="app-header">
        <div class="app-title">Kitchen Layout Decision Support</div>
        <p class="app-subtitle">
            Compare baseline and candidate layouts, move components, rotate them,
            and inspect why each score changes.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "baseline_layout" not in st.session_state:
    st.session_state["baseline_layout"] = copy.deepcopy(layout_base)
if "candidate_layout" not in st.session_state:
    st.session_state["candidate_layout"] = copy.deepcopy(st.session_state["baseline_layout"])

baseline_layout = copy.deepcopy(st.session_state["baseline_layout"])
initialize_object_dimensions(baseline_layout)
candidate_layout = copy.deepcopy(st.session_state["candidate_layout"])
initialize_object_dimensions(candidate_layout)

room_width = candidate_layout["room"]["width"]
room_depth = candidate_layout["room"]["depth"]

editable_object_ids = ["fridge_1", "sink_1", "stove_1", "oven_1", "table_1"]

drag_event = render_draggable_layout(candidate_layout, editable_object_ids, theme)
if drag_event:
    event_id = drag_event.get("event_id")
    if event_id != st.session_state.get("last_drag_event_id"):
        updated_candidate_layout = copy.deepcopy(st.session_state["candidate_layout"])
        initialize_object_dimensions(updated_candidate_layout)

        for object_id, orientation in drag_event.get("orientations", {}).items():
            if object_id not in editable_object_ids:
                continue
            obj = get_object_by_id(updated_candidate_layout, object_id)
            if obj is None:
                continue
            rotate_object(obj, int(orientation))

            max_x = updated_candidate_layout["room"]["width"] - obj["width"]
            max_y = updated_candidate_layout["room"]["depth"] - obj["depth"]
            obj["x"] = min(obj["x"], max_x)
            obj["y"] = min(obj["y"], max_y)

        for object_id, position in drag_event.get("positions", {}).items():
            if object_id not in editable_object_ids:
                continue
            obj = get_object_by_id(updated_candidate_layout, object_id)
            if obj is None:
                continue

            max_x = updated_candidate_layout["room"]["width"] - obj["width"]
            max_y = updated_candidate_layout["room"]["depth"] - obj["depth"]
            obj["x"] = min(int(position["x"]), max_x)
            obj["y"] = min(int(position["y"]), max_y)

        st.session_state["candidate_layout"] = copy.deepcopy(updated_candidate_layout)
        st.session_state["last_drag_event_id"] = event_id
        st.rerun()

st.sidebar.header("Layout Actions")
st.sidebar.caption("Move objects directly in the editor. Double click an object to rotate it by 90 deg.")

is_valid = layout_is_valid(candidate_layout["objects"])

if st.sidebar.button("Reset candidate to baseline"):
    st.session_state["candidate_layout"] = copy.deepcopy(st.session_state["baseline_layout"])
    st.rerun()

if st.sidebar.button("Update baseline with candidate", disabled=not is_valid):
    st.session_state["baseline_layout"] = copy.deepcopy(candidate_layout)
    st.session_state["candidate_layout"] = copy.deepcopy(candidate_layout)
    st.rerun()

plot_col_1, plot_col_2 = st.columns(2)

with plot_col_1:
    st.subheader("Baseline Layout")
    fig_base = plot_layout(baseline_layout, "Baseline", theme)
    st.pyplot(fig_base)

with plot_col_2:
    st.subheader("Candidate Layout")
    fig_candidate = plot_layout(candidate_layout, "Candidate", theme)
    st.pyplot(fig_candidate)

render_layout_legend()

if not is_valid:
    st.error("Invalid layout: some objects overlap. Please adjust the object positions.")
else:
    result_base = analyze_layout(baseline_layout)
    result_candidate = analyze_layout(candidate_layout)
    comparison = compare_layouts(result_base, result_candidate)

    if "workflow_paths" not in result_candidate:
        st.sidebar.warning("Score details are not loaded. Restart the app after updating logic.py.")

    score_col_1, score_col_2 = st.columns(2)

    with score_col_1:
        render_score_panel("Baseline Scores", result_base)

    with score_col_2:
        render_score_panel("Candidate Scores", result_candidate)

    st.subheader("Suggestions")
    st.table(build_suggestion_rows(result_candidate))

    st.subheader("Score Breakdown")

    detail_col_1, detail_col_2 = st.columns(2)

    with detail_col_1:
        with st.expander("Baseline workflow details", expanded=False):
            st.table(build_workflow_rows(result_base))
        with st.expander("Baseline space details", expanded=False):
            st.table(build_space_rows(result_base))

    with detail_col_2:
        with st.expander("Candidate workflow details", expanded=True):
            st.table(build_workflow_rows(result_candidate))
        with st.expander("Candidate space details", expanded=False):
            st.table(build_space_rows(result_candidate))

    st.subheader("Comparison Summary")
    st.write(f"**Space winner:** {comparison['space_winner']}")
    st.write(f"**Workflow winner:** {comparison['workflow_winner']}")
    st.write(f"**Recommendation:** {comparison['recommendation']}")
