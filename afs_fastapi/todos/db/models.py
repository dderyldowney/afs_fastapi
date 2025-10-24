"""
This module defines the SQLAlchemy models for the ToDoWrite data.
"""

from typing import Optional

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models using SQLAlchemy 2.0 API."""

    pass


node_labels = Table(
    "node_labels",
    Base.metadata,
    Column("node_id", String, ForeignKey("nodes.id"), primary_key=True),
    Column("label", String, ForeignKey("labels.label"), primary_key=True),
)
"""Association table for Node and Label many-to-many relationship."""


class Node(Base):
    """SQLAlchemy model for a ToDoWrite Node."""

    __tablename__ = "nodes"

    id = Column(String, primary_key=True)
    layer = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, nullable=False)
    owner = Column(String)
    severity = Column(String)
    work_type = Column(String)

    parents: Mapped[list["Node"]] = relationship(
        "Node",
        secondary="links",
        primaryjoin="Node.id==links.c.child_id",
        secondaryjoin="Node.id==links.c.parent_id",
        back_populates="children",
    )
    children: Mapped[list["Node"]] = relationship(
        "Node",
        secondary="links",
        primaryjoin="Node.id==links.c.parent_id",
        secondaryjoin="Node.id==links.c.child_id",
        back_populates="parents",
    )
    labels: Mapped[list["Label"]] = relationship(
        "Label", secondary=node_labels, back_populates="nodes"
    )
    command: Mapped[Optional["Command"]] = relationship(
        "Command", uselist=False, back_populates="node"
    )


class Link(Base):
    """SQLAlchemy model for a link between ToDoWrite Nodes."""

    __tablename__ = "links"

    parent_id = Column(String, ForeignKey("nodes.id"), primary_key=True)
    child_id = Column(String, ForeignKey("nodes.id"), primary_key=True)


class Label(Base):
    """SQLAlchemy model for a ToDoWrite Label."""

    __tablename__ = "labels"

    label = Column(String, primary_key=True)
    nodes: Mapped[list["Node"]] = relationship(
        "Node", secondary=node_labels, back_populates="labels"
    )


class Command(Base):
    """SQLAlchemy model for a ToDoWrite Command."""

    __tablename__ = "commands"

    node_id = Column(String, ForeignKey("nodes.id"), primary_key=True)
    ac_ref = Column(String, nullable=False)
    run = Column(String, nullable=False)

    node: Mapped["Node"] = relationship("Node", back_populates="command")
    artifacts: Mapped[list["Artifact"]] = relationship("Artifact", back_populates="command")


class Artifact(Base):
    """SQLAlchemy model for a Command Artifact."""

    __tablename__ = "artifacts"

    command_id = Column(String, ForeignKey("commands.node_id"), primary_key=True)
    artifact = Column(String, primary_key=True)

    command: Mapped["Command"] = relationship("Command", back_populates="artifacts")
