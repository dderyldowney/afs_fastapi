
import sqlite3
import unittest
from unittest.mock import patch

from afs_fastapi.todos.database import create_tables
from afs_fastapi.todos.manager import Link, Metadata, Node, get_active_items, load_todos


class TestTodosManager(unittest.TestCase):

    def setUp(self):
        """Set up an in-memory SQLite database for testing."""
        self.conn = sqlite3.connect(":memory:")
        create_tables(self.conn)
        self.c = self.conn.cursor()

        # Insert test data
        self.c.execute("INSERT INTO nodes VALUES ('goal1', 'Goal', 'Test Goal', 'A test goal', 'in_progress', 'test', 'high', 'architecture')")
        self.c.execute("INSERT INTO nodes VALUES ('phase1', 'Phase', 'Test Phase', 'A test phase', 'planned', 'test', 'medium', 'implementation')")
        self.c.execute("INSERT INTO links VALUES ('goal1', 'phase1')")
        self.c.execute("INSERT INTO labels VALUES ('goal1', 'test')")
        self.conn.commit()

    def tearDown(self):
        """Close the database connection."""
        self.conn.close()

    def test_load_todos(self):
        """Test that load_todos correctly loads data from the database."""
        # Arrange
        # The setUp method has already inserted the test data

        # Act
        with patch('afs_fastapi.todos.manager.create_connection') as mock_create_connection:
            mock_create_connection.return_value = self.conn
            todos = load_todos()

        # Assert
        self.assertIn("Goal", todos)
        self.assertIn("Phase", todos)
        self.assertEqual(len(todos["Goal"]), 1)
        self.assertEqual(len(todos["Phase"]), 1)

        goal = todos["Goal"][0]
        self.assertIsInstance(goal, Node)
        self.assertEqual(goal.id, "goal1")
        self.assertEqual(goal.status, "in_progress")

        phase = todos["Phase"][0]
        self.assertIsInstance(phase, Node)
        self.assertEqual(phase.id, "phase1")
        self.assertEqual(phase.status, "planned")

    def test_get_active_items(self):
        """Test that get_active_items correctly identifies active items."""
        # Arrange
        todos = {
            "Goal": [
                Node(
                    id="goal1",
                    layer="Goal",
                    title="Test Goal",
                    description="",
                    links=Link(),
                    metadata=Metadata(owner=""),
                    status="in_progress",
                )
            ],
            "Phase": [
                Node(
                    id="phase1",
                    layer="Phase",
                    title="Test Phase",
                    description="",
                    links=Link(),
                    metadata=Metadata(owner=""),
                    status="planned",
                )
            ],
        }

        # Act
        active_items = get_active_items(todos)

        # Assert
        self.assertIn("Goal", active_items)
        self.assertNotIn("Phase", active_items)
        self.assertEqual(active_items["Goal"].id, "goal1")

if __name__ == "__main__":
    unittest.main()
