"""
This module is responsible for managing the ToDoWrite database.
"""

import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent / "todos.db"

def create_connection():
    """Create a database connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
    except sqlite3.Error as e:
        print(e)
    return conn

def create_tables(conn):
    """Create the tables in the database."""
    try:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                layer TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                owner TEXT,
                severity TEXT,
                work_type TEXT
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS links (
                parent_id TEXT NOT NULL,
                child_id TEXT NOT NULL,
                PRIMARY KEY (parent_id, child_id),
                FOREIGN KEY (parent_id) REFERENCES nodes(id),
                FOREIGN KEY (child_id) REFERENCES nodes(id)
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS labels (
                label TEXT PRIMARY KEY
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS node_labels (
                node_id TEXT NOT NULL,
                label TEXT NOT NULL,
                PRIMARY KEY (node_id, label),
                FOREIGN KEY (node_id) REFERENCES nodes(id),
                FOREIGN KEY (label) REFERENCES labels(label)
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS commands (
                node_id TEXT PRIMARY KEY,
                ac_ref TEXT NOT NULL,
                run TEXT NOT NULL,
                FOREIGN KEY (node_id) REFERENCES nodes(id)
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                command_id TEXT NOT NULL,
                artifact TEXT NOT NULL,
                PRIMARY KEY (command_id, artifact),
                FOREIGN KEY (command_id) REFERENCES commands(node_id)
            );
        """)
    except sqlite3.Error as e:
        print(e)

# The main function should only be called when the script is executed directly.
# This prevents the tables from being created when the script is imported.
if __name__ == "__main__":
    """Main function to create the database and tables."""
    conn = create_connection()
    if conn is not None:
        create_tables(conn)
        conn.close()
    else:
        print("Error! cannot create the database connection.")