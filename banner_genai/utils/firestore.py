"""Utilities to interact with Firestore."""

import json
import os

from google.cloud import firestore

import constants as C
from config import settings


def init_document_store(config_file_path: str | None = None) -> None:
    """Inits contents in Firestore as the backend document storage.

    The initial contents include configurations for both visual segments and banner
    template layouts.

    Args:
        config_file_path: Path to the configuration JSON file.
    """
    if config_file_path is None:
        config_file_path = os.path.join(settings.local_artefacts_dir, "config.json")

    with open(config_file_path, "r") as f:
        config_data = json.load(f)

    db = firestore.Client(project=settings.gcp_project, database=settings.firestore_id)

    banner_template = config_data.get(C.DocKey.TEMPLATE, [])
    collection_ref = db.collection(C.DocKey.TEMPLATE)
    for banner in banner_template:
        doc_ref = collection_ref.document(banner["bannertemplate"])
        doc_ref.set(banner)

    visual_segments = config_data.get(C.DocKey.SEGMENT, [])
    collection_ref = db.collection(C.DocKey.SEGMENT)
    for segment in visual_segments:
        doc_ref = collection_ref.document(segment["visualsegment"])
        doc_ref.set(segment)


def cleanup_document_store() -> None:
    """Removes all documents from the backend Firestore."""
    db = firestore.Client(project=settings.gcp_project, database=settings.firestore_id)
    collections_to_nuke = [C.DocKey.SEGMENT, C.DocKey.TEMPLATE]
    for collection in collections_to_nuke:
        collection_ref = db.collection(collection)
        if collection_ref.get():
            docs = collection_ref.stream()
            for doc in docs:
                doc.reference.delete()


# FIXME: Do we need this at all?
def get_visual_segments_from_db(db: firestore.Client) -> list[dict]:
    # This essentially fetches all documents to memory.
    collection_ref = db.collection(C.DocKey.SEGMENT)
    docs = collection_ref.stream()
    visual_segments = []
    for doc in docs:
        visual_segments.append(doc.to_dict())

    return visual_segments


def fetch_visual_segment_names(db: firestore.Client) -> list[str]:
    """Fetches all segment names from Firestore.

    Args:
        db: Firestore connection client.

    Returns:
        Segment names.
    """
    collection_ref = db.collection(C.DocKey.SEGMENT)
    return [doc.id for doc in collection_ref.stream()]


def get_visual_segment_config_by_name(db: firestore.Client, name: str) -> dict:
    """Fetches a single segment configuration given its name.

    Args:
        db: Firestore connection client.
        name: Segment name.

    Returns:
        Segment attribute document.
    """
    collection_ref = db.collection(C.DocKey.SEGMENT)
    query_ref = collection_ref.where(
        filter=firestore.FieldFilter("visualsegment", "==", name)
    )
    docs = [d.to_dict() for d in query_ref.stream()]
    return docs[0]  # return only the first match


def add_or_update_visual_segment(db: firestore.Client, segment_data: dict):
    segment_name = segment_data["visualsegment"]
    collection_ref = db.collection(C.DocKey.SEGMENT)
    doc_ref = collection_ref.document(segment_name)

    if doc_ref.get().exists:
        doc_ref.update(segment_data)
        print(f"Visual segment '{segment_name}' updated successfully.")
        return "updated"
    else:
        doc_ref.set(segment_data)
        print(f"Visual segment '{segment_name}' created successfully.")
        return "created"


# FIXME: Do we need this function at all?
def get_bannertemplate_from_db(db: firestore.Client) -> list[dict]:
    """Fetches all template configurations at once."""

    collection_banner_template = db.collection("banner_template")
    collection_ref = collection_banner_template
    docs = collection_ref.stream()

    banner_template = []
    for doc in docs:
        banner_template.append(doc.to_dict())

    return banner_template


def get_bannertemplate_config_by_name(db: firestore.Client, name: str) -> dict:
    """Fetches a single template configuration given its name.

    Args:
        db: Firestore connection client.
        name: Template name.

    Returns:
        Template document.
    """
    collection_ref = db.collection("banner_template")
    query_ref = collection_ref.where(
        filter=firestore.FieldFilter("bannertemplate", "==", name)
    )
    docs = [d.to_dict() for d in query_ref.stream()]
    return docs[0]  # return only the first match


def get_template_configuration(db: firestore.Client, template_name: str):
    # The configuration has bounding box format not compatible with the annotator.
    # So we need to convert its format.
    existing_config = get_bannertemplate_config_by_name(db, template_name)

    del existing_config["bannertemplate"]

    # FIXME: Colors of bounding boxes. Why not set in the template document as well?
    label_color_map = {
        "logo_position": (66, 133, 244),
        "graphic1_position": (24, 90, 188),
        "graphic2_position": (24, 90, 188),
        "actor_position": (52, 168, 83),
        "text_header1_position": (60, 64, 67),
        "text_header2_position": (60, 64, 67),
        "text_details_position": (95, 99, 104),
        "text_highlight1_position": (32, 33, 36),
        "graphic_highlight2_position": (24, 90, 188),
        "text_highlight3_position": (32, 33, 36),
        "text_tagline_position": (128, 134, 139),
        "text_action_position": (251, 188, 4),
    }

    output_list = []

    for label, position_data in existing_config.items():
        if label != "background_size":
            x = position_data["x"]
            y = position_data["y"]
            width = position_data["width"]
            height = position_data["height"]

            xmax = x + width
            ymax = y + height

            # TODO: Put color directly from the source document.
            #       However, The source code suggests the format should be a string like 'rgb(1, 1, 1)'...
            #       And the docstr suggests a tuple. Here we use a list. And it works...
            _color = label_color_map.get(label, (255, 255, 255))
            color = position_data.get("color", _color)

            output_dict = {
                "label": label,
                "xmin": x,
                "ymin": y,
                "xmax": xmax,
                "ymax": ymax,
                "color": color,
            }

            output_list.append(output_dict)

    return output_list


def add_or_update_bannertemplate(db: firestore.Client, template_data: dict) -> str:
    collection_ref = db.collection(C.DocKey.TEMPLATE)
    template_key = template_data["bannertemplate"]
    doc_ref = collection_ref.document(template_key)

    if doc_ref.get().exists:
        doc_ref.update(template_data)
        print(f"Banner template '{template_key}' updated successfully.")
        return "updated"
    else:
        doc_ref.set(template_data)
        print(f"Banner template '{template_key}' created successfully.")
        return "created"


def get_bannertemplate_list(db: firestore.Client) -> list[str]:
    return [template["bannertemplate"] for template in get_bannertemplate_from_db(db)]
