
import unittest
from unittest.mock import mock_open, patch

from afs_fastapi.todos.manager import Link, Metadata, Node, get_active_items, load_todos


class TestTodosManager(unittest.TestCase):

    @patch("os.listdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_todos(self, mock_yaml_load, mock_open_file, mock_listdir):
        """Test that load_todos correctly loads and parses YAML files."""
        # Arrange
        mock_listdir.side_effect = [
            ["goals", "phases"],
            ["goal1.yaml"],
            ["phase1.yaml"],
        ]
        mock_yaml_load.side_effect = [
            {
                "id": "goal1",
                "layer": "Goal",
                "title": "Test Goal",
                "description": "A test goal",
                "links": {"parents": [], "children": ["phase1"]},
                "metadata": {"owner": "test"},
                "status": "in_progress",
            },
            {
                "id": "phase1",
                "layer": "Phase",
                "title": "Test Phase",
                "description": "A test phase",
                "links": {"parents": ["goal1"], "children": []},
                "metadata": {"owner": "test"},
            },
        ]

        # Act
        todos = load_todos()

        # Assert
        self.assertIn("goals", todos)
        self.assertIn("phases", todos)
        self.assertEqual(len(todos["goals"]), 1)
        self.assertEqual(len(todos["phases"]), 1)

        goal = todos["goals"][0]
        self.assertIsInstance(goal, Node)
        self.assertEqual(goal.id, "goal1")
        self.assertEqual(goal.status, "in_progress")

        phase = todos["phases"][0]
        self.assertIsInstance(phase, Node)
        self.assertEqual(phase.id, "phase1")
        self.assertEqual(phase.status, "planned")

    def test_get_active_items(self):
        """Test that get_active_items correctly identifies active items."""
        # Arrange
        todos = {
            "goals": [
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
            "phases": [
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
        self.assertIn("goals", active_items)
        self.assertNotIn("phases", active_items)
        self.assertEqual(active_items["goals"].id, "goal1")

if __name__ == "__main__":
    unittest.main()
