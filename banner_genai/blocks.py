"""Gradio frontend blocks."""

import os

import gradio as gr
from gradio_image_annotation import image_annotator

import constants as C
from callbacks import (
    create_bounding_box_annotator,
    create_new_segment,
    generate_banner,
    save_template_configuration,
    update_segment_config,
)
from config import settings
from database import db
from utils.firestore import (
    fetch_visual_segment_names,
    get_bannertemplate_list,
)
from utils.gradio import (
    display_image,
    generate_assets,
    move_images_to_library,
    preprocess_assets_in_library,
    select_folder,
)
from utils.io import create_file_map

gallery_dirname_list = []  # FIXME: Use session state instead.

# FIXME: Get rid of these constants.
default_model = settings.image_model
default_background = "White background"
default_photography = "Studio portrait, professional lighting, DSLR camera shot, 4K"
default_count = settings.n_image_generated
default_aspectratio = "4:3"


with gr.Blocks() as ui_about_tab:
    gr.Markdown("""
    ### About this Demo
    This demo demonstrates an end to end pipeline for dynamic banner generation for CVM targeting using Imagen3, Gemini and opensource Python libraries like `rembg` (which leverages DNN models for object detection).

    ### Instructions
    Step 1 - Use the "Demo Asset Library" to walk the customer through the building blocks for a dynamic banner generation - a library of elements for Actors / Background / Logos / Graphics / Text
    \n
    Step 2 - Use the "Demo Asset Creation" section to demonstrate the creation of a new visual segments (tied to customer targeting needs), generation of Actors using Imagen3
    \n
    Step 3 - Use the "Demo Asset Preprocessing" section to demonstrate the concept of removal of background from elements like Actors assets to enable overlay on top of background template
    \n
    Step 4 - Use the "Demo Banner Template" section to illustrate the concept of banner templates and how this can be defined via a UX or even via tools like Figma
    \n
    Step 5 - Use the "Demo Banner Generation" section to illustrate the concept of dynamic banner generation for one or more templates for one or more visual segments
    """)


with gr.Blocks() as ui_demo_tab_assetlibrary:
    ROOT_FOLDER = settings.local_artefacts_dir

    with gr.Column(variant="panel"):
        gr.Markdown("# Marketing Assets Library")

    with gr.Column(variant="panel"):
        with gr.Row():
            gr.Markdown(f"**Image Library:** loaded from {ROOT_FOLDER}")

    with gr.Column(variant="panel"):
        with gr.Row():
            with gr.Column(scale=1):
                file_explorer = gr.FileExplorer(
                    root_dir=ROOT_FOLDER, ignore_glob="*.json", label="Library Explorer"
                )

            with gr.Column(scale=3):
                thumbnail_gallery = gr.Gallery(
                    label="Selected Image Gallery", columns=3, rows=None, height="auto"
                )

    with gr.Column(variant="panel"):
        with gr.Row():
            displayed_image = gr.Image(label="Selected Image")

    # Event handler for folder selection
    file_explorer.change(
        select_folder,
        inputs=[file_explorer],
        outputs=[thumbnail_gallery, displayed_image],
    )

    # Event handler for thumbnail selection
    thumbnail_gallery.select(display_image, inputs=[], outputs=[displayed_image])


