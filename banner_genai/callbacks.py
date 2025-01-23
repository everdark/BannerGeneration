"""Callback functions for event listeners."""

import base64
import datetime
import io
import os
import shutil
from string import ascii_letters

import gradio as gr
import numpy as np
from gradio_image_annotation import image_annotator
from PIL import Image, ImageDraw, ImageFont

import constants as C
from config import settings
from database import db
from model import SegmentProfile
from utils.firestore import (
    add_or_update_bannertemplate,
    add_or_update_visual_segment,
    fetch_visual_segment_names,
    get_bannertemplate_config_by_name,
    get_template_configuration,
    get_visual_segment_config_by_name,
)
from utils.imagen import (
    generate_imagen_outputs,
    remove_background,
    rewrite_prompt,
)
from utils.io import (
    find_files_with_prefix,
    get_filepath_in_folder_nested,
)


def _get_image_files(dir: str):
    image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
    images = [
        f for f in os.listdir(dir) if os.path.splitext(f)[1].lower() in image_extensions
    ]
    return images


def _create_thumbnail(image_path, size=(200, 200)):
    with Image.open(image_path) as img:
        img.thumbnail(
            size, Image.Resampling.LANCZOS
        )  # use a high-quality resampling filter
        return np.array(img)


def _update_thumbnails(selected_folder):
    image_files = _get_image_files(selected_folder)
    thumbnails = [
        _create_thumbnail(os.path.join(selected_folder, img)) for img in image_files
    ]
    imagepath = [(os.path.join(selected_folder, img)) for img in image_files]
    return thumbnails, imagepath


def display_image(evt: gr.SelectData):
    global gallery_dirname_list
    print(f"all_thumbnails positional data {gallery_dirname_list[evt.index]}")
    return Image.open(gallery_dirname_list[evt.index])


def select_folder(selected_files):
    global gallery_dirname_list
    print(f"Selection - {selected_files}")

    if selected_files:
        dirnames = []
        for file_path in selected_files:
            if os.path.isfile(file_path):
                dirname = os.path.dirname(file_path)
            else:
                dirname = file_path
            dirnames.append(dirname)

        # Get unique dirnames
        unique_dirnames = list(set(dirnames))

        all_thumbnails = []
        gallery_dirname_list = []  # Reset gallery_dirname_list
        for dirname in unique_dirnames:
            thumbnails, imagepath = _update_thumbnails(
                dirname
            )  # Get thumbnails for the current dirname
            all_thumbnails.extend(thumbnails)
            gallery_dirname_list.extend(imagepath)  # Add imagepath for each thumbnail

        return all_thumbnails, None  # Return only the list of thumbnails
    return None, None  # Return None if no files are selected


def update_segment_config(name: str):
    """Updates frontend inputs for a visual segment.

    Args:
        name: Name of a visual segment.

    Returns:
       Values of all segment attributes and the selected name itself for UI updates.
    """
    global db

    config = get_visual_segment_config_by_name(db, name)
    profile = SegmentProfile(**config)

    return tuple(profile.model_dump().values())


def create_new_segment(
    age: str,
    background: str,
    clothing: str,
    photography: str,
    subject: str,
    theme: str,
    name: str,
) -> tuple[str, gr.Dropdown]:
    """Creates a new visual segment configuration saving to Firestore.

    Args:
        All the segment attributes and the segment name.

    Returns:
        Updated selected segment state and the segment dropdown.
    """
    global db

    if (not name) or name == "":
        raise gr.Error(f"Visual segment is empty!", duration=3)

    existing_segments = fetch_visual_segment_names(db)
    if name in existing_segments:
        raise gr.Error(f"Visual segment '{name}' already exists!", duration=3)

    new_profile = SegmentProfile(
        age=age,
        background=background,
        clothing=clothing,
        photography=photography,
        subject=subject,
        theme=theme,
        visualsegment=name,
    )
    add_or_update_visual_segment(db, new_profile.model_dump())
    gr.Info(f"New segment '{name}' saved!", duration=5)

    updated_segments = fetch_visual_segment_names(db)

    return name, gr.Dropdown(choices=updated_segments)


