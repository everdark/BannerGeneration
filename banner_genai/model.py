"""Data models."""

from pydantic import BaseModel

from config import settings


class SegmentProfile(BaseModel):
    """Data model to describe a visual segment with various attributes."""

    age: str | None = None
    background: str = settings.default_background
    clothing: str | None = None
    photography: str = settings.default_photography
    subject: str | None = None
    theme: str | None = None
    visualsegment: str

    def prompt(self) -> str:
        """Creates a basic prompt to consolidate all attributes."""

        # TODO: Dynamically create attributes to allow some missingness.
        #       For example, photography should be optional cause it only helps for
        #       near-real human creation.

        prompt = f"""
        "Subject: {self.subject}"
        "Age: {self.age}"
        "Clothing: {self.clothing}"
        "Theme: {self.theme}"
        "Environment Settings: {self.background}"
        "Photography Setting: {self.photography}"

        If the subject involves multiple people, ensure that they DO NOT LOOK alike.
        """
        return prompt


class Offer(BaseModel):
    """Data model for package offer."""

    data: str
    price: str
    time: str

    def text(self) -> str:
        lines = [f"{k}: {v}" for k, v in dict(self).items()]
        return "\n".join(lines)


# TODO: Data models for template documents.