with gr.Blocks() as ui_demo_tab_assetcreation:
    selected_visual_segment = gr.State()

    with gr.Row(variant="panel"):
        gr.Markdown("# Create New Marketing Assets With Imagen3")

    with gr.Row():
        with gr.Column(variant="panel"):
            visual_segment_dropdown = gr.Dropdown(
                choices=fetch_visual_segment_names(db),
                label="Select Visual Segment",
                elem_id=C.ElementID.SEGMENT_DROPDOWN,
            )
            load_segment_config_button = gr.Button("Load Visual Config")

        with gr.Column(variant="panel"):
            new_segment_input = gr.Textbox(label="New Visual Segment Name")
            create_segment_button = gr.Button("Define Visual Config")

    with gr.Column(variant="panel"):
        with gr.Row(elem_id=C.ElementID.SEGMENT_INPUTS):
            subject_input = gr.Textbox(
                label="Subject",
                placeholder="Describe the subject. E.g. a vibrant Indonesian woman",
                lines=2,
                interactive=True,
            )
            age_input = gr.Textbox(
                label="Age",
                placeholder="Age of the subject. E.g. age 40-50 years old",
                lines=2,
                interactive=True,
            )
            clothing_input = gr.Textbox(
                label="Clothing",
                placeholder="Clothing of the subject. E.g. wearing a traditional Balinese dress",
                lines=4,
                interactive=True,
            )
            theme_input = gr.Textbox(
                label="Theme",
                placeholder="Theme of the visual. E.g. enjoying movie on her phone screen wearing red headphones",
                lines=4,
                interactive=True,
            )
        with gr.Row(elem_id=C.ElementID.SEGMENT_INPUTS_EXT):
            background_input = gr.Textbox(
                label="Background Settings",
                placeholder="White background",
                interactive=True,
            )
            photography_input = gr.Textbox(
                label="Photography Setting",
                placeholder="Studio portrait, professional lighting, DSLR camera shot, 4K",
                interactive=True,
            )
        with gr.Row():
            count_input = gr.Dropdown(
                choices=[1, 2, 3], label="# Images", interactive=True
            )
            aspectratio_input = gr.Dropdown(
                choices=["1:1", "3:4", "4:3", "16:9", "9:16"],
                label="Aspect Ratio",
                interactive=True,
            )
            model_input = gr.Dropdown(
                choices=["imagen-3.0-fast-generate-001", "imagen-3.0-generate-001"],
                label="Imagen Models",
                interactive=True,
            )

    with gr.Row(visible=False) as generate_visual_assets:
        generate_assets_button = gr.Button(
            "Click to use Imagen3 to Generate Visual Assets"
        )

    with gr.Row(visible=False) as review_visual_assets:
        with gr.Row(variant="panel"):
            prompt_text = gr.Markdown()
        with gr.Row(variant="panel"):
            gallery = gr.Gallery(label="Generated Images", columns=[3], height="auto")

    with gr.Row(visible=False) as approve_visual_assets:
        with gr.Column(variant="panel"):
            approve_button = gr.Button("Save Images to Marketing Library")

    gr.on(
        triggers=[load_segment_config_button.click, visual_segment_dropdown.change],
        fn=update_segment_config,
        inputs=visual_segment_dropdown,
        # NOTE: The outputs shall follow alphabetic order from the SegmentProfile model.
        outputs=[
            age_input,
            background_input,
            clothing_input,
            photography_input,
            subject_input,
            theme_input,
            selected_visual_segment,
        ],
    ).then(
        fn=lambda: [
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
        ],
        outputs=[
            generate_visual_assets,
            review_visual_assets,
            approve_visual_assets,
        ],
    )

    create_segment_button.click(
        create_new_segment,
        inputs=[
            age_input,
            background_input,
            clothing_input,
            photography_input,
            subject_input,
            theme_input,
            new_segment_input,
        ],
        outputs=visual_segment_dropdown,
    ).then(
        fn=lambda: [
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
        ],
        outputs=[
            generate_visual_assets,
            review_visual_assets,
            approve_visual_assets,
        ],
    )

    # When click imagen button...
    generate_assets_button.click(
        generate_assets,
        inputs=[
            subject_input,
            age_input,
            clothing_input,
            theme_input,
            background_input,
            photography_input,
            count_input,
            aspectratio_input,
            model_input,
            selected_visual_segment,
        ],
        outputs=[gallery, generate_assets_button, prompt_text],
    ).then(
        fn=lambda: [
            gr.update(visible=True),
            gr.update(visible=True),
        ],
        outputs=[
            review_visual_assets,
            approve_visual_assets,
        ],
    )

    # When click save images...
    approve_button.click(
        move_images_to_library,
        inputs=[
            selected_visual_segment,
            # subject_input,
            # age_input,
            # clothing_input,
            # theme_input,
            # background_input,
            # photography_input,
        ],
        outputs=[],
    ).then(
        fn=lambda: [
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
        ],
        outputs=[
            generate_visual_assets,
            review_visual_assets,
            approve_visual_assets,
        ],
    ).then(
        fn=lambda: [
            gr.update(choices=fetch_visual_segment_names(db)),
            gr.update(value=None),  # Reset the dropdown value
            gr.update(value=None),
            gr.update(value=None),
            gr.update(value=None),
            gr.update(value=None),
            gr.update(value=default_background),
            gr.update(value=default_photography),
            gr.update(value=default_count),
            gr.update(value=default_aspectratio),
            gr.update(value=default_model),
        ],
        outputs=[
            visual_segment_dropdown,
            new_segment_input,
            subject_input,
            age_input,
            clothing_input,
            theme_input,
            background_input,
            photography_input,
            count_input,
            aspectratio_input,
            model_input,
        ],
    )