def _generate_image_filename(directory, image_count):
    now = datetime.datetime.now()
    datetime_str = now.strftime("%d%m%H%M%S")
    filename = f"{directory}_{image_count}_{datetime_str}.png"
    return filename


def generate_assets(
    subject,
    age,
    clothing,
    theme,
    background,
    photography,
    imagecount,
    aspectratio,
    model,
    selected_visual_segment,
):
    """Generates images given visual segment attributes."""

    # Show a "processing" state while generating images
    yield (
        [],
        gr.update(value="Processing...", interactive=False),
        None,
    )

    segment_profile = SegmentProfile(
        age=age,
        background=background,
        clothing=clothing,
        photography=photography,
        subject=subject,
        theme=theme,
        visualsegment=selected_visual_segment,
    )

    print(f"User Input : {segment_profile.prompt()}")

    imagen_prompt = rewrite_prompt(segment_profile)

    print(f"Generated prompt:")
    print(imagen_prompt)

    image_list = generate_imagen_outputs(imagen_prompt, imagecount, aspectratio, model)

    # Save in temp folder
    LOCAL_TEMP_DIR = "/tmp"
    image_file_dir = os.path.join(LOCAL_TEMP_DIR, selected_visual_segment)
    print(
        f"Retrieved {len(image_list)} images to be saved in in image_file_dir - {image_file_dir}"
    )

    if os.path.exists(image_file_dir):
        shutil.rmtree(image_file_dir)  # Delete the existing directory and its contents
    os.makedirs(image_file_dir)  # Recreate the directory

    # Convert GeneratedImage object
    processed_images = []
    image_count = 1
    for generated_image in image_list:
        generated_image_data = base64.b64decode(generated_image._as_base64_string())
        pil_image = Image.open(io.BytesIO(generated_image_data))
        pil_file = os.path.join(
            image_file_dir,
            _generate_image_filename(selected_visual_segment, image_count),
        )
        pil_image.save(os.path.join(pil_file), "PNG")
        print(f"Saved image {image_count} @ {pil_file}")
        processed_images.append(pil_image)  # Add the PIL Image to the list
        image_count += 1

    yield (
        processed_images,
        gr.update(
            value="Click to use Imagen3 to Generate Visual Assets", interactive=True
        ),
        gr.Markdown(imagen_prompt),
    )


def move_images_to_library(selected_segment: str) -> None:
    """Moves generated images from temporary dir to local artefacts dir.

    Args:
        selected_segment: Name of the selected segment.
    """
    source_folder = os.path.join(settings.local_tmp_dir, selected_segment)
    destination_folder = os.path.join(
        settings.local_artefacts_dir, settings.local_actor_dirname, selected_segment
    )
    print(f"Move images - source {source_folder}, target {destination_folder}!")

    # Check if the destination folder exists
    if os.path.exists(destination_folder):
        # Loop through all files and subdirectories in the source folder
        for item in os.listdir(source_folder):
            s = os.path.join(source_folder, item)
            d = os.path.join(destination_folder, item)

            # If the item is a file, move it
            if os.path.isfile(s):
                shutil.move(s, d)
                print(f"Moving asset from {s} to {d}")
            # If the item is a directory, use shutil.move for the whole subdirectory
            elif os.path.isdir(s):
                shutil.move(s, d)

        # Remove the source folder (now empty)
        shutil.rmtree(source_folder)
        print(f"Files moved and source folder '{source_folder}' deleted.")
    else:
        # If the destination doesn't exist, simply move the whole source folder
        shutil.move(source_folder, destination_folder)
        print(
            f"Images moved to Marketing Library successfully into {destination_folder}!"
        )


