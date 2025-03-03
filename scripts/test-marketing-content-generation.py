import base64
import io

from PIL import Image
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
)
from vertexai.vision_models import ImageGenerationModel

from banner_genai.config import settings
from banner_genai.model import Offer
from banner_genai.utils.text import batch_generate_marketing_contents
from banner_genai.utils.imagen import (
    remove_background,
    show_image,
)

offer = Offer(
    data="30 GB",
    price="Rp 59,000",
    time="28 days",
)

user_profiles = {
    "core_heavy_user": "Customers who are loyal and happy to our brand.",
    "up_and_coming": "Customers who are young and newbies recently onboarded, excisting about our brand to explore more.",
    "multi_service_non_cvm_taker": "Customers with weak loyalty and switching brands frequently for values.",
    "traditional_churner": "Customers in their mid-40s, and we are likely to lose them if we do nothing to entertain them.",
    "dormant_base": "Customers who are not active now and we need some stimulation to bring them back.",
}

sms_contents = batch_generate_marketing_contents(offer, "sms")
popup_contents = batch_generate_marketing_contents(offer, "popup")


for segment, content in sms_contents.items():
    print(f"For {segment}:")
    print("==================================")
    print(content)

for segment, content in popup_contents.items():
    print(f"For {segment}:")
    print("==================================")
    print(content)


# core heavy user
# - a drop in purchase (e.g., we miss you)
# - spike in international usage (e.g., change image to travel-like)
# - customer recently try to buy data loan and drop off (not complete the purchase)


# https://cloud.google.com/vertex-ai/generative-ai/docs/image/img-gen-prompt-guide

image_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")

system_instruction = """
You are a prompt engineering expert specializes in high-quality prompt for Imagen 3, a text-to-image model.
You will create a prompt based on a description of a particular customer profile.
The task is to create photorealistic portraits of Indonesian person with colorful style of closing and accessories associated with the described profile.

Follow the instructions:
- The background must always be pure white.
- The style MUST be photorealistic and NOT artist.
- Return only the prompt.
"""

# A customer who is loyal and happy to our brand and seems to travel a lot around the world.
# Newly joined and curious to explore our brand and apparently a music lover.
# Newly joined and curious to explore our brand and apparently a sport lover.

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
    number_of_images=3,
    safety_filter_level="block_few",
    person_generation="allow_all",
    negative_prompt="artist style",
)

image = images[2]
show_image(image)


name = "travel-lover"
generated_image_data = base64.b64decode(image._as_base64_string())
pil_image = Image.open(io.BytesIO(generated_image_data))
pil_image.save(f"./{name}.png")

remove_background(
    input_path=f"./{name}.png",
    output_path=f"./{name}-nobg.png",
    mask_path=f"./{name}-mask.png",
)