with gr.Blocks() as ui_demo_tab_assetpreprocess:
    # FIXME: The block is almost the same as the asset library tab. Reuse the layout?
    with gr.Column(variant="panel"):
        gr.Markdown("# Marketing Assets Preprocessing")

    with gr.Column(variant="panel"):
        preprocess_assets_button = gr.Button(
            "Click to Preprocess Newly Created Visual Assets"
        )

    with gr.Column(variant="panel"):
        with gr.Row():
            with gr.Column(scale=1):
                file_explorer_pp = gr.FileExplorer(
                    root_dir=settings.local_artefacts_dir,
                    ignore_glob="*.json",
                    label="Library Explorer",
                )

            with gr.Column(scale=3):
                thumbnail_gallery_pp = gr.Gallery(
                    label="Selected Image Gallery", columns=3, rows=None, height="auto"
                )

    with gr.Column(variant="panel"):
        with gr.Row():
            displayed_image_pp = gr.Image(label="Selected Image")

    preprocess_assets_button.click(
        preprocess_assets_in_library,
        inputs=[],
        outputs=[file_explorer_pp, thumbnail_gallery_pp, displayed_image_pp],
    )

    # Event handler for folder selection
    file_explorer_pp.change(
        select_folder,
        inputs=[file_explorer_pp],
        outputs=[thumbnail_gallery_pp, displayed_image_pp],
    )

    # Event handler for thumbnail selection
    thumbnail_gallery_pp.select(display_image, inputs=[], outputs=[displayed_image_pp])


with gr.Blocks() as ui_demo_bannertemplateconfig_tab:
    LOCAL_OUTPUT_DIR_BG = os.path.join(
        settings.local_artefacts_dir, "Background_Processed"
    )

    # (template key -> template image file path)
    local_image_data = gr.State(create_file_map(LOCAL_OUTPUT_DIR_BG, ".png", "Grid_"))

    gr.Markdown("# Banner Template Configuration Demo")

    gr.Markdown("#### Select Banner Template")
    image_key_dropdown = gr.Dropdown(
        choices=list(local_image_data.value.keys()),
        label="Select the background template to configure",
        value=None,  # do not select any initial value
        interactive=True,
    )

    # FIXME: why do we need a tab here?
    with gr.Tab("Object annotation", id="tab_object_annotation"):
        annotator = image_annotator(value=None, show_label=False)

        button_get = gr.Button("Save Template Configuration")
        json_boxes = gr.JSON()
        button_get.click(
            fn=save_template_configuration,
            inputs=[annotator, image_key_dropdown],
            outputs=json_boxes,
        )

    image_key_dropdown.change(
        create_bounding_box_annotator,
        inputs=[local_image_data, image_key_dropdown],
        outputs=annotator,
    )


# TODO: Use session state instead.
selected_visual_segment_list = None
selected_bannertemplate_list = None


