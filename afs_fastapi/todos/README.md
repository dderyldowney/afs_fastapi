# ToDoWrite Module

This module contains the ToDoWrite system. The data is now stored in a local SQLite database, with support for PostgreSQL.

## Database

The database interaction is managed using SQLAlchemy ORM. Schema migrations are handled by Alembic.

- **Configuration:** `db/config.py` contains the database connection URL.
- **Models:** `db/models.py` defines the SQLAlchemy models for the ToDoWrite data.
- **Repository:** `db/repository.py` implements the repository pattern for data access, including CRUD operations and data validation.
- **Migrations:** Alembic is configured for schema migrations.

## Manager

The `manager.py` script provides functions for accessing and managing the ToDoWrite data, utilizing the repository for database interactions.