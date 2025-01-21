"""Utility - Assorted JSON Handling for Gradio."""

import base64
import datetime
import io
import json
import os
import shutil

import gradio as gr
import numpy as np
from PIL import Image

from config import settings
from utils.imagen import (
    invoke_gemini_for_text,
    generate_imagen_outputs,
    remove_background,
)
from utils.io import get_filepath_in_folder_nested
from model import SegmentProfile

# TODO: Move event methods to callbacks.py module for better clarity.


def json_to_html_table(json_data):
    try:
        data_dict = json.loads(json_data)
    except json.JSONDecodeError:
        return "<p>Invalid JSON format.</p>"

    html_table = """
    <table border="1">
        <tr>
            <th>Attribute</th>
            <th>Value</th>
        </tr>
    """

    for key, value in data_dict.items():
        html_table += f"<tr><td>{key}</td><td>{value}</td></tr>"

    html_table += "</table>"
    return html_table


def get_image_files(dir: str):
    image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
    images = [
        f for f in os.listdir(dir) if os.path.splitext(f)[1].lower() in image_extensions
    ]
    return images


def create_thumbnail(image_path, size=(200, 200)):
    with Image.open(image_path) as img:
        img.thumbnail(
            size, Image.Resampling.LANCZOS
        )  # use a high-quality resampling filter
        return np.array(img)


def update_thumbnails(selected_folder):
    image_files = get_image_files(selected_folder)
    thumbnails = [
        create_thumbnail(os.path.join(selected_folder, img)) for img in image_files
    ]
    imagepath = [(os.path.join(selected_folder, img)) for img in image_files]
    return thumbnails, imagepath


def display_image(evt: gr.SelectData):  # , selected_folder):
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
            thumbnails, imagepath = update_thumbnails(
                dirname
            )  # Get thumbnails for the current dirname
            all_thumbnails.extend(thumbnails)
            gallery_dirname_list.extend(imagepath)  # Add imagepath for each thumbnail

        return all_thumbnails, None  # Return only the list of thumbnails
    return None, None  # Return None if no files are selected


def generate_image_filename(directory, image_count):
    now = datetime.datetime.now()
    datetime_str = now.strftime("%d%m%H%M%S")  # Format as ddmmHHMMSS
    filename = f"{directory}_{image_count}_{datetime_str}.png"  # Create filename with .png extension
    return filename


def display_message(type, msg, duration):
    duration = None if duration < 0 else duration
    if type == "error":
        raise gr.Error(msg, duration=duration)
    elif type == "info":
        gr.Info(msg, duration=duration)
    elif type == "warning":
        gr.Warning(msg, duration=duration)


def rewrite_prompt(segment_profile: SegmentProfile) -> str:
    prompt_user_input = segment_profile.prompt()
    print(f"User Input : {prompt_user_input}")

    # TODO: Move this out.
    rewrite_prompt = f"""
        Act as a prompt engineering expert to generate a high quality prompt for Imagen3 image generation strictly following the user input below.

        Extract all key information and entities required for you to rewrite the prompt retaining exact original intent without hyperbole to feed it to an image generation model.
        Retain all inputs related to subject including age, ethinicity, gender, clothing, theme, background, photography in your output prompt
        The input will be based for a marketing campaign description for creating posters, banners, etc.
        Strictly do not provide any input text in the output top prompts or high confidence prompt.
        You are only to generate image and not text on image.
        The output should be concise, explaining all entities of what is required in the image and how it has to be generated.

        Check if your response is a SINGLE high quality prompt meeting the guidelines above, before responding.

        USER INPUT -
        {prompt_user_input}

        OUTPUT -
    """
    prompt = invoke_gemini_for_text(rewrite_prompt)
    return prompt


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
    """Function to handle "Generate Visual Assets" button click."""

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
            generate_image_filename(selected_visual_segment, image_count),
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


def move_images_to_library(
    selected_segment,
    # subject_input,
    # age_input,
    # clothing_input,
    # theme_input,
    # background_input,
    # photography_input,
):
    source_folder = os.path.join(settings.local_tmp_dir, selected_segment)
    destination_folder = os.path.join(
        settings.local_artefacts_dir, "Actors", selected_segment
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

    # updated_visualsegment_config = {
    #     "visualsegment": selected_segment,
    #     "subject": subject_input,
    #     "age": age_input,
    #     "clothing": clothing_input,
    #     "theme": theme_input,
    #     "background": background_input,
    #     "photography": photography_input,
    # }

    # # Update Firebase config
    # add_or_update_visual_segment(updated_visualsegment_config)

    # print(f"Updated config - \n {updated_visualsegment_config}")


def preprocess_assets_in_library(progress=gr.Progress()):
    # FIXME: The dir needs to exist beforehand.
    LOCAL_OUTPUT_DIR_ACTOR = settings.local_artefacts_processed_dir

    progress(0.1, desc="Step 1: Checking for unprocessed assets...")

    list_input_files = get_filepath_in_folder_nested(
        os.path.join(settings.local_artefacts_dir, "Actors")
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
