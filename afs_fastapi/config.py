"""Configuration management for the AFS FastAPI platform.

This module provides configuration utilities including external viewer preferences
and system-specific settings for optimal development workflow.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


class ConfigurationError(Exception):
    """Exception raised when configuration operations fail."""

    pass


class ViewerConfig:
    """Configuration manager for external viewers.

    Manages user preferences for external Markdown viewers and provides
    persistent storage of configuration settings for the AFS FastAPI platform.

    Agricultural Development Context:
    Maintains consistent documentation viewing preferences across development
    sessions, ensuring that agricultural robotics documentation (WORKFLOW.md,
    TDD_WORKFLOW.md, etc.) opens in the developer's preferred environment.
    """

    DEFAULT_CONFIG_DIR = Path.home() / ".afs_fastapi"
    CONFIG_FILE = "viewer_config.json"

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize viewer configuration manager.

        Args:
            config_dir: Directory for configuration files. Defaults to ~/.afs_fastapi
        """
        self.config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self.config_path = self.config_dir / self.CONFIG_FILE
        self._config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file, creating default if needed."""
        if not self.config_path.exists():
            self._create_default_config()
            return

        try:
            with open(self.config_path, encoding="utf-8") as f:
                self._config = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e

        # Ensure required keys exist
        self._ensure_config_keys()

    def _create_default_config(self) -> None:
        """Create default configuration file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        default_config = {
            "preferred_viewer": self._get_platform_default(),
            "auto_detect_viewers": True,
            "fallback_to_system": True,
            "viewer_preferences": {
                "macdown": {"priority": 1},
                "typora": {"priority": 2},
                "mark_text": {"priority": 3},
                "vscode": {"priority": 4},
                "default_system": {"priority": 5},
            },
        }

        self._config = default_config
        self._save_config()

    def _get_platform_default(self) -> str:
        """Get default viewer for current platform."""
        if sys.platform == "darwin":
            return "macdown"
        elif sys.platform in ("linux", "linux2"):
            return "default_system"
        elif sys.platform == "win32":
            return "default_system"
        else:
            return "default_system"

    def _ensure_config_keys(self) -> None:
        """Ensure all required configuration keys exist."""
        required_keys: dict[str, Any] = {
            "preferred_viewer": self._get_platform_default(),
            "auto_detect_viewers": True,
            "fallback_to_system": True,
            "viewer_preferences": {},
        }

        for key, default_value in required_keys.items():
            if key not in self._config:
                self._config[key] = default_value

    def _save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, sort_keys=True)
        except OSError as e:
            raise ConfigurationError(f"Failed to save configuration: {e}") from e

    def get_preferred_viewer(self) -> str:
        """Get the preferred viewer from configuration.

        Returns:
            String key of the preferred viewer.
        """
        return str(self._config.get("preferred_viewer", self._get_platform_default()))

    def set_preferred_viewer(self, viewer_key: str) -> None:
        """Set the preferred viewer in configuration.

        Args:
            viewer_key: Key of the viewer to set as preferred.
        """
        self._config["preferred_viewer"] = viewer_key
        self._save_config()

    def get_auto_detect(self) -> bool:
        """Check if auto-detection of viewers is enabled.

        Returns:
            True if auto-detection is enabled, False otherwise.
        """
        return bool(self._config.get("auto_detect_viewers", True))

    def set_auto_detect(self, enabled: bool) -> None:
        """Enable or disable auto-detection of viewers.

        Args:
            enabled: Whether to enable auto-detection.
        """
        self._config["auto_detect_viewers"] = enabled
        self._save_config()

    def get_fallback_to_system(self) -> bool:
        """Check if fallback to system default is enabled.

        Returns:
            True if fallback is enabled, False otherwise.
        """
        return bool(self._config.get("fallback_to_system", True))

    def set_fallback_to_system(self, enabled: bool) -> None:
        """Enable or disable fallback to system default viewer.

        Args:
            enabled: Whether to enable fallback.
        """
        self._config["fallback_to_system"] = enabled
        self._save_config()

    def get_viewer_priority(self, viewer_key: str) -> int:
        """Get priority for a specific viewer.

        Args:
            viewer_key: Key of the viewer.

        Returns:
            Priority value (lower is higher priority).
        """
        preferences = self._config.get("viewer_preferences", {})
        return int(preferences.get(viewer_key, {}).get("priority", 999))

    def set_viewer_priority(self, viewer_key: str, priority: int) -> None:
        """Set priority for a specific viewer.

        Args:
            viewer_key: Key of the viewer.
            priority: Priority value (lower is higher priority).
        """
        if "viewer_preferences" not in self._config:
            self._config["viewer_preferences"] = {}

        if viewer_key not in self._config["viewer_preferences"]:
            self._config["viewer_preferences"][viewer_key] = {}

        self._config["viewer_preferences"][viewer_key]["priority"] = priority
        self._save_config()

    def get_all_settings(self) -> dict[str, Any]:
        """Get all configuration settings.

        Returns:
            Dictionary containing all configuration settings.
        """
        return self._config.copy()

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        if self.config_path.exists():
            self.config_path.unlink()
        self._create_default_config()


# Global configuration instance
_viewer_config: ViewerConfig | None = None


def get_viewer_config() -> ViewerConfig:
    """Get the global viewer configuration instance.

    Returns:
        ViewerConfig instance for managing viewer preferences.
    """
    global _viewer_config
    if _viewer_config is None:
        _viewer_config = ViewerConfig()
    return _viewer_config


def reset_viewer_config() -> None:
    """Reset the global viewer configuration to defaults."""
    global _viewer_config
    _viewer_config = None
    config = get_viewer_config()
    config.reset_to_defaults()
