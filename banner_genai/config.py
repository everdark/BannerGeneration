"""Global configurations."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global settings overridable by .env file and environment variables."""

    gcp_project: str = "genai-mckinsey-dev-fg78"
    image_model: str = "imagen-3.0-fast-generate-001"
    text_model: str = "gemini-1.5-flash-001"
    firestore_id: str = "(default)"

    local_artefacts_dir: str = "./Artefacts"
    local_artefacts_processed_dir: str = "./Artefacts/processed"
    local_tmp_dir: str = "/tmp"
    n_image_generated: int = 3

    default_background: str = "White background"
    default_photography: str = (
        "Studio portrait, professional lighting, DSLR camera shot, 4K"
    )
    default_aspectratio: str = "4:3"

    # Override values from .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()  # singleton
