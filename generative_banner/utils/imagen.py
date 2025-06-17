"""Utility - Imagen3 & Gemini Model Invocations.

.. code-block:: python
    prompt = f'''
    "Subject: a young Indonesian woman"
    "Age: 20-30 years old"
    "Clothing: Modern stylish clothing in red / yellow"
    "Theme: Joyfully looking at her phone"
    "Environment Settings: white bacjground"
    "Photography Setting: studio lighting, DLSR"
    '''

    image_list = generate_imagen_outputs(prompt, 1, "1:1")
    show_image(image_list[0])
"""

import base64
import io
from typing import Literal

import numpy as np
from PIL import Image
from rembg import new_session, remove
from vertexai.generative_models import (
    Content,
    GenerativeModel,
)
from vertexai.vision_models import GeneratedImage, ImageGenerationModel

from generative_banner.config import settings
from generative_banner.model import SegmentProfile


def generate_imagen_outputs(
    prompt: str,
    number_of_images: int = 1,
    aspect_ratio: Literal["1:1", "9:16", "16:9", "4:3", "3:4"] = "1:1",
    model: str = "imagen-3.0-generate-001",  # https://ai.google.dev/gemini-api/docs/imagen
) -> list[GeneratedImage]:
    generation_model = ImageGenerationModel.from_pretrained(model)
    image_list = generation_model.generate_images(
        prompt=prompt,
        number_of_images=number_of_images,
        aspect_ratio=aspect_ratio,
    )
    return image_list.images


def show_image(image: GeneratedImage) -> None:
    image_data = base64.b64decode(image._as_base64_string())
    pil_image = Image.open(io.BytesIO(image_data))
    pil_image.show()


def invoke_gemini_for_text(prompt: str, model: str | None = None) -> str:
    if model is None:
        model = settings.text_model

    gemini_model = GenerativeModel(model)
    response = gemini_model.generate_content(prompt)
    return response.text


def invoke_gemini_multimodal_model_with_files(
    model: GenerativeModel, contents: list[Content]
):
    response = model.generate_content(contents)
    return response


def rewrite_prompt(segment_profile: SegmentProfile) -> str:
    prompt_user_input = segment_profile.prompt()

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


def remove_background(
    input_path: str,
    output_path: str,
    mask_path: str,
    margin=10,
    alpha_threshold=10,
):
    with open(input_path, "rb") as input_file:
        input_data = input_file.read()

    # NOTE: U2Net excels at accurate and detailed salient object detection,
    #       enabling high-quality background removal with preserved fine details and
    #       complex edge structures.
    session = new_session("u2net")  # require internet to download the model

    # NOTE: enables alpha matting for smoother edges. Alpha matting is a technique for determining partial transparency of pixels in an image, especially at object edges, to create smooth and realistic transitions between foreground and background.
    # NOTE: alpha_matting_foreground_threshold high value (close to 255, which is pure white) is chosen because: a) It ensures that only pixels that are very likely to be part of the foreground are immediately classified as such (b) ensure that the solid parts of the  dress and the actor's skin are definitely classified as foreground
    # NOTE: alpha_matting_background_threshold low value (close to 0, which is pure black) is chosen because: a) It ensures that only pixels that are very likely to be part of the background are immediately classified as such (b) we generate actor images with white background to optimize output, avoiding black or dark dress colors
    # NOTE: alpha_matting_erode_size=10 parameter in rembg controls the size of the transition area between definite foreground and background for alpha matting. Useful for preserving details around actor dress and the hair or held objects, ensuring smooth transitions and preserved details.
    output_data = remove(
        input_data,
        session=session,
        alpha_matting=True,
        alpha_matting_foreground_threshold=230,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_size=10,
    )

    # Open the output image and convert to numpy array
    output_image = Image.open(io.BytesIO(output_data)).convert("RGBA")
    output_array = np.array(output_image)

    # Extract the alpha channel
    alpha = output_array[:, :, 3]

    # Apply threshold to alpha channel for a binary mask filter
    # NOTE: Using alpha_threshold to ensure excess white space in top or sides is removed. 2C had problem of excess white space in top
    alpha_threshold_mask = alpha > alpha_threshold

    # Find the bounding box of the non-transparent area
    rows = np.any(alpha_threshold_mask, axis=1)
    cols = np.any(alpha_threshold_mask, axis=0)

    if np.any(rows) and np.any(
        cols
    ):  # Check if there's any content left after thresholding
        ymin, ymax = np.where(rows)[0][[0, -1]]
        xmin, xmax = np.where(cols)[0][[0, -1]]

        # Add margin
        height, width = alpha.shape
        ymin = max(0, ymin - margin)
        ymax = min(height, ymax + margin)
        xmin = max(0, xmin - margin)
        xmax = min(width, xmax + margin)

        # Crop the image
        cropped_image = output_image.crop((xmin, ymin, xmax, ymax))

        # Save the cropped output image with transparent background
        cropped_image.save(output_path)

        # Crop and save the mask
        mask_image = Image.fromarray(alpha)
        cropped_mask = mask_image.crop((xmin, ymin, xmax, ymax))
        cropped_mask.save(mask_path)

        print(f"Background removed image saved to {output_path}")
        print(f"Mask saved to {mask_path}")
    else:
        print("No content found after applying threshold. Saving original image.")
        output_image.save(output_path)
        Image.fromarray(alpha).save(mask_path)
