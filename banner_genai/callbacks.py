"""Callback functions for event listeners."""

import datetime
import os
from string import ascii_letters

import gradio as gr
from gradio_image_annotation import image_annotator
from PIL import Image, ImageDraw, ImageFont

from config import settings
from database import db
from utils.firestore import (
    get_template_configuration,
    get_bannertemplate_config_by_name,
    add_or_update_bannertemplate,
)
from utils.io import find_files_with_prefix


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


def _place_singleline_text_overlay_on_background(overlay_image_path, text, initial_font_size, overlay_config, font_name, text_color, alignment, margin=10):
    x, y = overlay_config['x'], overlay_config['y']
    width, height = overlay_config['width'], overlay_config['height']

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
        if alignment == 'center':
            anchor = 'mm'  # middle-middle
            text_x = x + width // 2
        elif alignment == 'right':
            anchor = 'rm'  # right-middle
            text_x = x + width - margin
        else:  # left alignment
            anchor = 'lm'  # left-middle
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
        font_name = "LiberationSans-Bold.ttf"
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
        font_name = "LiberationSans-Regular.ttf"
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
        font_name = "LiberationSans-Regular.ttf"
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
        font_name = "LiberationSans-Bold.ttf"
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
        font_name = "LiberationSans-Bold.ttf"
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
        font_name = "LiberationMono-Italic"
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
        font_name = "LiberationMono-Bold.ttf"
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
    LOCAL_OUTPUT_DIR_ACTOR = os.path.join(settings.local_artefacts_dir, "Actors_Processed")
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
