"""TodoWrite configuration module for AFS FastAPI.

This module provides centralized TodoWrite configuration following the
preferred database order: PostgreSQL → SQLite3 → YAML files.

Agricultural Context:
Ensures consistent task management configuration across all agricultural
robotics components, with reliable database persistence for safety-critical
agricultural operations and graceful fallback to file-based storage.
"""

from __future__ import annotations

import os

from todowrite import ToDoWrite
from todowrite.database import StoragePreference


def get_todowrite_database_url() -> str | None:
    """Get TodoWrite database URL from environment variables.

    Checks environment variables in order of preference:
    1. TODOWRITE_DATABASE_URL (TodoWrite-specific)
    2. DATABASE_URL (general database URL)
    3. TODOWRITE_SQLITE_URL (SQLite fallback)

    Returns
    -------
    Optional[str]
        Database URL if configured, None for YAML fallback

    Agricultural Context:
    Provides flexible database configuration for different agricultural
    deployment environments (development, testing, production).
    """
    # Check for PostgreSQL configuration (highest preference)
    postgres_url = os.getenv("TODOWRITE_DATABASE_URL") or os.getenv("DATABASE_URL")
    if postgres_url and postgres_url.startswith("postgresql"):
        return postgres_url

    # Check for SQLite configuration (medium preference)
    sqlite_url = os.getenv("TODOWRITE_SQLITE_URL")
    if sqlite_url:
        return sqlite_url

    # Default SQLite for development
    return "sqlite:///todowrite.db"


def get_storage_preference() -> StoragePreference:
    """Get TodoWrite storage preference from environment.

    Returns
    -------
    StoragePreference
        Storage preference enum value

    Agricultural Context:
    Allows override of storage preference for specific agricultural
    deployment scenarios (e.g., YAML_ONLY for air-gapped systems).
    """
    preference_str = os.getenv("TODOWRITE_STORAGE_PREFERENCE", "AUTO").upper()

    preference_map = {
        "AUTO": StoragePreference.AUTO,
        "POSTGRESQL_ONLY": StoragePreference.POSTGRESQL_ONLY,
        "SQLITE_ONLY": StoragePreference.SQLITE_ONLY,
        "YAML_ONLY": StoragePreference.YAML_ONLY,
    }

    return preference_map.get(preference_str, StoragePreference.AUTO)


def create_todowrite_app(
    auto_import: bool = True,
    db_url: str | None = None,
    storage_preference: StoragePreference | None = None,
) -> ToDoWrite:
    """Create configured TodoWrite application instance.

    Parameters
    ----------
    auto_import : bool, default True
        Whether to automatically import existing data
    db_url : Optional[str], default None
        Override database URL (uses environment if None)
    storage_preference : Optional[StoragePreference], default None
        Override storage preference (uses environment if None)

    Returns
    -------
    ToDoWrite
        Configured TodoWrite application instance

    Agricultural Context:
    Creates TodoWrite instances with consistent configuration for
    agricultural robotics task management, ensuring reliable persistence
    and graceful fallback across different deployment environments.
    """
    if db_url is None:
        db_url = get_todowrite_database_url()

    if storage_preference is None:
        storage_preference = get_storage_preference()

    return ToDoWrite(
        db_url=db_url,
        auto_import=auto_import,
        storage_preference=storage_preference,
    )


def get_todowrite_status() -> dict[str, str]:
    """Get TodoWrite configuration status information.

    Returns
    -------
    dict[str, str]
        Configuration status information

    Agricultural Context:
    Provides diagnostic information for agricultural system administrators
    to verify TodoWrite configuration and troubleshoot issues.
    """
    db_url = get_todowrite_database_url()
    storage_pref = get_storage_preference()

    # Determine database type
    if db_url:
        if db_url.startswith("postgresql"):
            db_type = "PostgreSQL"
        elif db_url.startswith("sqlite"):
            db_type = "SQLite3"
        else:
            db_type = "Unknown"
    else:
        db_type = "YAML Files"

    return {
        "database_url": db_url or "Not configured",
        "database_type": db_type,
        "storage_preference": storage_pref.name,
        "auto_import": "Enabled",
        "configuration_source": "Environment variables",
    }


# Global TodoWrite instance for API and scripts
# This ensures consistent configuration across the application
_todowrite_app: ToDoWrite | None = None


def get_global_todowrite_app() -> ToDoWrite:
    """Get global TodoWrite application instance.

    Returns
    -------
    ToDoWrite
        Global TodoWrite application instance

    Agricultural Context:
    Provides singleton TodoWrite instance for consistent task management
    across all agricultural robotics components and API endpoints.
    """
    global _todowrite_app

    if _todowrite_app is None:
        _todowrite_app = create_todowrite_app()

    return _todowrite_app


def reset_global_todowrite_app() -> None:
    """Reset global TodoWrite application instance.

    Used for testing and configuration changes.

    Agricultural Context:
    Allows reconfiguration of TodoWrite instance during agricultural
    system maintenance or testing scenarios.
    """
    global _todowrite_app
    _todowrite_app = None
