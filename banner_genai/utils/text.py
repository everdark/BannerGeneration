"""Module to handle text generations for marketing content."""

from typing import Literal

from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
)

from config import settings
from model import Offer

system_instructions = {
    "sms": "You are a Telco marketing expert that specializes in creating short, sincere, and concise marketing message in SMS format.",
    "popup": "You are a Telco marketing expert that specializes in creating pop-up message used in our mobile app.",
}

user_profiles = {
    "core_heavy_user": "Customers who are loyal and happy to our brand.",
    "up_and_coming": "Customers who are young and newbies recently onboarded, excisting about our brand to explore more.",
    "multi_service_non_cvm_taker": "Customers with weak loyalty and switching brands frequently for values.",
    "traditional_churner": "Customers in their mid-40s, and we are likely to lose them if we do nothing to entertain them.",
    "dormant_base": "Customers who are not active now and we need some stimulation to bring them back.",
}


def invoke_gemini_for_text(
    prompt: str,
    model: str | None = None,
    config: GenerationConfig | None = None,
) -> str:
    if model is None:
        model = settings.text_model

    gemini_model = GenerativeModel(model, generation_config=config)
    response = gemini_model.generate_content(prompt, generation_config=config)
    return response.text


def _prompt(offer: Offer, user_profile: str, n: int) -> str:
    prompt = f"""
    Create {n} promoting messages for the following offer and make sure they are variant:

    {offer.text()}

    Customize the tone to attract the following customer profile:

    {user_profile}
    """
    return prompt


def batch_generate_marketing_contents(
    offer: Offer,
    channel: Literal["sms", "popup"],
    n: int = 3,
    config: GenerationConfig | None = None,
) -> dict[str, str]:
    """Generates marketing contents using LLM.

    Args:
        offer: Package offer to be promoted.
        channel: Marketing channel.
        n: Number of candidates to generate.
        config: Gemini model configuration.

    Returns:
        Generated content by segment.
    """
    global system_instructions
    global user_profiles

    model_name = settings.text_model
    if config is None:
        config = GenerationConfig(temperature=0.1)

    system_instruction = system_instructions[channel]
    gemini_model = GenerativeModel(
        model_name, generation_config=config, system_instruction=system_instruction
    )

    results = {}
    for segment, user_profile in user_profiles.items():
        prompt = _prompt(offer, user_profile, n=n)
        response = gemini_model.generate_content(prompt)
        results[segment] = response.text

    return results
