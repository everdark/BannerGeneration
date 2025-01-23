from enum import Enum


# FIXME: Make sure the system fonts are available on deployed runtime.
#        To install liberation fonts on macos:
#           brew install --cask font-liberation
class Font(str, Enum):
    sans_bold = "LiberationSans-Bold.ttf"
    sans_regular = "LiberationSans-Regular.ttf"
    sans_narrow_bold = "LiberationSansNarrow-Bold.ttf"
    mono_italic = "LiberationMono-Italic"
    mono_bold = "LiberationMono-Bold.ttf"


class ImageModel(str, Enum):
    """Existing image model from Google Gemini.

    https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/imagen-api
    """

    IMAGEN_3_FAST = "imagen-3.0-fast-generate-001"
    IMAGEN_3 = "imagen-3.0-generate-001"


class BlockName(str, Enum):
    """Gradio block (tab) name."""

    ABOUT = "About"
    IMAGE = "Demo Asset Library"
    CREATE = "Demo Asset Creation"
    PREPROCESS = "Demo Asset Preprocessing"
    TEMPLATE = "Demo Banner Template"
    BANNER = "Demo Banner Generation"


class DocKey(str, Enum):
    """Document collection keys for Firestore."""

    TEMPLATE = "banner_template"
    SEGMENT = "visuals_segment_clusters"


class ElementID(str, Enum):
    """HTML element ID."""

    SEGMENT_INPUTS = "segment-inputs"
    SEGMENT_INPUTS_EXT = "segment-inputs-extra"
    SEGMENT_DROPDOWN = "segment-dropdown"
