"""Global configurations."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global settings overridable by .env file and environment variables."""

    gcp_project: str = "genai-mckinsey-dev-fg78"
    # NOTE: The fast model does not generate quality "eyes" for real-looking human
    image_model: str = "imagen-3.0-fast-generate-001"
    text_model: str = "gemini-1.5-flash-001"
    firestore_id: str = "(default)"

    local_artefacts_dir: str = "./artefacts"
    local_artefacts_processed_dir: str = "./artefacts/actor_processed"
    local_tmp_dir: str = "/tmp"
    n_image_generated: int = 3

    default_background: str = "White background"
    default_photography: str = (
        "Studio portrait, professional lighting, DSLR camera shot, 4K"
    )
    default_aspectratio: str = "4:3"

    # Whether to re-create the initial documents in Firestore
    is_init_backend: bool = True

    # Override values from .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()  # singleton