def preprocess_assets_in_library(progress=gr.Progress()):
    LOCAL_OUTPUT_DIR_ACTOR = os.path.join(
        settings.local_artefacts_dir, settings.local_actor_processed_dirname
    )

    progress(0.1, desc="Step 1: Checking for unprocessed assets...")

    list_input_files = get_filepath_in_folder_nested(
        os.path.join(settings.local_artefacts_dir, settings.local_actor_dirname)
    )
    unprocessed_input_files = []
    print(list_input_files)
    for input_path in list_input_files:
        input_file = os.path.basename(input_path)
        output_path = os.path.join(LOCAL_OUTPUT_DIR_ACTOR, f"NoBg_{input_file}")
        if os.path.exists(output_path):
            print(f"The file {output_path} exists.")
        else:
            print(f"The file {output_path} does not exist.")
            unprocessed_input_files.append(input_path)

    count_unprocessed = len(unprocessed_input_files)
    count_processed = 1
    for input_path in unprocessed_input_files:
        progress(
            round((count_processed / count_unprocessed) * 0.8, 2),
            desc="Step 2: Processing unprocessed assets...",
        )
        input_file = os.path.basename(input_path)
        output_path = os.path.join(LOCAL_OUTPUT_DIR_ACTOR, f"NoBg_{input_file}")
        mask_path = os.path.join(LOCAL_OUTPUT_DIR_ACTOR, f"Mask_{input_file}")
        remove_background(input_path, output_path, mask_path)
        count_processed += 1

    progress(0.95, desc="Step 3: Almost done...")

    return (
        gr.update(
            root_dir=settings.local_artefacts_dir,
            ignore_glob="*.json",
            label="Library Explorer",
        ),
        gr.update(label="Selected Image Gallery", columns=3, rows=None, height="auto"),
        None,
    )


def create_bounding_box_annotator(image_data: list[dict], key: str) -> image_annotator:
    """Creates annotator with colored bounding boxes.

    Args:
        image_data: Dict of (key -> file path) to locate the template image files.
        key: Name of a template image used to locate its file path.

    Returns:
        Image annotator UI component.
    """
    global db

    annotator = image_annotator(
        value={
            "image": image_data.get(key),
            "boxes": get_template_configuration(db, key),
        },
    )
    return annotator


def save_template_configuration(annotations: dict, template_name: str) -> dict:
    global db

    result = get_bannertemplate_config_by_name(db, template_name)
    elements = annotations["boxes"]
    for element in elements:
        label = element["label"]
        result[label] = {
            "x": element["xmin"],
            "y": element["ymin"],
            "width": element["xmax"] - element["xmin"],
            "height": element["ymax"] - element["ymin"],
            "color": element["color"],
        }

    add_or_update_bannertemplate(db, result)

    return result


def _generate_banner_filename(visual_segment, image_count):
    now = datetime.datetime.now()
    datetime_str = now.strftime("%d%m%H%M%S")
    filename = f"{visual_segment}_{image_count}_{datetime_str}.png"
    return filename


def _place_image_overlay_on_background(
    overlay_image_path, background_image_path, overlay_config, output_path
):
    # Placement config
    target_x = overlay_config["x"]
    target_y = overlay_config["y"]
    target_width = overlay_config["width"]
    target_height = overlay_config["height"]

    # Open images
    background_image = Image.open(background_image_path).convert("RGBA")
    overlay_image = Image.open(overlay_image_path).convert("RGBA")

    # Calculate aspect ratio
    overlay_image_aspect_ratio = overlay_image.width / overlay_image.height

    print(
        f"Original size of overlay image {overlay_image_path}, Aspect Ratio - {overlay_image_aspect_ratio}, Size - {background_image.size}"
    )

    # Resize to meet target height, maintaining aspect ratio, using LANCZOS
    new_width = int(target_height * overlay_image_aspect_ratio)
    resized_overlay_image = overlay_image.resize(
        (new_width, target_height), Image.LANCZOS
    )
    print(f"Resized overlay image to Size - {resized_overlay_image.size}")

    # Check if resized width exceeds target width, and resize again if needed
    if new_width > target_width:
        new_height = int(target_width / overlay_image_aspect_ratio)
        resized_overlay_image = overlay_image.resize(
            (target_width, new_height), Image.LANCZOS
        )
        print(
            f"Width exceeds boundary, adjusting overlay image with width / height - {target_width} / {new_height} to Size - {resized_overlay_image.size}"
        )

    # Calculate centered coordinates
    final_x = target_x + (target_width - resized_overlay_image.width) // 2
    final_y = target_y + (target_height - resized_overlay_image.height) // 2

    # Paste actor image onto background
    background_image.paste(
        resized_overlay_image, (final_x, final_y), resized_overlay_image
    )  # Use mask for transparency

    # Save the result (optional)
    background_image.save(output_path)  # Save as PNG to preserve transparency

    return background_image


