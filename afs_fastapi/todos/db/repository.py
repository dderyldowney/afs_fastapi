"""
This module implements the repository pattern for accessing the ToDoWrite data.
"""

from typing import Any, TypeVar

from sqlalchemy.orm import Session

from afs_fastapi.todos.db.models import (
    Artifact as DBArtifact,
    Command as DBCommand,
    Label as DBLabel,
    Link as DBLink,
    Node as DBNode,
)

T = TypeVar("T")


class BaseRepository[T]:
    """Base repository class with common CRUD operations."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, obj: T) -> T:
        """Adds a new object to the database."""
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def get(self, model: type[T], id: Any) -> T | None:
        """Retrieves an object by its ID."""
        return self.session.query(model).filter(model.id == id).first()

    def list(self, model: type[T]) -> list[T]:
        """Retrieves all objects of a given type."""
        return self.session.query(model).all()

    def update(self, obj: T) -> T:
        """Updates an existing object in the database."""
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def delete(self, obj: T) -> None:
        """Deletes an object from the database."""
        self.session.delete(obj)
        self.session.commit()


class NodeRepository(BaseRepository[DBNode]):
    """Repository for managing Node objects."""

    def __init__(self, session: Session):
        super().__init__(session)

    def get(self, model: type[DBNode], id: str) -> DBNode | None:
        """Retrieves a Node by its ID."""
        return super().get(model, id)

    def list(self, model: type[DBNode]) -> list[DBNode]:
        """Retrieves all Node objects."""
        return super().list(model)

    def create(self, node_data: dict[str, Any]) -> DBNode:
        """Creates a new Node object in the database."""
        # Data validation
        required_fields = ["id", "layer", "title", "description"]
        for field_name in required_fields:
            if field_name not in node_data:
                raise ValueError(f"Missing required field: {field_name}")

        db_node = DBNode(
            id=node_data["id"],
            layer=node_data["layer"],
            title=node_data["title"],
            description=node_data["description"],
            status=node_data.get("status", "planned"),
            owner=node_data["metadata"].get("owner"),
            severity=node_data["metadata"].get("severity"),
            work_type=node_data["metadata"].get("work_type"),
        )
        self.session.add(db_node)
        self.session.flush()  # Flush to get the node ID for relationships

        for parent_id in node_data["links"].get("parents", []):
            link = DBLink(parent_id=parent_id, child_id=db_node.id)
            self.session.add(link)

        for label_text in node_data["metadata"].get("labels", []):
            label = self.session.query(DBLabel).filter(DBLabel.label == label_text).first()
            if not label:
                label = DBLabel(label=label_text)
                self.session.add(label)
            db_node.labels.append(label)

        if "command" in node_data and node_data["command"]:
            command_data = node_data["command"]
            db_command = DBCommand(
                node_id=db_node.id,
                ac_ref=command_data["ac_ref"],
                run=str(command_data["run"]),
            )
            self.session.add(db_command)
            self.session.flush()

            for artifact_text in command_data.get("artifacts", []):
                artifact = DBArtifact(command_id=db_command.node_id, artifact=artifact_text)
                self.session.add(artifact)

        self.session.commit()
        self.session.refresh(db_node)
        return db_node

    def update_node_by_id(self, node_id: str, node_data: dict[str, Any]) -> DBNode | None:
        """Updates an existing Node object in the database."""
        db_node = self.get(DBNode, node_id)
        if db_node:
            # Data validation
            if "layer" in node_data and not isinstance(node_data["layer"], str):
                raise ValueError("Layer must be a string")
            if "title" in node_data and not isinstance(node_data["title"], str):
                raise ValueError("Title must be a string")
            # ... add more validation as needed

            db_node.layer = node_data.get("layer", db_node.layer)
            db_node.title = node_data.get("title", db_node.title)
            db_node.description = node_data.get("description", db_node.description)
            db_node.status = node_data.get("status", db_node.status)
            db_node.owner = (
                node_data["metadata"].get("owner", db_node.owner)
                if "metadata" in node_data
                else db_node.owner
            )
            db_node.severity = (
                node_data["metadata"].get("severity", db_node.severity)
                if "metadata" in node_data
                else db_node.severity
            )
            db_node.work_type = (
                node_data["metadata"].get("work_type", db_node.work_type)
                if "metadata" in node_data
                else db_node.work_type
            )

            # Update links (this is a simplified update, a full update would involve diffing and adding/removing)
            self.session.query(DBLink).filter(DBLink.child_id == node_id).delete()
            self.session.query(DBLink).filter(DBLink.parent_id == node_id).delete()
            for parent_id in node_data["links"].get("parents", []):
                link = DBLink(parent_id=parent_id, child_id=db_node.id)
                self.session.add(link)
            for child_id in node_data["links"].get("children", []):
                link = DBLink(parent_id=db_node.id, child_id=child_id)
                self.session.add(link)

            # Update labels
            db_node.labels.clear()
            for label_text in node_data["metadata"].get("labels", []):
                label = self.session.query(DBLabel).filter(DBLabel.label == label_text).first()
                if not label:
                    label = DBLabel(label=label_text)
                    self.session.add(label)
                db_node.labels.append(label)

            # Update command
            if "command" in node_data and node_data["command"]:
                db_command = (
                    self.session.query(DBCommand).filter(DBCommand.node_id == node_id).first()
                )
                if not db_command:
                    db_command = DBCommand(node_id=node_id)
                    self.session.add(db_command)
                db_command.ac_ref = node_data["command"].get("ac_ref", db_command.ac_ref)
                db_command.run = str(node_data["command"].get("run", db_command.run))

                self.session.query(DBArtifact).filter(DBArtifact.command_id == node_id).delete()
                for artifact_text in node_data["command"].get("artifacts", []):
                    artifact = DBArtifact(command_id=node_id, artifact=artifact_text)
                    self.session.add(artifact)
            else:
                self.session.query(DBCommand).filter(DBCommand.node_id == node_id).delete()
                self.session.query(DBArtifact).filter(DBArtifact.command_id == node_id).delete()

            return super().update(db_node)
        return None

    def delete_node_by_id(self, node_id: str):
        """Deletes a Node object from the database."""
        db_node = self.get(DBNode, node_id)
        if db_node:
            self.session.delete(db_node)
            self.session.commit()
