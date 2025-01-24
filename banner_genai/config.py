"""Global configurations."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global settings overridable by .env file and environment variables."""

    gcp_project: str = "genai-mckinsey-dev-fg78"
    # NOTE: The fast model sometimes does not generate quality "eyes" for person
    image_model: str = "imagen-3.0-fast-generate-001"
    text_model: str = "gemini-1.5-flash-001"
    firestore_id: str = "(default)"

    # This model is used for background removal.
    u2net_home: str = "./u2net"

    local_artefacts_dir: str = "./artefacts"
    local_tmp_dir: str = "/tmp"
    local_actor_dirname: str = "Actors"
    local_actor_processed_dirname: str = "Actors_Processed"
    local_banner_dirname: str = "Banner_Generated"

    n_image_generated: int = 3

    # This is for easier background removal if the background is irrelevant.
    default_background: str = "White background"
    # To create non-real-looking person, keep this attribute blank for better result.
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
