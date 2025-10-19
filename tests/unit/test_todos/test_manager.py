import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from afs_fastapi.todos.db.models import Base, Label as DBLabel, Link as DBLink, Node as DBNode
from afs_fastapi.todos.db.repository import NodeRepository
from afs_fastapi.todos.manager import Link, Metadata, Node, get_active_items, load_todos


class TestTodosManager(unittest.TestCase):

    def setUp(self):
        """Set up an in-memory SQLite database for testing."""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.repository = NodeRepository(self.session)

        # Insert test data
        node1 = DBNode(
            id="goal1",
            layer="Goal",
            title="Test Goal",
            description="A test goal",
            status="in_progress",
            owner="test",
            severity="high",
            work_type="architecture",
        )
        node2 = DBNode(
            id="phase1",
            layer="Phase",
            title="Test Phase",
            description="A test phase",
            status="planned",
            owner="test",
            severity="medium",
            work_type="implementation",
        )
        link = DBLink(parent_id="goal1", child_id="phase1")
        label = DBLabel(label="test")
        node1.labels.append(label)

        self.session.add_all([node1, node2, link, label])
        self.session.commit()

    def tearDown(self):
        """Close the database connection."""
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_load_todos(self):
        """Test that load_todos correctly loads data from the database."""
        # Arrange
        # The setUp method has already inserted the test data

        # Act
        with patch("afs_fastapi.todos.manager.SessionLocal") as mock_session_local:
            mock_session_local.return_value = self.session
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

    def test_create_node_missing_fields(self):
        """Test that create_node raises ValueError for missing required fields."""
        node_data = {
            "layer": "Goal",
            "title": "Test Goal",
            "description": "A test goal",
            "links": {},
            "metadata": {},
        }
        with self.assertRaisesRegex(ValueError, "Missing required field: id"):
            self.repository.create(node_data)

    def test_update_node_invalid_data_type(self):
        """Test that update_node raises ValueError for invalid data types."""
        node_data = {"layer": 123}  # Invalid type for layer
        with self.assertRaisesRegex(ValueError, "Layer must be a string"):
            self.repository.update_node_by_id("goal1", node_data)


if __name__ == "__main__":
    unittest.main()
