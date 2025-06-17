"""Script to demonstrate Imagen model usage."""

import base64
import io
import os

from PIL import Image
from vertexai.generative_models import GenerationConfig, GenerativeModel
from vertexai.vision_models import ImageGenerationModel

from generative_banner.config import settings
from generative_banner.utils.imagen import remove_background, show_image


# https://cloud.google.com/vertex-ai/generative-ai/docs/image/img-gen-prompt-guide

image_model = ImageGenerationModel.from_pretrained("imagen-4.0-generate-preview-06-06")

system_instruction = """
You are a prompt engineering expert specializes in high-quality prompt for Imagen, a text-to-image model.
You will create a prompt based on a description of a particular customer profile.
The task is to create photorealistic portraits of Indonesian person with colorful style of closing and accessories associated with the described profile.

Follow the instructions:
- The background must always be pure white.
- The style MUST be photorealistic and NOT artist.
- Return only the prompt.
"""

gemini_model = GenerativeModel(
    settings.text_model, generation_config=GenerationConfig(temperature=0.1), system_instruction=system_instruction
)
prompt = """
Customer profile:

A happy mid-age customer who travels alot with a camera and bag.

Your prompt:
"""
response = gemini_model.generate_content(prompt)
imagen_prompt = response.text

images = image_model.generate_images(
    prompt=imagen_prompt,
    number_of_images=1,
    safety_filter_level="block_few",
    person_generation="allow_all",
    negative_prompt="artist style",
)

image = images[0]
show_image(image)

name = "test"
generated_image_data = base64.b64decode(image._as_base64_string())
pil_image = Image.open(io.BytesIO(generated_image_data))
pil_image.save(f"./{name}.png")

os.environ["U2NET_HOME"] = settings.u2net_home
remove_background(
    input_path=f"./{name}.png",
    output_path=f"./{name}-nobg.png",
    mask_path=f"./{name}-mask.png",
)
