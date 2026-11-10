import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from platformdirs import user_data_dir, user_documents_dir

APP_NAME = "canvas-course-materials"

DEFAULT_DOWNLOAD_DIR = Path(user_documents_dir()) / "Canvas"
DEFAULT_STATE_PATH = Path(user_data_dir(APP_NAME, appauthor=False)) / "state.json"


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    base_url: str
    token: str
    download_dir: Path
    state_path: Path


def load_config() -> Config:
    load_dotenv()
    base_url = os.environ.get("CANVAS_URL", "").strip()
    token = os.environ.get("CANVAS_TOKEN", "").strip()

    if not base_url:
        raise ConfigError(
            "CANVAS_URL is not set. Put it in your .env file "
            '(e.g. CANVAS_URL="https://university.test.instructure.com").'
        )
    if not base_url.startswith(("http://", "https://")):
        raise ConfigError(f"CANVAS_URL must start with http:// or https:// (got {base_url!r}).")
    if not token:
        raise ConfigError(
            "CANVAS_TOKEN is not set. Generate an access token in Canvas "
            "(Account > Settings > Approved Integrations) and add it to your .env file."
        )

    return Config(
        base_url=base_url.rstrip("/"),
        token=token,
        download_dir=Path(
            os.environ.get("CANVAS_DOWNLOAD_DIR", DEFAULT_DOWNLOAD_DIR)
        ).expanduser(),
        state_path=Path(
            os.environ.get("CANVAS_STATE_PATH", DEFAULT_STATE_PATH)
        ).expanduser(),
    )
