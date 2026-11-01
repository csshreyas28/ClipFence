import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.json"


DEFAULT_SETTINGS = {
    "enabled": True,
    "replacement": "[REDACTED]",
    "custom_words": [
        "password",
        "api_key",
        "secret"
    ],
    "detectors": {
        "jwt": True,
        "api_keys": True,
        "email": False,
        "phone": False,
        "ipv4": False
    }
}


def ensure_settings_file():
    CONFIG_DIR.mkdir(exist_ok=True)

    if not SETTINGS_FILE.exists():
        save_settings(DEFAULT_SETTINGS)


def load_settings():
    ensure_settings_file()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            settings = json.load(file)

        return merge_defaults(settings)

    except (json.JSONDecodeError, OSError):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    CONFIG_DIR.mkdir(exist_ok=True)

    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4)


def merge_defaults(settings):
    merged = DEFAULT_SETTINGS.copy()

    merged["custom_words"] = settings.get(
        "custom_words",
        DEFAULT_SETTINGS["custom_words"]
    )

    merged["replacement"] = settings.get(
        "replacement",
        DEFAULT_SETTINGS["replacement"]
    )

    merged["enabled"] = settings.get(
        "enabled",
        DEFAULT_SETTINGS["enabled"]
    )

    merged["detectors"] = DEFAULT_SETTINGS["detectors"].copy()
    merged["detectors"].update(
        settings.get("detectors", {})
    )

    return merged