def _get_font_metrics(font):
    ascent, descent = font.getmetrics()
    avg_char_width = sum(font.getbbox(char)[2] for char in ascii_letters) / len(
        ascii_letters
    )
    return ascent, descent, avg_char_width


def _wrap_text_custom(text, font, max_width):
    words = text.split()
    lines = []
    current_line = []
    current_width = 0

    for word in words:
        word_width = font.getbbox(word)[2]
        space_width = font.getbbox(" ")[2]

        if current_width + word_width <= max_width:
            current_line.append(word)
            current_width += word_width + space_width
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_width = word_width + space_width

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def _get_font_size(textarea, text, font_name, pixel_gap=2):
    text_width, text_height = int(textarea[0]), int(textarea[1])

    for point_size in range(5, 300):
        font = ImageFont.truetype(font_name, point_size)
        ascent, descent, avg_char_width = _get_font_metrics(font)

        wrapped_lines = _wrap_text_custom(text, font, text_width)

        total_height = (ascent + descent + pixel_gap) * len(wrapped_lines) - pixel_gap

        if total_height >= text_height:
            point_size -= 1
            font = ImageFont.truetype(font_name, point_size)
            wrapped_lines = _wrap_text_custom(text, font, text_width)
            break

    return wrapped_lines, point_size


def _place_singleline_text_overlay_on_background(
    overlay_image_path,
    text,
    initial_font_size,
    overlay_config,
    font_name,
    text_color,
    alignment,
    margin=10,
):
    x, y = overlay_config["x"], overlay_config["y"]
    width, height = overlay_config["width"], overlay_config["height"]

    with Image.open(overlay_image_path) as img:
        draw = ImageDraw.Draw(img)

        # Function to get text width
        def get_text_width(font):
            return draw.textbbox((0, 0), text, font=font)[2]

        # Start with the initial font size and decrease if necessary
        font_size = initial_font_size
        font = ImageFont.truetype(font_name, font_size)
        text_width = get_text_width(font)
        print(f"Processing text {text} with initial font size {initial_font_size}")

        # Decrease font size until text fits within max_width (including margin)
        while text_width > (width - 2 * margin) and font_size > 1:
            print(f"Optimizing fontsize to fit, reducing.. ")
            font_size -= 1
            font = ImageFont.truetype(font_name, font_size)
            text_width = get_text_width(font)
        print(f"Final text {text} with font size {font_size}")

        # Calculate text position and use Pillow's built-in alignment
        if alignment == "center":
            anchor = "mm"  # middle-middle
            text_x = x + width // 2
        elif alignment == "right":
            anchor = "rm"  # right-middle
            text_x = x + width - margin
        else:  # left alignment
            anchor = "lm"  # left-middle
            text_x = x + margin

        # Calculate vertical position (center of the height)
        text_y = y + height // 2

        # Draw the text using Pillow's alignment feature
        draw.text((text_x, text_y), text, font=font, fill=text_color, anchor=anchor)

        # Save the result
        img.save(overlay_image_path)
        return img