with gr.Blocks() as ui_demo_tab_bannergen:
    with gr.Row(variant="panel"):
        gr.Markdown("# Generate Dynamically New Marketing Banners")

    with gr.Column(variant="panel"):
        preprocess_visualsegments_button = gr.Button(
            "Click to update Newly Added Visual Segments"
        )

    with gr.Row():
        with gr.Column(scale=1, variant="panel"):
            visual_segment_dropdown = gr.Dropdown(
                choices=fetch_visual_segment_names(db),
                label="Select Visual Segment",
                multiselect=True,
            )

        with gr.Column(scale=1, variant="panel"):
            bannertemplate_options = get_bannertemplate_list(db)
            bannertemplate_dropdown = gr.Dropdown(
                choices=bannertemplate_options,
                label="Select Banner Template",
                multiselect=True,
            )

    with gr.Column(variant="panel"):
        with gr.Row():
            text_header1_input = gr.Textbox(
                label="Text Header 1",
                value="Freedom Unlimited Apps Bundle Special Offer",
                lines=2,
                interactive=True,
            )
            text_header2_input = gr.Textbox(
                label="Text Header 2",
                value="Enjoy the festivities with new exciting games and movies.",
                lines=2,
                interactive=True,
            )
        with gr.Row():
            text_details_input = gr.Textbox(
                label="Text Details",
                value="FREEDOM U ! Now Able to Access More Apps, Limitless Call to IM3 Ooredoo and Tri! Plus, 24 hours to access even more of your favorite apps, like YouTube, Instagram, TikTok, Facebook, Spotify, Joox, WhatsApp, and Line. This will be unlimited",
                lines=5,
                interactive=True,
            )
        with gr.Row():
            text_highlight1_input = gr.Textbox(
                label="Text Highlight 1", value="100 GB", interactive=True
            )
            text_highlight3_input = gr.Textbox(
                label="Text Highlight 3", value="250 Ribu Only", interactive=True
            )
        with gr.Row():
            text_tagline_input = gr.Textbox(
                label="Text Tagline",
                value="Offer Valid for prepaid and postpaid IM3 customers.",
                interactive=True,
            )
            text_action_input = gr.Textbox(
                label="Text Action", value="BUY NOW", interactive=True
            )

        with gr.Row():
            with gr.Column(scale=1, variant="panel"):
                logo_path_input = gr.Textbox(
                    label="Logo Path", value="im3logo.png", interactive=True
                )

        with gr.Row():
            with gr.Column(scale=1, variant="panel"):
                graphic1_path_input = gr.Textbox(
                    label="Graphics 1", value="Graphics1.png", interactive=True
                )
            with gr.Column(scale=1, variant="panel"):
                graphic2_path_input = gr.Textbox(
                    label="Graphics 2", value="Graphics4.png", interactive=True
                )
            with gr.Column(scale=1, variant="panel"):
                graphic_highlight2_path_input = gr.Textbox(
                    label="Graphics Highlight",
                    value="50GraphicH2.png",
                    interactive=True,
                )

    with gr.Row(visible=False) as generate_banner_assets:
        generate_bannerassets_button = gr.Button(
            "Click to Generate Banners for Campaign"
        )

    with gr.Row(visible=False) as review_banner_assets:
        with gr.Row(variant="panel"):
            banner_gallery = gr.Gallery(
                label="Generated Images", columns=[3], height="auto"
            )

    with gr.Row(visible=False) as success_banner_assets:
        with gr.Row(variant="panel"):
            banner_prompt_text = gr.Markdown()

    def load_config(selected_visual_segments, selected_bannertemplates):
        if not selected_visual_segments:
            gr.Warning(
                "Please select one or more visual segment from the dropdown.",
                duration=2,
            )
            return

        if not selected_bannertemplates:
            gr.Warning(
                "Please select one or more banner templates from the dropdown.",
                duration=2,
            )
            return

        global selected_visual_segment_list  # Declare selected_visual_segment as global
        selected_visual_segment_list = selected_visual_segments

        global selected_bannertemplate_list
        selected_bannertemplate_list = selected_bannertemplates

        print(
            f"Selected Visual Segment - {selected_visual_segment_list}; Banner Templates - {selected_bannertemplate_list}"
        )

        return

    # TODO: Merge the two listener into one.
    # Event listener for the dropdown
    visual_segment_dropdown.change(
        load_config,
        inputs=[visual_segment_dropdown, bannertemplate_dropdown],
        outputs=[],
    ).then(
        fn=lambda: [
            gr.update(visible=True),  # Return the update directly
            gr.update(visible=False),  # Return the update to disable image gallery
        ],
        outputs=[generate_banner_assets, review_banner_assets],
    )

    # Event listener for the dropdown
    bannertemplate_dropdown.change(
        load_config,
        inputs=[visual_segment_dropdown, bannertemplate_dropdown],
        outputs=[],
    ).then(
        fn=lambda: [
            gr.update(visible=True),  # Return the update directly
            gr.update(visible=False),  # Return the update to disable image gallery
        ],
        outputs=[generate_banner_assets, review_banner_assets],
    )

    # Event listener for the "Generate Visual Assets" button
    generate_bannerassets_button.click(
        fn=lambda: gr.update(visible=True), outputs=review_banner_assets
    ).then(
        generate_banner,
        inputs=[
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
        ],
        outputs=[
            banner_gallery,
            generate_bannerassets_button,
        ],  # Include the button as an output
    ).then(
        fn=lambda: [
            gr.update(visible=True),
            gr.update(
                value=f"##  ... Banner Generation Demo Complete. Powered By Google Vertex AI, Gemini & Imagen3 ..."
            ),
        ],
        outputs=[success_banner_assets, banner_prompt_text],
    )

    def update_dropdown():  # No input needed here
        """
        This function updates the choices of the visual_segment_dropdown.
        """
        return gr.Dropdown(
            choices=fetch_visual_segment_names(db),
            label="Select Visual Segment",
            multiselect=True,
        )

    preprocess_visualsegments_button.click(
        fn=update_dropdown, outputs=visual_segment_dropdown
    )
