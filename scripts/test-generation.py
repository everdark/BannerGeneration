"""Script to demonstrate marketing message generation using LLM."""

from generative_banner.model import Offer
from generative_banner.utils.text import batch_generate_marketing_contents

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