def _place_multiline_text_overlay_on_background(
    overlay_image_path,
    text,
    overlay_config,
    font_name,
    text_color,
    alignment,
    margin=10,
):
    x, y = overlay_config["x"], overlay_config["y"]
    width, height = overlay_config["width"], overlay_config["height"]

    with Image.open(overlay_image_path) as img:
        draw = ImageDraw.Draw(img)

        wrapped_lines, font_size = _get_font_size(
            (width, height), text, font_name, margin
        )
        font = ImageFont.truetype(font_name, font_size)

        ascent, descent, _ = _get_font_metrics(font)
        line_height = ascent + descent + margin

        current_y = y
        for line in wrapped_lines:
            if alignment == "center":
                line_bbox = draw.textbbox((0, 0), line, font=font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = x + (width - line_width) // 2
            elif alignment == "right":
                line_bbox = draw.textbbox((0, 0), line, font=font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = x + width - line_width
            else:  # left alignment
                line_x = x

            draw.text((line_x, current_y), line, font=font, fill=text_color)
            current_y += line_height

        # Save the result
        img.save(overlay_image_path)
        return img


def _create_marketing_banner_baseline(
    background_path,
    background_config,
    image_inputs: dict,
    text_inputs: dict,
    output_path,
):
    if "actor_position" in background_config and "actor_path" in image_inputs:
        # Process Actor overlay
        _place_image_overlay_on_background(
            image_inputs["actor_path"],
            background_path,
            background_config["actor_position"],
            output_path,
        )

    if "logo_position" in background_config and "logo_path" in image_inputs:
        # Process Logo overlay
        _place_image_overlay_on_background(
            image_inputs["logo_path"],
            output_path,
            background_config["logo_position"],
            output_path,
        )

    if "graphic1_position" in background_config and "graphic1_path" in image_inputs:
        # Process Logo overlay
        _place_image_overlay_on_background(
            image_inputs["graphic1_path"],
            output_path,
            background_config["graphic1_position"],
            output_path,
        )

    if "graphic2_position" in background_config and "graphic2_path" in image_inputs:
        # Process Logo overlay
        _place_image_overlay_on_background(
            image_inputs["graphic2_path"],
            output_path,
            background_config["graphic2_position"],
            output_path,
        )

    if (
        "graphic_highlight2_position" in background_config
        and "graphic_highlight2_path" in image_inputs
    ):
        # Process Logo overlay
        _place_image_overlay_on_background(
            image_inputs["graphic_highlight2_path"],
            output_path,
            background_config["graphic_highlight2_position"],
            output_path,
        )

    if "text_header1_position" in background_config and "text_header1" in text_inputs:
        # Process Text Header overlay
        text_header = text_inputs["text_header1"]
        text_color = (0, 0, 0)
        text_alignment = "left"
        text_margin = 25
        font_name = C.Font.sans_bold
        _place_multiline_text_overlay_on_background(
            output_path,
            text_header,
            background_config["text_header1_position"],
            font_name=font_name,
            text_color=text_color,
            alignment=text_alignment,
            margin=text_margin,
        )

    if "text_header2_position" in background_config and "text_header2" in text_inputs:
        # Process Text Header overlay
        text_header = text_inputs["text_header2"]
        text_color = (0, 0, 0)
        text_alignment = "left"
        text_margin = 25
        font_name = C.Font.sans_regular
        _place_multiline_text_overlay_on_background(
            output_path,
            text_header,
            background_config["text_header2_position"],
            font_name=font_name,
            text_color=text_color,
            alignment=text_alignment,
            margin=text_margin,
        )

    if "text_details_position" in background_config and "text_details" in text_inputs:
        # Process Text Detail overlay
        text_header = text_inputs["text_details"]
        text_color = (0, 0, 0)
        text_alignment = "left"
        text_margin = 25
        font_name = C.Font.sans_regular
        _place_multiline_text_overlay_on_background(
            output_path,
            text_header,
            background_config["text_details_position"],
            font_name=font_name,
            text_color=text_color,
            alignment=text_alignment,
            margin=text_margin,
        )

    if (
        "text_highlight1_position" in background_config
        and "text_highlight1" in text_inputs
    ):
        # Process Text Highlight overlay
        text_header = text_inputs["text_highlight1"]
        text_color = (0, 0, 0)
        text_alignment = "center"
        text_margin = 5
        # font_name = "LiberationSansNarrow-Bold.ttf"
        font_name = C.Font.sans_bold
        _place_singleline_text_overlay_on_background(
            output_path,
            text_header,
            100,
            background_config["text_highlight1_position"],
            font_name=font_name,
            text_color=text_color,
            alignment=text_alignment,
            margin=text_margin,
        )

    if (
        "text_highlight3_position" in background_config
        and "text_highlight3" in text_inputs
    ):
        # Process Text Highlight overlay
        text_header = text_inputs["text_highlight3"]
        text_color = (0, 0, 0)
        text_alignment = "center"
        text_margin = 20
        # font_name = "LiberationSansNarrow-Bold.ttf"
        font_name = C.Font.sans_bold
        _place_singleline_text_overlay_on_background(
            output_path,
            text_header,
            120,
            background_config["text_highlight3_position"],
            font_name=font_name,
            text_color=text_color,
            alignment=text_alignment,
            margin=text_margin,
        )

    if "text_tagline_position" in background_config and "text_tagline" in text_inputs:
        # Process Text Tagline overlay
        text_header = text_inputs["text_tagline"]
        text_color = (255, 0, 0)
        text_alignment = "center"
        text_margin = 25
        font_name = C.Font.mono_italic
        _place_singleline_text_overlay_on_background(
            output_path,
            text_header,
            25,
            background_config["text_tagline_position"],
            font_name=font_name,
            text_color=text_color,
            alignment=text_alignment,
            margin=text_margin,
        )

    if "text_action_position" in background_config and "text_action" in text_inputs:
        # Process Text Tagline overlay
        text_header = text_inputs["text_action"]
        text_color = (255, 255, 255)
        text_alignment = "center"
        text_margin = 25
        font_name = C.Font.mono_bold
        _place_singleline_text_overlay_on_background(
            output_path,
            text_header,
            35,
            background_config["text_action_position"],
            font_name=font_name,
            text_color=text_color,
            alignment=text_alignment,
            margin=text_margin,
        )

    return output_path


def generate_banner(
    visual_segment_dropdown,
    bannertemplate_dropdown,
    text_header1_input,
    text_header2_input,
    text_details_input,
    text_highlight1_input,
    text_highlight3_input,
    text_tagline_input,
    text_action_input,
    logo_path_input,
    graphic1_path_input,
    graphic2_path_input,
    graphic_highlight2_path_input,
    progress=gr.Progress(),
):
    # Show a "processing" state while generating images
    yield [], gr.update(value="Processing...", interactive=False)

    LOCAL_INPUT_DIR_GRAPHICS = os.path.join(settings.local_artefacts_dir, "Graphics")
    LOCAL_INPUT_DIR_LOGO = os.path.join(settings.local_artefacts_dir, "Logo")
    LOCAL_OUTPUT_DIR_ACTOR = os.path.join(
        settings.local_artefacts_dir, "Actors_Processed"
    )
    LOCAL_INPUT_DIR_BG = os.path.join(settings.local_artefacts_dir, "Background")
    LOCAL_OUTPUT_DIR_BANNER = os.path.join(
        settings.local_artefacts_dir, "Banner_Generated"
    )  # FIXME: the dir needs to exist

    print(f"""
        {visual_segment_dropdown},
        {bannertemplate_dropdown},
        {text_header1_input},
        {text_header2_input},
        {text_details_input},
        {text_highlight1_input},
        {text_highlight3_input},
        {text_tagline_input},
        {text_action_input},
        {logo_path_input},
        {graphic1_path_input},
        {graphic2_path_input},
        {graphic_highlight2_path_input}""")

    image_inputs = {}

    if graphic1_path_input is not None and graphic1_path_input.strip() != "":
        image_inputs["graphic1_path"] = (
            f"{LOCAL_INPUT_DIR_GRAPHICS}/{graphic1_path_input}"
        )

    if graphic2_path_input is not None and graphic2_path_input.strip() != "":
        image_inputs["graphic2_path"] = (
            f"{LOCAL_INPUT_DIR_GRAPHICS}/{graphic2_path_input}"
        )

    if (
        graphic_highlight2_path_input is not None
        and graphic_highlight2_path_input.strip() != ""
    ):
        image_inputs["graphic_highlight2_path"] = (
            f"{LOCAL_INPUT_DIR_GRAPHICS}/{graphic_highlight2_path_input}"
        )

    if logo_path_input is not None and logo_path_input.strip() != "":
        image_inputs["logo_path"] = f"{LOCAL_INPUT_DIR_LOGO}/{logo_path_input}"

    text_inputs = {}

    if text_header1_input is not None and text_header1_input.strip() != "":
        text_inputs["text_header1"] = text_header1_input

    if text_header2_input is not None and text_header2_input.strip() != "":
        text_inputs["text_header2"] = text_header2_input

    if text_details_input is not None and text_details_input.strip() != "":
        text_inputs["text_details"] = text_details_input

    if text_highlight1_input is not None and text_highlight1_input.strip() != "":
        text_inputs["text_highlight1"] = text_highlight1_input

    if text_highlight3_input is not None and text_highlight3_input.strip() != "":
        text_inputs["text_highlight3"] = text_highlight3_input

    if text_tagline_input is not None and text_tagline_input.strip() != "":
        text_inputs["text_tagline"] = text_tagline_input

    if text_action_input is not None and text_action_input.strip() != "":
        text_inputs["text_action"] = text_action_input

    bannertemplate_list = bannertemplate_dropdown
    visual_segments_list = visual_segment_dropdown

    progress(0.1, desc="Step 1: Checking banner configuration and assets...")

    total_banner_count = 0
    for bannertemplate in bannertemplate_list:
        for visual_segment in visual_segments_list:
            for image_input in find_files_with_prefix(
                LOCAL_OUTPUT_DIR_ACTOR, f"NoBg_{visual_segment}"
            ):
                total_banner_count += 1

    generated_banner_images = []
    current_banner_count = 0
    for bannertemplate in bannertemplate_list:
        background_path = f"{LOCAL_INPUT_DIR_BG}/{bannertemplate}.png"
        background_config = get_bannertemplate_config_by_name(db, bannertemplate)
        for visual_segment in visual_segments_list:
            for image_input in find_files_with_prefix(
                LOCAL_OUTPUT_DIR_ACTOR, f"NoBg_{visual_segment}"
            ):
                current_banner_count += 1
                progress(
                    round((current_banner_count / total_banner_count) * 0.9, 2),
                    desc="Step 2: Generating banners dynamically ...",
                )
                image_inputs["actor_path"] = image_input
                output_filename = _generate_banner_filename(
                    visual_segment, current_banner_count
                )
                output_path = f"{LOCAL_OUTPUT_DIR_BANNER}/{output_filename}"
                print(
                    f"Generating banner count {current_banner_count} of {total_banner_count}... {output_path}"
                )
                # Create the banner with Actor & Logo overlaid
                generated_banner_image = _create_marketing_banner_baseline(
                    background_path,
                    background_config,
                    image_inputs,
                    text_inputs,
                    output_path,
                )
                print(
                    f"Generated banner count {current_banner_count} of {total_banner_count}... {output_path}"
                )
                generated_banner_images.append(generated_banner_image)

    progress(0.95, desc="Step 3: Almost done...")

    yield (
        generated_banner_images,
        gr.update(value="Click to Generate Banners for Campaign", interactive=True),
    )  # Reset the button
