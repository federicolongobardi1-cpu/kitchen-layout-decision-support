import copy

import matplotlib.pyplot as plt
import streamlit as st
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

def apply_custom_style():
    st.markdown(
        """
        <style>
        .stApp {
            background: #f6f4ef;
            color: #27313f;
        }

        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e3ded5;
        }

        .app-header {
            padding: 1.1rem 1.25rem;
            border: 1px solid #e3ded5;
            background: #ffffff;
            border-radius: 8px;
            margin-bottom: 1rem;
        }

        .app-title {
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.1;
            margin: 0 0 0.35rem 0;
            color: #27313f;
        }

        .app-subtitle {
            font-size: 1rem;
            margin: 0;
            color: #657080;
        }

        .score-panel {
            border: 1px solid #e3ded5;
            background: #ffffff;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }

        .score-panel-title {
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
            color: #27313f;
        }

        .score-label {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            font-size: 0.9rem;
            color: #465366;
            margin: 0.3rem 0;
        }

        div[data-testid="stExpander"] {
            background: #ffffff;
            border: 1px solid #e3ded5;
            border-radius: 8px;
        }

        .layout-legend {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem 0.85rem;
            align-items: center;
            color: #465366;
            font-size: 0.9rem;
            margin: 0.35rem 0 1rem 0;
        }

        .legend-item {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }

        .legend-swatch {
            width: 0.85rem;
            height: 0.85rem;
            border-radius: 3px;
            border: 1px solid #27313f;
            display: inline-block;
        }

        [data-testid="stSidebar"] div.stButton > button {
            background: #2f7a67;
            color: #ffffff;
            border: 1px solid #276756;
            border-radius: 8px;
            font-weight: 700;
            width: 100%;
        }

        [data-testid="stSidebar"] div.stButton > button:hover {
            background: #276756;
            color: #ffffff;
            border-color: #1f5446;
        }

        [data-testid="stSidebar"] div.stButton > button:disabled {
            background: #d8d2c8;
            color: #8a8175;
            border-color: #d8d2c8;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_object_by_id(layout_data, object_id):
    for obj in layout_data["objects"]:
        if obj["id"] == object_id:
            return obj
    return None


def plot_layout(layout_data, title):
    room_width = layout_data["room"]["width"]
    room_depth = layout_data["room"]["depth"]

    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#fbfaf7")
    ax.set_axisbelow(True)

    room_rect = Rectangle(
        (0, 0),
        room_width,
        room_depth,
        fill=False,
        linewidth=2.2,
        edgecolor="#27313f",
        zorder=3,
    )
    ax.add_patch(room_rect)

    for obj in layout_data["objects"]:
        color = OBJECT_COLORS.get(obj["type"], "#9AA3AF")
        rect = Rectangle(
            (obj["x"], obj["y"]),
            obj["width"],
            obj["depth"],
            fill=True,
            facecolor=color,
            edgecolor="#27313f",
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
            color="#1f2937",
            zorder=4,
        )

    door = layout_data["door"]
    if door["orientation"] == "vertical":
        ax.plot(
            [door["x"], door["x"]],
            [door["y"], door["y"] + door["width"]],
            linewidth=5,
            color="#111827",
            solid_capstyle="round",
            zorder=4,
        )
    else:
        ax.plot(
            [door["x"], door["x"] + door["width"]],
            [door["y"], door["y"]],
            linewidth=5,
            color="#111827",
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
    ax.grid(True, color="#e5e1d8", linewidth=0.6, zorder=0)
    ax.tick_params(colors="#657080", labelsize=8)
    ax.title.set_color("#27313f")
    ax.xaxis.label.set_color("#657080")
    ax.yaxis.label.set_color("#657080")
    for spine in ax.spines.values():
        spine.set_visible(False)

    return fig


def update_object_position(layout_data, object_id, new_x, new_y):
    obj = get_object_by_id(layout_data, object_id)
    if obj is not None:
        obj["x"] = new_x
        obj["y"] = new_y


def get_base_dimensions(obj):
    if obj["orientation"] in (90, 270):
        return obj["depth"], obj["width"]
    return obj["width"], obj["depth"]


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
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(result["space_score"])

    st.markdown(
        f"""
        <div class="score-panel">
            <div class="score-label">
                <span>Workflow score</span>
                <strong>{result['workflow_score']:.4f}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(result["workflow_score"])


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


apply_custom_style()

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

baseline_layout = copy.deepcopy(st.session_state["baseline_layout"])
candidate_layout = copy.deepcopy(baseline_layout)

room_width = candidate_layout["room"]["width"]
room_depth = candidate_layout["room"]["depth"]

st.sidebar.header("Candidate Layout Controls")

editable_object_ids = ["fridge_1", "sink_1", "stove_1", "oven_1", "table_1"]

for object_id in editable_object_ids:
    obj = get_object_by_id(candidate_layout, object_id)
    if obj is None:
        continue

    st.sidebar.subheader(obj["type"].capitalize())

    new_orientation = st.sidebar.selectbox(
        f"{obj['type']} rotation",
        options=[0, 90, 180, 270],
        index=[0, 90, 180, 270].index(obj["orientation"]),
        format_func=lambda value: f"{value} deg",
        key=f"{object_id}_orientation",
    )

    rotate_object(obj, new_orientation)
    clamp_session_position(object_id, obj, room_width, room_depth)

    max_x = room_width - obj["width"]
    max_y = room_depth - obj["depth"]

    new_x = st.sidebar.number_input(
        f"{obj['type']} x",
        min_value=0,
        max_value=max_x,
        value=int(obj["x"]),
        step=10,
        key=f"{object_id}_x",
    )

    new_y = st.sidebar.number_input(
        f"{obj['type']} y",
        min_value=0,
        max_value=max_y,
        value=int(obj["y"]),
        step=10,
        key=f"{object_id}_y",
    )

    update_object_position(candidate_layout, object_id, new_x, new_y)

is_valid = layout_is_valid(candidate_layout["objects"])

if st.sidebar.button("Update baseline with candidate", disabled=not is_valid):
    st.session_state["baseline_layout"] = copy.deepcopy(candidate_layout)
    st.rerun()

plot_col_1, plot_col_2 = st.columns(2)

with plot_col_1:
    st.subheader("Baseline Layout")
    fig_base = plot_layout(baseline_layout, "Baseline")
    st.pyplot(fig_base)

with plot_col_2:
    st.subheader("Candidate Layout")
    fig_candidate = plot_layout(candidate_layout, "Candidate")
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
