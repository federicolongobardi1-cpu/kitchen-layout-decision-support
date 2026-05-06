import copy
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st
import streamlit.components.v1 as components
from matplotlib.patches import Rectangle

from logic import CELL_SIZE, analyze_layout, compare_layouts, layout_base, layout_is_valid


st.set_page_config(page_title="Kitchen Layout Decision Support", layout="wide")


OBJECT_COLORS = {
    "fridge": "#5B8DEF",
    "sink": "#2FB7A7",
    "stove": "#F28C52",
    "oven": "#B06AB3",
    "table": "#D9A441",
    "sofa": "#6A8D73",
    "tv": "#2F3A45",
    "bed": "#9B7EDE",
    "wardrobe": "#A66E4A",
    "shower": "#4FB3D8",
    "toilet": "#A8B3BD",
    "vanity": "#C7956D",
    "outdoor_table": "#7AA95C",
    "chair": "#D8A64F",
    "plant": "#3E9C5C",
    "pantry": "#C58A3A",
    "countertop": "#8B9A46",
}

DRAGGABLE_LAYOUT = components.declare_component(
    "draggable_layout",
    path=str(Path(__file__).parent / "components" / "draggable_layout"),
)
OPENING_LAYOUT = components.declare_component(
    "opening_layout",
    path=str(Path(__file__).parent / "components" / "opening_layout"),
)

APP_DIR = Path(__file__).parent
BRAND_GREEN = "#35C462"
BRAND_GREEN_DARK = "#23994B"
BRAND_GREEN_SOFT = "#E8F7EE"

INTERIOR_IMAGES = [
    "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1556911220-bff31c812dba?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=900&q=80",
]

ROOM_TYPES = {
    "kitchen": {
        "label": "Kitchen",
        "description": "Cooking workflow and appliance placement.",
        "image": "https://images.unsplash.com/photo-1556911220-bff31c812dba?auto=format&fit=crop&w=900&q=80",
        "width_cm": 400,
        "depth_cm": 300,
    },
    "bathroom": {
        "label": "Bathroom",
        "description": "Fixtures, access clearances, and compact layouts.",
        "image": "https://images.unsplash.com/photo-1620626011761-996317b8d101?auto=format&fit=crop&w=900&q=80",
        "width_cm": 240,
        "depth_cm": 220,
    },
    "living_room": {
        "label": "Living room",
        "description": "Seating, media wall, and circulation space.",
        "image": "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=900&q=80",
        "width_cm": 500,
        "depth_cm": 400,
    },
    "bedroom": {
        "label": "Bedroom",
        "description": "Bed, storage, and comfortable walking paths.",
        "image": "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=900&q=80",
        "width_cm": 420,
        "depth_cm": 360,
    },
    "outdoor": {
        "label": "Outdoor",
        "description": "Terrace or garden furniture arrangement.",
        "image": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=900&q=80",
        "width_cm": 600,
        "depth_cm": 400,
    },
    "dining_room": {
        "label": "Dining room",
        "description": "Table placement, circulation, and serving paths.",
        "image": "https://images.unsplash.com/photo-1617104551722-3b2d51366400?auto=format&fit=crop&w=900&q=80",
        "width_cm": 420,
        "depth_cm": 360,
    },
    "home_office": {
        "label": "Home office",
        "description": "Desk, storage, and ergonomic working clearance.",
        "image": "https://images.unsplash.com/photo-1593476550610-87baa860004a?auto=format&fit=crop&w=900&q=80",
        "width_cm": 320,
        "depth_cm": 280,
    },
    "laundry_room": {
        "label": "Laundry room",
        "description": "Appliance access, storage, and utility workflow.",
        "image": "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?auto=format&fit=crop&w=900&q=80",
        "width_cm": 260,
        "depth_cm": 240,
    },
    "entryway": {
        "label": "Entryway",
        "description": "Arrival flow, coats, shoes, and passage width.",
        "image": "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?auto=format&fit=crop&w=900&q=80",
        "width_cm": 260,
        "depth_cm": 200,
    },
    "storage": {
        "label": "Storage",
        "description": "Shelving, wardrobes, and compact service space.",
        "image": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=900&q=80",
        "width_cm": 240,
        "depth_cm": 220,
    },
    "garage": {
        "label": "Garage",
        "description": "Parking area, storage zones, and access paths.",
        "image": "https://images.unsplash.com/photo-1597007056704-67bf2068d5b2?auto=format&fit=crop&w=900&q=80",
        "width_cm": 600,
        "depth_cm": 550,
    },
}

