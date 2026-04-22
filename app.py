import copy
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from logic import layout_base, analyze_layout, compare_layouts, layout_is_valid


st.set_page_config(page_title="Kitchen Layout Decision Support", layout="wide")


def get_object_by_id(layout_data, object_id):
    for obj in layout_data["objects"]:
        if obj["id"] == object_id:
            return obj
    return None


def plot_layout(layout_data, title):
    room_width = layout_data["room"]["width"]
    room_depth = layout_data["room"]["depth"]

    fig, ax = plt.subplots(figsize=(6, 5))

    # Room boundary
    room_rect = Rectangle((0, 0), room_width, room_depth, fill=False, linewidth=2)
    ax.add_patch(room_rect)

    # Objects
    for obj in layout_data["objects"]:
        rect = Rectangle(
            (obj["x"], obj["y"]),
            obj["width"],
            obj["depth"],
            fill=True,
            alpha=0.5
        )
        ax.add_patch(rect)

        label = obj["type"]
        center_x = obj["x"] + obj["width"] / 2
        center_y = obj["y"] + obj["depth"] / 2
        ax.text(center_x, center_y, label, ha="center", va="center", fontsize=8)

    # Door (simple representation)
    door = layout_data["door"]
    if door["orientation"] == "vertical":
        ax.plot(
            [door["x"], door["x"]],
            [door["y"], door["y"] + door["width"]],
            linewidth=4
        )
    else:
        ax.plot(
            [door["x"], door["x"] + door["width"]],
            [door["y"], door["y"]],
            linewidth=4
        )

    ax.set_xlim(0, room_width)
    ax.set_ylim(0, room_depth)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.set_title(title)
    ax.set_xlabel("x (cm)")
    ax.set_ylabel("y (cm)")

    return fig


def update_object_position(layout_data, object_id, new_x, new_y):
    obj = get_object_by_id(layout_data, object_id)
    if obj is not None:
        obj["x"] = new_x
        obj["y"] = new_y


st.title("Kitchen Layout Decision Support MVP")
st.write("Compare a baseline kitchen layout with an exploratory candidate layout.")

baseline_layout = copy.deepcopy(layout_base)
candidate_layout = copy.deepcopy(layout_base)

room_width = candidate_layout["room"]["width"]
room_depth = candidate_layout["room"]["depth"]

st.sidebar.header("Candidate Layout Controls")

editable_object_ids = ["fridge_1", "sink_1", "stove_1", "table_1"]

for object_id in editable_object_ids:
    obj = get_object_by_id(candidate_layout, object_id)
    if obj is None:
        continue

    st.sidebar.subheader(obj["type"].capitalize())

    max_x = room_width - obj["width"]
    max_y = room_depth - obj["depth"]

    new_x = st.sidebar.number_input(
        f"{obj['type']} x",
        min_value=0,
        max_value=max_x,
        value=int(obj["x"]),
        step=10,
        key=f"{object_id}_x"
    )

    new_y = st.sidebar.number_input(
        f"{obj['type']} y",
        min_value=0,
        max_value=max_y,
        value=int(obj["y"]),
        step=10,
        key=f"{object_id}_y"
    )

    update_object_position(candidate_layout, object_id, new_x, new_y)

is_valid = layout_is_valid(candidate_layout["objects"])

plot_col_1, plot_col_2 = st.columns(2)

with plot_col_1:
    st.subheader("Baseline Layout")
    fig_base = plot_layout(baseline_layout, "Baseline")
    st.pyplot(fig_base)

with plot_col_2:
    st.subheader("Candidate Layout")
    fig_candidate = plot_layout(candidate_layout, "Candidate")
    st.pyplot(fig_candidate)

if not is_valid:
    st.error("Invalid layout: some objects overlap. Please adjust the object positions.")
else:
    result_base = analyze_layout(baseline_layout)
    result_candidate = analyze_layout(candidate_layout)
    comparison = compare_layouts(result_base, result_candidate)

    score_col_1, score_col_2 = st.columns(2)

    with score_col_1:
        st.subheader("Baseline Scores")
        st.metric("Space Score", f"{result_base['space_score']:.4f}")
        st.metric("Workflow Score", f"{result_base['workflow_score']:.4f}")

    with score_col_2:
        st.subheader("Candidate Scores")
        st.metric("Space Score", f"{result_candidate['space_score']:.4f}")
        st.metric("Workflow Score", f"{result_candidate['workflow_score']:.4f}")

    st.subheader("Comparison Summary")
    st.write(f"**Space winner:** {comparison['space_winner']}")
    st.write(f"**Workflow winner:** {comparison['workflow_winner']}")
    st.write(f"**Recommendation:** {comparison['recommendation']}")