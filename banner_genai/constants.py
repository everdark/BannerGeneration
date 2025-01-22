from enum import Enum


class BlockName(str, Enum):
    """Gradio block (tab) name."""

    ABOUT = "About"
    IMAGE = "Demo Asset Library"
    CREATE = "Demo Asset Creation"
    PREPROCESS = "Demo Asset Preprocessing"
    TEMPLATE = "Demo Banner Template"
    BANNER = "Demo Banner Generation"


class DocKey(str, Enum):
    """Document keys for Firestore."""

    TEMPLATE = "banner_template"
    SEGMENT = "visuals_segment_clusters"


class ElementID(str, Enum):
    """HTML element ID."""

    SEGMENT_INPUTS = "segment-inputs"
    SEGMENT_INPUTS_EXT = "segment-inputs-extra"
    SEGMENT_DROPDOWN = "segment-dropdown"