FURNITURE_CATALOG = {
    "kitchen": [
        {"type": "fridge", "label": "Fridge", "width": 60, "depth": 60},
        {"type": "oven", "label": "Oven", "width": 60, "depth": 60},
        {"type": "sink", "label": "Sink", "width": 80, "depth": 60},
        {"type": "stove", "label": "Stove", "width": 60, "depth": 60},
        {"type": "countertop", "label": "Kitchen worktop", "width": 120, "depth": 60},
        {"type": "table", "label": "Table", "width": 120, "depth": 80},
        {"type": "pantry", "label": "Pantry", "width": 80, "depth": 60},
    ],
    "bathroom": [
        {"type": "shower", "label": "Shower", "width": 90, "depth": 90},
        {"type": "toilet", "label": "Toilet", "width": 40, "depth": 70},
        {"type": "sink", "label": "Sink", "width": 70, "depth": 45},
        {"type": "vanity", "label": "Vanity", "width": 90, "depth": 50},
    ],
    "living_room": [
        {"type": "sofa", "label": "Sofa", "width": 220, "depth": 90},
        {"type": "tv", "label": "TV unit", "width": 160, "depth": 40},
        {"type": "table", "label": "Coffee table", "width": 110, "depth": 60},
        {"type": "plant", "label": "Plant", "width": 40, "depth": 40},
    ],
    "bedroom": [
        {"type": "bed", "label": "Bed", "width": 160, "depth": 200},
        {"type": "wardrobe", "label": "Wardrobe", "width": 180, "depth": 60},
        {"type": "table", "label": "Desk", "width": 120, "depth": 60},
        {"type": "chair", "label": "Chair", "width": 50, "depth": 50},
    ],
    "outdoor": [
        {"type": "outdoor_table", "label": "Outdoor table", "width": 160, "depth": 90},
        {"type": "chair", "label": "Chair", "width": 55, "depth": 55},
        {"type": "sofa", "label": "Outdoor sofa", "width": 210, "depth": 85},
        {"type": "plant", "label": "Planter", "width": 60, "depth": 60},
    ],
    "dining_room": [
        {"type": "table", "label": "Dining table", "width": 180, "depth": 90},
        {"type": "chair", "label": "Chair", "width": 50, "depth": 50},
        {"type": "wardrobe", "label": "Sideboard", "width": 160, "depth": 45},
        {"type": "plant", "label": "Plant", "width": 40, "depth": 40},
    ],
    "home_office": [
        {"type": "table", "label": "Desk", "width": 140, "depth": 70},
        {"type": "chair", "label": "Office chair", "width": 60, "depth": 60},
        {"type": "wardrobe", "label": "Bookshelf", "width": 120, "depth": 35},
        {"type": "plant", "label": "Plant", "width": 40, "depth": 40},
    ],
    "laundry_room": [
        {"type": "vanity", "label": "Washing machine", "width": 60, "depth": 65},
        {"type": "vanity", "label": "Dryer", "width": 60, "depth": 65},
        {"type": "sink", "label": "Utility sink", "width": 70, "depth": 55},
        {"type": "wardrobe", "label": "Storage cabinet", "width": 100, "depth": 45},
    ],
    "entryway": [
        {"type": "wardrobe", "label": "Coat closet", "width": 120, "depth": 55},
        {"type": "table", "label": "Console", "width": 110, "depth": 35},
        {"type": "chair", "label": "Bench", "width": 120, "depth": 45},
        {"type": "plant", "label": "Plant", "width": 40, "depth": 40},
    ],
    "storage": [
        {"type": "wardrobe", "label": "Shelving unit", "width": 120, "depth": 45},
        {"type": "wardrobe", "label": "Cabinet", "width": 90, "depth": 50},
        {"type": "table", "label": "Utility table", "width": 120, "depth": 60},
        {"type": "chair", "label": "Step stool", "width": 45, "depth": 45},
    ],
    "garage": [
        {"type": "table", "label": "Car footprint", "width": 200, "depth": 450},
        {"type": "wardrobe", "label": "Storage shelves", "width": 180, "depth": 50},
        {"type": "table", "label": "Workbench", "width": 180, "depth": 70},
        {"type": "chair", "label": "Bike area", "width": 180, "depth": 70},
    ],
}

OPENING_SIDES = ["top", "right", "bottom", "left"]

OPENING_CATEGORIES = {
    "door": {
        "label": "Doors",
        "image": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=700&q=80",
    },
    "window": {
        "label": "Windows",
        "image": "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=700&q=80",
    },
}

