"""
This module contains the configuration for the database connection.

Supports both SQLite (default) and PostgreSQL databases through environment variables.
"""

import os

# Database configuration with environment variable support
DATABASE_URL = os.getenv("TODOWRITE_DATABASE_URL", "sqlite:///ToDoWrite/todos.db")
"""The URL for the database connection.

Environment Variables:
    TODOWRITE_DATABASE_URL: Full database URL (overrides default SQLite)

Examples:
    SQLite (default): sqlite:///./todos.db
    PostgreSQL: postgresql://user:password@localhost:5432/todowrite_db
    PostgreSQL (production): postgresql://user:password@db.example.com:5432/afs_agricultural_todos
"""


# PostgreSQL configuration helpers
def get_postgresql_url(
    user: str,
    password: str,
    host: str = "localhost",
    port: int = 5432,
    database: str = "todowrite_agricultural",
) -> str:
    """
    Generate PostgreSQL connection URL for agricultural robotics environments.

    Args:
        user: Database username
        password: Database password
        host: Database host (default: localhost)
        port: Database port (default: 5432)
        database: Database name (default: todowrite_agricultural)

    Returns:
        PostgreSQL connection URL string
    """
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


# Database type detection
def is_sqlite() -> bool:
    """Check if current configuration uses SQLite."""
    return DATABASE_URL.startswith("sqlite:")


def is_postgresql() -> bool:
    """Check if current configuration uses PostgreSQL."""
    return DATABASE_URL.startswith("postgresql:")


# Agricultural robotics specific database settings
AGRICULTURAL_DB_SETTINGS = {
    "sqlite": {
        "pool_pre_ping": True,
        "echo": False,  # Set to True for SQL debugging
    },
    "postgresql": {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 3600,  # 1 hour for long-running agricultural operations
        "echo": False,  # Set to True for SQL debugging
    },
}
