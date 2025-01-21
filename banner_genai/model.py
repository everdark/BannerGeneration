"""Data models."""

from enum import Enum

from pydantic import BaseModel


# FIXME: How to make sure the system fonts are available?
#        To install liberation fonts on macos:
#           brew install --cask font-liberation
class Font(str, Enum):
    sans_bold = "LiberationSans-Bold.ttf"
    sans_regular = "LiberationSans-Regular.ttf"
    sans_narrow_bold = "LiberationSansNarrow-Bold.ttf"
    mono_italic = "LiberationMono-Italic"
    mono_bold = "LiberationMono-Bold.ttf"


class SegmentProfile(BaseModel):
    """Data model to describe a visual segment with various attributes."""

    age: str
    background: str = "White background"
    clothing: str
    photography: str = "Studio portrait, professional lighting, DSLR camera shot, 4K"
    subject: str
    theme: str
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


# TODO: Data models for template documents.