OPENING_TYPES = {
    "door": [
        {"type": "single", "label": "Single", "width": 90, "image": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=700&q=80"},
        {"type": "double", "label": "Double", "width": 160, "image": "https://images.unsplash.com/photo-1600566752355-35792bedcfea?auto=format&fit=crop&w=700&q=80"},
        {"type": "sliding", "label": "Sliding", "width": 180, "image": "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=700&q=80"},
    ],
    "window": [
        {"type": "window_1", "label": "Window 1", "width": 90, "image": "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=700&q=80"},
        {"type": "window_2", "label": "Window 2", "width": 150, "image": "https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=700&q=80"},
        {"type": "window_3", "label": "Window 3", "width": 220, "image": "https://images.unsplash.com/photo-1600607688969-a5bfcd646154?auto=format&fit=crop&w=700&q=80"},
    ],
}

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

        .landing-background {{
            position: fixed;
            inset: 0;
            z-index: 0;
            overflow: hidden;
            background: #111711;
        }}

        .landing-bg-slide {{
            position: absolute;
            inset: 0;
            background-size: cover;
            background-position: center;
            opacity: 0;
            animation: landing-bg-fade 25s infinite;
        }}

        .landing-background::after {{
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(180deg, rgba(6, 14, 8, 0.35), rgba(6, 14, 8, 0.62)),
                linear-gradient(90deg, rgba(6, 14, 8, 0.52), rgba(6, 14, 8, 0.12));
        }}

        @keyframes landing-bg-fade {{
            0% {{
                opacity: 1;
            }}
            16% {{
                opacity: 1;
            }}
            24% {{
                opacity: 0;
            }}
            100% {{
                opacity: 0;
            }}
        }}

        .landing-shell {{
            position: relative;
            z-index: 1;
            min-height: 58vh;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            padding: 5rem 1rem 1rem 1rem;
        }}

        .landing-panel {{
            width: min(680px, 100%);
            text-align: left;
        }}

        .landing-title {{
            font-size: 3rem;
            font-weight: 800;
            line-height: 1.05;
            margin: 0 0 0.75rem 0;
            color: #ffffff;
            text-shadow: 0 2px 18px rgba(0, 0, 0, 0.28);
        }}

        .landing-brand-dark {{
            color: #ffffff;
        }}

        .landing-brand-green {{
            color: {BRAND_GREEN};
        }}

        .landing-kicker {{
            color: rgba(255, 255, 255, 0.82);
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: 0;
            margin-bottom: 0.55rem;
        }}

        .landing-subtitle {{
            font-size: 1.15rem;
            line-height: 1.55;
            margin: 0 0 1.4rem 0;
            color: rgba(255, 255, 255, 0.86);
            max-width: 620px;
        }}

        .landing-actions {{
            position: relative;
            z-index: 1;
            margin-top: -4rem;
            padding-bottom: 4rem;
        }}

        .landing-actions div.stButton > button {{
            min-height: 4.5rem;
            width: 100%;
            border-radius: 8px;
            border: 1px solid {BRAND_GREEN_DARK};
            background: {BRAND_GREEN};
            color: #ffffff;
            font-size: 1.05rem;
            font-weight: 750;
        }}

        .landing-actions div.stButton > button:hover {{
            background: {BRAND_GREEN_DARK};
            color: #ffffff;
            border-color: {BRAND_GREEN_DARK};
        }}

        div.stButton > button {{
            background: {BRAND_GREEN};
            color: #ffffff;
            border: 1px solid {BRAND_GREEN_DARK};
        }}

        div.stButton > button:hover {{
            background: {BRAND_GREEN_DARK};
            color: #ffffff;
            border-color: {BRAND_GREEN_DARK};
        }}

        @media (max-width: 760px) {{
            .landing-shell {{
                min-height: 58vh;
                padding-top: 4rem;
            }}

            .landing-title {{
                font-size: 2.1rem;
            }}

            .landing-actions {{
                margin-top: -2rem;
            }}
        }}

        .placeholder-panel {{
            border: 1px solid {theme["panel_border"]};
            background: {theme["panel_bg"]};
            border-radius: 8px;
            padding: 1.25rem;
            margin-top: 1rem;
        }}

        .room-form-note {{
            color: {theme["muted"]};
            font-size: 0.95rem;
            margin: 0.4rem 0 1rem 0;
        }}

        .room-summary {{
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
            margin: 0.75rem 0 1rem 0;
        }}

        .room-summary-item {{
            border: 1px solid {theme["panel_border"]};
            background: {theme["panel_bg"]};
            border-radius: 8px;
            padding: 0.65rem 0.8rem;
            color: {theme["text"]};
            font-weight: 700;
        }}

        .room-type-card {{
            border: 1px solid {theme["panel_border"]};
            background: {theme["panel_bg"]};
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 0.5rem;
        }}

        .room-type-image {{
            height: 120px;
            background-size: cover;
            background-position: center;
        }}

        .room-type-body {{
            padding: 0.75rem;
        }}

        .room-type-title {{
            color: {theme["text"]};
            font-size: 1rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }}

        .room-type-description {{
            color: {theme["muted"]};
            font-size: 0.86rem;
            line-height: 1.35;
            min-height: 2.35rem;
        }}

        .selected-room-label {{
            color: {BRAND_GREEN_DARK};
            font-size: 0.95rem;
            font-weight: 800;
            margin: 0 0 0.75rem 0;
        }}

        .furniture-list {{
            margin-top: 0.75rem;
        }}

        .furniture-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            color: {theme["text"]};
            border-bottom: 1px solid {theme["panel_border"]};
            padding: 0.45rem 0;
            font-size: 0.92rem;
        }}

        .opening-card {{
            border: 1px solid {theme["panel_border"]};
            background: {theme["panel_bg"]};
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 0.45rem;
        }}

        .opening-card-image {{
            height: 96px;
            background-size: cover;
            background-position: center;
        }}

        .opening-card-title {{
            color: {theme["text"]};
            font-size: 1rem;
            font-weight: 750;
            padding: 0.65rem 0.75rem;
        }}

        .opening-card-meta {{
            color: {theme["muted"]};
            font-size: 0.82rem;
            padding: 0 0.75rem 0.65rem 0.75rem;
        }}

        .opening-icon-card {{
            border: 1px solid {theme["panel_border"]};
            background: {theme["panel_bg"]};
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 0.4rem;
        }}

        .opening-icon-image {{
            height: 74px;
            background-size: cover;
            background-position: center;
        }}

        .opening-icon-title {{
            color: {theme["text"]};
            font-size: 0.9rem;
            font-weight: 800;
            padding: 0.5rem 0.6rem;
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


def plot_empty_room_grid(
    room_width_cm,
    room_depth_cm,
    cell_size,
    theme,
    objects=None,
    openings=None,
):
    fig_width = min(9, max(5, room_width_cm / 80))
    fig_height = min(7, max(4, room_depth_cm / 80))
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    fig.patch.set_facecolor(theme["panel_bg"])
    ax.set_facecolor(theme["room_bg"])
    ax.set_axisbelow(True)

    room_rect = Rectangle(
        (0, 0),
        room_width_cm,
        room_depth_cm,
        fill=False,
        linewidth=2.2,
        edgecolor=theme["text"],
        zorder=3,
    )
    ax.add_patch(room_rect)

    for opening in openings or []:
        side = opening["side"]
        position = opening["position"]
        width = opening["width"]
        if side in ("top", "bottom"):
            y = 0 if side == "top" else room_depth_cm
            x_values = [position, position + width]
            y_values = [y, y]
            text_x = position + width / 2
            text_y = y - 18 if side == "top" else y + 18
        else:
            x = 0 if side == "left" else room_width_cm
            x_values = [x, x]
            y_values = [position, position + width]
            text_x = x - 26 if side == "left" else x + 26
            text_y = position + width / 2

        opening_color = theme["text"] if opening["kind"] == "door" else "#4FB3D8"
        ax.plot(
            x_values,
            y_values,
            linewidth=8,
            color=theme["room_bg"],
            solid_capstyle="butt",
            zorder=5,
        )
        ax.plot(
            x_values,
            y_values,
            linewidth=4,
            color=opening_color,
            solid_capstyle="round",
            zorder=6,
        )
        if opening.get("label"):
            ax.text(
                text_x,
                text_y,
                opening["label"],
                ha="center",
                va="center",
                fontsize=7,
                fontweight="bold",
                color=opening_color,
                zorder=7,
            )

    for obj in objects or []:
        color = OBJECT_COLORS.get(obj["type"], theme["fallback_object"])
        rect = Rectangle(
            (obj["x"], obj["y"]),
            obj["width"],
            obj["depth"],
            fill=True,
            facecolor=color,
            edgecolor=theme["text"],
            linewidth=1.2,
            alpha=0.82,
            zorder=3,
        )
        ax.add_patch(rect)
        ax.text(
            obj["x"] + obj["width"] / 2,
            obj["y"] + obj["depth"] / 2,
            obj["label"],
            ha="center",
            va="center",
            fontsize=7,
            fontweight="bold",
            color=theme["plot_text"],
            zorder=4,
        )

    margin = 45
    ax.set_xlim(-margin, room_width_cm + margin)
    ax.set_ylim(-margin, room_depth_cm + margin)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.set_title("")
    ax.set_xlabel("x (cm)")
    ax.set_ylabel("y (cm)")

    ax.set_xticks(range(0, room_width_cm + 1, 50))
    ax.set_yticks(range(0, room_depth_cm + 1, 50))
    ax.set_xticks(range(0, room_width_cm + 1, cell_size), minor=True)
    ax.set_yticks(range(0, room_depth_cm + 1, cell_size), minor=True)
    ax.grid(which="minor", color=theme["grid"], linewidth=0.45, zorder=0)
    ax.grid(which="major", color=theme["panel_border"], linewidth=0.9, zorder=1)

    ax.tick_params(colors=theme["subtitle"], labelsize=8)
    ax.tick_params(which="minor", length=0)
    ax.title.set_color(theme["text"])
    ax.xaxis.label.set_color(theme["subtitle"])
    ax.yaxis.label.set_color(theme["subtitle"])
    for spine in ax.spines.values():
        spine.set_visible(False)

    return fig


def initialize_created_room_state():
    if "created_room_type" not in st.session_state:
        first_room_key = next(iter(ROOM_TYPES))
        st.session_state["created_room_type"] = first_room_key
        st.session_state["created_room_selected"] = False
        st.session_state["created_room_width_cm"] = ROOM_TYPES[first_room_key]["width_cm"]
        st.session_state["created_room_depth_cm"] = ROOM_TYPES[first_room_key]["depth_cm"]
        st.session_state["created_room_width_input"] = ROOM_TYPES[first_room_key]["width_cm"] / 100
        st.session_state["created_room_depth_input"] = ROOM_TYPES[first_room_key]["depth_cm"] / 100
        st.session_state["created_room_objects"] = []
        st.session_state["created_object_counter"] = 0
        st.session_state["created_room_door"] = None
        st.session_state["created_room_windows"] = []
        st.session_state["created_window_counter"] = 0
        st.session_state["created_opening_category"] = "door"
        st.session_state["created_opening_type"] = "single"


def select_created_room(room_key):
    room_data = ROOM_TYPES[room_key]
    st.session_state["created_room_type"] = room_key
    st.session_state["created_room_width_cm"] = room_data["width_cm"]
    st.session_state["created_room_depth_cm"] = room_data["depth_cm"]
    st.session_state["created_room_width_input"] = room_data["width_cm"] / 100
    st.session_state["created_room_depth_input"] = room_data["depth_cm"] / 100
    st.session_state["created_room_objects"] = []
    st.session_state["created_object_counter"] = 0
    st.session_state["created_room_door"] = None
    st.session_state["created_room_windows"] = []
    st.session_state["created_window_counter"] = 0
    st.session_state["created_opening_category"] = "door"
    st.session_state["created_opening_type"] = "single"
    st.session_state["created_room_selected"] = True
    st.rerun()


def get_opening_side_length(side, room_width_cm, room_depth_cm):
    if side in ("top", "bottom"):
        return room_width_cm
    return room_depth_cm


def clamp_opening(opening, room_width_cm, room_depth_cm):
    side_length = get_opening_side_length(opening["side"], room_width_cm, room_depth_cm)
    opening["width"] = min(max(opening["width"], CELL_SIZE), side_length)
    opening["position"] = min(max(opening["position"], 0), max(side_length - opening["width"], 0))
    return opening


def clamp_created_room_openings():
    room_width_cm = st.session_state["created_room_width_cm"]
    room_depth_cm = st.session_state["created_room_depth_cm"]

    if st.session_state.get("created_room_door"):
        st.session_state["created_room_door"] = clamp_opening(
            st.session_state["created_room_door"],
            room_width_cm,
            room_depth_cm,
        )

    st.session_state["created_room_windows"] = [
        clamp_opening(window, room_width_cm, room_depth_cm)
        for window in st.session_state.get("created_room_windows", [])
    ]


def clamp_created_room_objects():
    room_width_cm = st.session_state["created_room_width_cm"]
    room_depth_cm = st.session_state["created_room_depth_cm"]
    for obj in st.session_state.get("created_room_objects", []):
        obj["x"] = min(max(int(obj.get("x", 0)), 0), max(room_width_cm - obj["width"], 0))
        obj["y"] = min(max(int(obj.get("y", 0)), 0), max(room_depth_cm - obj["depth"], 0))


def update_created_room_object_dimensions(object_id, width_m, depth_m):
    width_cm = max(CELL_SIZE, int(round(width_m * 100 / CELL_SIZE) * CELL_SIZE))
    depth_cm = max(CELL_SIZE, int(round(depth_m * 100 / CELL_SIZE) * CELL_SIZE))

    for obj in st.session_state.get("created_room_objects", []):
        if obj["id"] != object_id:
            continue

        orientation = obj.get("orientation", 0)
        obj["width"] = width_cm
        obj["depth"] = depth_cm
        if orientation in (90, 270):
            obj["base_width"] = depth_cm
            obj["base_depth"] = width_cm
        else:
            obj["base_width"] = width_cm
            obj["base_depth"] = depth_cm
        break

    clamp_created_room_objects()
    st.rerun()


def update_created_room_object_dimensions_from_inputs(object_id, width_key, depth_key):
    update_created_room_object_dimensions(
        object_id,
        st.session_state[width_key],
        st.session_state[depth_key],
    )


def build_created_room_openings():
    openings = []
    door = st.session_state.get("created_room_door")
    if door:
        openings.append(door)
    openings.extend(st.session_state.get("created_room_windows", []))
    return openings


def opening_to_layout_door(opening):
    if not opening:
        return None

    if opening["side"] in ("left", "right"):
        return {
            "x": 0 if opening["side"] == "left" else st.session_state["created_room_width_cm"],
            "y": opening["position"],
            "width": opening["width"],
            "orientation": "vertical",
        }

    return {
        "x": opening["position"],
        "y": 0 if opening["side"] == "top" else st.session_state["created_room_depth_cm"],
        "width": opening["width"],
        "orientation": "horizontal",
    }


def get_default_created_room_entry():
    room_width = st.session_state["created_room_width_cm"]
    room_depth = st.session_state["created_room_depth_cm"]
    entry_width = min(90, max(CELL_SIZE, room_width))
    entry_x = min(50, max(room_width - entry_width, 0))
    return {
        "x": entry_x,
        "y": room_depth,
        "width": entry_width,
        "orientation": "horizontal",
    }


def get_default_created_room_entry_opening():
    room_width = st.session_state["created_room_width_cm"]
    entry_width = min(90, max(CELL_SIZE, room_width))
    return {
        "id": "created_default_entry",
        "kind": "door",
        "type": "entry",
        "label": "",
        "side": "bottom",
        "position": min(50, max(room_width - entry_width, 0)),
        "width": entry_width,
    }


def build_created_room_layout():
    return {
        "room": {
            "width": st.session_state["created_room_width_cm"],
            "depth": st.session_state["created_room_depth_cm"],
        },
        "door": get_default_created_room_entry(),
        "objects": copy.deepcopy(st.session_state.get("created_room_objects", [])),
    }


def build_created_room_score_layout():
    layout_data = build_created_room_layout()

    required_ids = {
        "fridge": "fridge_1",
        "sink": "sink_1",
        "stove": "stove_1",
    }
    optional_ids = {
        "table": "table_1",
    }
    score_ids = {**required_ids, **optional_ids}
    used_required_types = set()
    for obj in layout_data["objects"]:
        object_type = obj.get("type")
        if object_type in score_ids and object_type not in used_required_types:
            obj["id"] = score_ids[object_type]
            used_required_types.add(object_type)

    return layout_data, sorted(set(required_ids) - used_required_types)


def render_opening_layout(room_width_cm, room_depth_cm, openings, theme):
    return OPENING_LAYOUT(
        room={"width": room_width_cm, "depth": room_depth_cm},
        openings=openings,
        theme=theme,
        default=None,
        key="created_room_opening_layout",
    )


def update_created_room_opening(opening_id, side, position):
    door = st.session_state.get("created_room_door")
    if door and door["id"] == opening_id:
        door["side"] = side
        door["position"] = position
        clamp_created_room_openings()
        return True

    for window in st.session_state.get("created_room_windows", []):
        if window["id"] == opening_id:
            window["side"] = side
            window["position"] = position
            clamp_created_room_openings()
            return True

    return False


def select_opening_category(category):
    st.session_state["created_opening_category"] = category
    st.session_state["created_opening_type"] = OPENING_TYPES[category][0]["type"]
    st.rerun()


def select_opening_type(opening_type):
    st.session_state["created_opening_type"] = opening_type
    st.rerun()


def get_selected_opening_type():
    category = st.session_state.get("created_opening_category", "door")
    selected_type = st.session_state.get("created_opening_type", OPENING_TYPES[category][0]["type"])
    for item in OPENING_TYPES[category]:
        if item["type"] == selected_type:
            return item
    return OPENING_TYPES[category][0]


def add_created_room_object(item):
    objects = st.session_state.setdefault("created_room_objects", [])
    room_width = st.session_state["created_room_width_cm"]
    room_depth = st.session_state["created_room_depth_cm"]
    st.session_state["created_object_counter"] = st.session_state.get("created_object_counter", 0) + 1
    index = st.session_state["created_object_counter"]
    max_x = max(room_width - item["width"], 0)
    max_y = max(room_depth - item["depth"], 0)
    x = min(((index - 1) % 5) * 40, max_x)
    y = min(((index - 1) // 5) * 40, max_y)
    objects.append(
        {
            "id": f"created_{item['type']}_{index}",
            "type": item["type"],
            "label": item["label"],
            "x": x,
            "y": y,
            "width": item["width"],
            "depth": item["depth"],
            "orientation": 0,
            "access_side": "all" if item["type"] == "table" else "front",
        }
    )
    st.rerun()


def remove_created_room_object(object_id):
    st.session_state["created_room_objects"] = [
        obj for obj in st.session_state.get("created_room_objects", [])
        if obj["id"] != object_id
    ]
    st.rerun()


def update_object_position(layout_data, object_id, new_x, new_y):
    obj = get_object_by_id(layout_data, object_id)
    if obj is not None:
        obj["x"] = new_x
        obj["y"] = new_y


def ensure_base_dimensions(obj):
    obj.setdefault("orientation", 0)
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


def render_draggable_layout(layout_data, editable_ids, theme, key="candidate_drag_layout"):
    return DRAGGABLE_LAYOUT(
        layout_data=layout_data,
        editable_ids=editable_ids,
        object_colors=OBJECT_COLORS,
        theme=theme,
        default=None,
        key=key,
    )


def apply_drag_event_to_layout(layout_data, editable_ids, drag_event):
    updated_layout = copy.deepcopy(layout_data)
    initialize_object_dimensions(updated_layout)

    for object_id, orientation in drag_event.get("orientations", {}).items():
        if object_id not in editable_ids:
            continue
        obj = get_object_by_id(updated_layout, object_id)
        if obj is None:
            continue
        rotate_object(obj, int(orientation))
        obj["x"] = min(obj["x"], max(updated_layout["room"]["width"] - obj["width"], 0))
        obj["y"] = min(obj["y"], max(updated_layout["room"]["depth"] - obj["depth"], 0))

    for object_id, position in drag_event.get("positions", {}).items():
        if object_id not in editable_ids:
            continue
        obj = get_object_by_id(updated_layout, object_id)
        if obj is None:
            continue

        max_x = max(updated_layout["room"]["width"] - obj["width"], 0)
        max_y = max(updated_layout["room"]["depth"] - obj["depth"], 0)
        obj["x"] = min(max(int(position["x"]), 0), max_x)
        obj["y"] = min(max(int(position["y"]), 0), max_y)

    return updated_layout




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


def build_work_triangle_rows(result):
    triangle = result.get("work_triangle")
    if not triangle:
        return [
            {
                "Element": "-",
                "Distance": "-",
                "Ideal range": "-",
                "Score": "-",
                "Effect": "work triangle details unavailable",
            }
        ]

    rows = []
    for leg in triangle["legs"]:
        rows.append(
            {
                "Element": f"{leg['from']} -> {leg['to']}",
                "Distance": format_cm(leg["length_cm"]),
                "Ideal range": f"{leg['ideal_min_cm']:.0f}-{leg['ideal_max_cm']:.0f} cm",
                "Score": f"{leg['score']:.4f}",
                "Effect": describe_workflow_path(leg),
            }
        )

    rows.append(
        {
            "Element": "triangle total",
            "Distance": format_cm(triangle["total_cm"]),
            "Ideal range": (
                f"{triangle['total_ideal_min_cm']:.0f}-"
                f"{triangle['total_ideal_max_cm']:.0f} cm"
            ),
            "Score": f"{triangle['total_score']:.4f}",
            "Effect": describe_workflow_path(
                {
                    "length_cm": triangle["total_cm"],
                    "ideal_min_cm": triangle["total_ideal_min_cm"],
                    "ideal_max_cm": triangle["total_ideal_max_cm"],
                }
            ),
        }
    )

    rows.append(
        {
            "Element": "triangle score",
            "Distance": "-",
            "Ideal range": "120-270 cm per leg, 400-790 cm total",
            "Score": f"{triangle['triangle_score']:.4f}",
            "Effect": "included in workflow score",
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

    triangle = result.get("work_triangle")
    if triangle:
        for leg in triangle["legs"]:
            effect = describe_workflow_path(leg)
            if leg["score"] < 0.75:
                if effect == "too far":
                    suggestion = "Move these work centers closer or remove detours between them."
                elif effect == "too close":
                    suggestion = "Increase the working distance between these two centers."
                elif effect == "blocked path":
                    suggestion = "Clear the path so the triangle leg is reachable."
                else:
                    suggestion = "Review this side of the work triangle."

                suggestions.append(
                    {
                        "Area": "Work triangle",
                        "Issue": f"{leg['from']} -> {leg['to']} is {effect}",
                        "Score": f"{leg['score']:.4f}",
                        "Suggestion": suggestion,
                    }
                )

        total_effect = describe_workflow_path(
            {
                "length_cm": triangle["total_cm"],
                "ideal_min_cm": triangle["total_ideal_min_cm"],
                "ideal_max_cm": triangle["total_ideal_max_cm"],
            }
        )
        if triangle["total_score"] < 0.75:
            suggestions.append(
                {
                    "Area": "Work triangle",
                    "Issue": f"Triangle total is {total_effect}",
                    "Score": f"{triangle['total_score']:.4f}",
                    "Suggestion": "Keep the fridge, sink, and stove triangle within the recommended total travel distance.",
                }
            )

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


def set_app_view(view):
    st.session_state["app_view"] = view
    st.rerun()


def build_landing_background():
    slides = "".join(
        (
            '<div class="landing-bg-slide" '
            f'style="background-image:url({image_url}); animation-delay:{index * 5}s;">'
            "</div>"
        )
        for index, image_url in enumerate(INTERIOR_IMAGES)
    )

    return f'<div class="landing-background">{slides}</div>'


def render_landing_page():
    background_markup = build_landing_background()

    st.markdown(
        f"""
        {background_markup}
        <div class="landing-shell">
            <div class="landing-panel">
                <div class="landing-kicker">MVP decision support for interior layouts</div>
                <div class="landing-title">
                    <span class="landing-brand-dark">HU</span><span class="landing-brand-green">Bspace</span>
                </div>
                <p class="landing-subtitle">
                    Explore, evaluate, and compare room configurations with
                    measurable support for layout decisions.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="landing-actions">', unsafe_allow_html=True)
    action_col_1, action_col_2, action_col_3 = st.columns(3)

    with action_col_1:
        if st.button("create new room", use_container_width=True):
            set_app_view("create_room")

    with action_col_2:
        if st.button("upload room", use_container_width=True):
            set_app_view("upload_room")

    with action_col_3:
        if st.button("compare room", use_container_width=True):
            set_app_view("compare_room")

    st.markdown("</div>", unsafe_allow_html=True)


def render_placeholder_page(title, description):
    if st.button("Back to home"):
        set_app_view("landing")

    st.markdown(
        f"""
        <div class="app-header">
            <div class="app-title">{title}</div>
            <p class="app-subtitle">{description}</p>
        </div>
        <div class="placeholder-panel">
            This section is ready for the next implementation step.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_create_room_page(theme):
    initialize_created_room_state()

    if st.button("Back to home"):
        set_app_view("landing")

    st.markdown(
        """
        <div class="app-header">
            <div class="app-title">Create new room</div>
            <p class="app-subtitle">
                Select a room type, then define the room dimensions and build a
                10 cm decision grid for the MVP.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.get("created_room_selected", False):
        st.subheader("Choose room type")
        room_cards = st.columns(3)
        for index, (room_key, room_data) in enumerate(ROOM_TYPES.items()):
            with room_cards[index % 3]:
                st.markdown(
                    f"""
                    <div class="room-type-card">
                        <div class="room-type-image" style="background-image:url({room_data['image']});"></div>
                        <div class="room-type-body">
                            <div class="room-type-title">{room_data['label']}</div>
                            <div class="room-type-description">{room_data['description']}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Select", key=f"select_room_{room_key}", use_container_width=True):
                    select_created_room(room_key)
        return

    selected_room_key = st.session_state["created_room_type"]
    selected_room = ROOM_TYPES[selected_room_key]

    menu_col, workspace_col = st.columns([1, 2])

    with menu_col:
        if st.button("Change room type", use_container_width=True):
            st.session_state["created_room_selected"] = False
            st.rerun()

        st.subheader("Room dimensions")
        st.markdown(
            f'<p class="selected-room-label">Selected room: {selected_room["label"]}</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="room-form-note">Use 0.10 m increments: every value maps to 10 cm cells.</p>',
            unsafe_allow_html=True,
        )

        width_m = st.number_input(
            "Room width (m)",
            min_value=1.0,
            max_value=20.0,
            value=float(st.session_state["created_room_width_cm"] / 100),
            step=0.1,
            format="%.2f",
            key="created_room_width_input",
        )
        depth_m = st.number_input(
            "Room depth (m)",
            min_value=1.0,
            max_value=20.0,
            value=float(st.session_state["created_room_depth_cm"] / 100),
            step=0.1,
            format="%.2f",
            key="created_room_depth_input",
        )

        if st.button("Update dimensions", use_container_width=True):
            st.session_state["created_room_width_cm"] = int(round(width_m * 100 / CELL_SIZE) * CELL_SIZE)
            st.session_state["created_room_depth_cm"] = int(round(depth_m * 100 / CELL_SIZE) * CELL_SIZE)
            clamp_created_room_openings()
            clamp_created_room_objects()
            st.rerun()

        room_width_cm = st.session_state["created_room_width_cm"]
        room_depth_cm = st.session_state["created_room_depth_cm"]

        st.subheader("Elements")
        st.caption("Add items, then move them in the editor. Double click an item to rotate it.")
        furniture_items = FURNITURE_CATALOG.get(selected_room_key, [])
        item_cols = st.columns(2)
        for index, item in enumerate(furniture_items):
            with item_cols[index % 2]:
                if st.button(
                    f"+ {item['label']}",
                    key=f"add_created_object_{selected_room_key}_{item['type']}_{index}",
                    use_container_width=True,
                ):
                    add_created_room_object(item)

        objects = st.session_state.get("created_room_objects", [])
        if objects:
            st.markdown('<div class="furniture-list">', unsafe_allow_html=True)
            for obj in objects:
                item_col_1, item_col_2, item_col_3, item_col_4 = st.columns([1.15, 0.72, 0.72, 0.8])
                width_key = f"inline_width_{obj['id']}_{obj.get('orientation', 0)}"
                depth_key = f"inline_depth_{obj['id']}_{obj.get('orientation', 0)}"
                with item_col_1:
                    st.markdown(
                        f"""
                        <div class="furniture-item">
                            <span>{obj['label']}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with item_col_2:
                    st.number_input(
                        "W",
                        min_value=0.1,
                        max_value=max(0.1, room_width_cm / 100),
                        value=float(obj["width"] / 100),
                        step=0.1,
                        format="%.2f",
                        key=width_key,
                        label_visibility="collapsed",
                        on_change=update_created_room_object_dimensions_from_inputs,
                        args=(obj["id"], width_key, depth_key),
                    )
                with item_col_3:
                    st.number_input(
                        "D",
                        min_value=0.1,
                        max_value=max(0.1, room_depth_cm / 100),
                        value=float(obj["depth"] / 100),
                        step=0.1,
                        format="%.2f",
                        key=depth_key,
                        label_visibility="collapsed",
                        on_change=update_created_room_object_dimensions_from_inputs,
                        args=(obj["id"], width_key, depth_key),
                    )
                with item_col_4:
                    if st.button("Remove", key=f"remove_created_object_{obj['id']}", use_container_width=True):
                        remove_created_room_object(obj["id"])
            st.markdown("</div>", unsafe_allow_html=True)

    room_width_cm = st.session_state["created_room_width_cm"]
    room_depth_cm = st.session_state["created_room_depth_cm"]
    objects = st.session_state.get("created_room_objects", [])
    openings = [get_default_created_room_entry_opening()]

    with workspace_col:
        if objects:
            created_layout = build_created_room_layout()
            initialize_object_dimensions(created_layout)
            editable_ids = [obj["id"] for obj in created_layout["objects"]]
            drag_event = render_draggable_layout(
                created_layout,
                editable_ids,
                theme,
                key="created_room_drag_layout",
            )
            if drag_event:
                event_id = drag_event.get("event_id")
                if event_id != st.session_state.get("last_created_drag_event_id"):
                    updated_layout = apply_drag_event_to_layout(created_layout, editable_ids, drag_event)
                    st.session_state["created_room_objects"] = copy.deepcopy(updated_layout["objects"])
                    st.session_state["last_created_drag_event_id"] = event_id
                    st.rerun()
        else:
            fig = plot_empty_room_grid(room_width_cm, room_depth_cm, CELL_SIZE, theme, objects, openings)
            st.pyplot(fig)

        if objects:
            st.subheader("Layout scores")
            if not layout_is_valid(objects):
                st.error("Invalid layout: some objects overlap. Move or resize them before reading the scores.")
            else:
                score_layout, missing_types = build_created_room_score_layout()
                if missing_types:
                    missing_labels = ", ".join(missing_types)
                    st.info(
                        "Add fridge, sink, and stove to unlock workflow scoring. "
                        f"Missing: {missing_labels}."
                    )
                else:
                    try:
                        result_created = analyze_layout(score_layout)
                    except Exception as exc:
                        st.warning(f"Scores are not available for this layout yet: {exc}")
                    else:
                        render_score_panel("Created layout", result_created)
                        with st.expander("Suggestions", expanded=True):
                            st.table(build_suggestion_rows(result_created))
                        detail_col_1, detail_col_2 = st.columns(2)
                        with detail_col_1:
                            with st.expander("Workflow details", expanded=False):
                                st.table(build_workflow_rows(result_created))
                            with st.expander("Work triangle details", expanded=False):
                                st.table(build_work_triangle_rows(result_created))
                        with detail_col_2:
                            with st.expander("Space details", expanded=False):
                                st.table(build_space_rows(result_created))


theme = resolve_theme()
apply_custom_style(theme)

if "app_view" not in st.session_state:
    st.session_state["app_view"] = "landing"

if st.session_state["app_view"] == "landing":
    render_landing_page()
    st.stop()

if st.session_state["app_view"] == "create_room":
    render_create_room_page(theme)
    st.stop()

if st.session_state["app_view"] == "upload_room":
    render_placeholder_page(
        "Upload room",
        "Import an existing room layout and prepare it for analysis.",
    )
    st.stop()

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
        updated_candidate_layout = apply_drag_event_to_layout(
            st.session_state["candidate_layout"],
            editable_object_ids,
            drag_event,
        )
        st.session_state["candidate_layout"] = copy.deepcopy(updated_candidate_layout)
        st.session_state["last_drag_event_id"] = event_id
        st.rerun()

if st.sidebar.button("Back to home"):
    set_app_view("landing")

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

    if "workflow_paths" not in result_candidate or "work_triangle" not in result_candidate:
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
        with st.expander("Baseline work triangle details", expanded=False):
            st.table(build_work_triangle_rows(result_base))
        with st.expander("Baseline space details", expanded=False):
            st.table(build_space_rows(result_base))

    with detail_col_2:
        with st.expander("Candidate workflow details", expanded=True):
            st.table(build_workflow_rows(result_candidate))
        with st.expander("Candidate work triangle details", expanded=True):
            st.table(build_work_triangle_rows(result_candidate))
        with st.expander("Candidate space details", expanded=False):
            st.table(build_space_rows(result_candidate))

    st.subheader("Comparison Summary")
    st.write(f"**Space winner:** {comparison['space_winner']}")
    st.write(f"**Workflow winner:** {comparison['workflow_winner']}")
    st.write(f"**Recommendation:** {comparison['recommendation']}")
