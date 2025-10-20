#!/usr/bin/env python3
"""
TodoWrite Traceability Tool
Builds forward/backward traceability matrix and dependency graph
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import yaml


class TraceabilityNode:
    """Represents a node in the traceability graph."""

    def __init__(self, node_id: str, layer: str, title: str, file_path: Path) -> None:
        self.id = node_id
        self.layer = layer
        self.title = title
        self.file_path = file_path
        self.parents: set[str] = set()
        self.children: set[str] = set()
        self.metadata: dict[str, Any] = {}

    def add_parent(self, parent_id: str) -> None:
        """Add a parent relationship."""
        self.parents.add(parent_id)

    def add_child(self, child_id: str) -> None:
        """Add a child relationship."""
        self.children.add(child_id)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "layer": self.layer,
            "title": self.title,
            "file_path": str(self.file_path),
            "parents": list(self.parents),
            "children": list(self.children),
            "metadata": self.metadata,
        }


class TraceabilityBuilder:
    """Builds traceability matrix and dependency graph."""

    def __init__(self) -> None:
        self.nodes: dict[str, TraceabilityNode] = {}
        self.orphan_nodes: set[str] = set()
        self.missing_references: set[str] = set()

    def load_plans(self, plans_dir: Path) -> None:
        """Load all YAML files from plans directory."""
        if not plans_dir.exists():
            print(f"❌ Plans directory does not exist: {plans_dir}")
            return

        # Find all YAML files
        yaml_files: list[Path] = []
        for pattern in ["*.yaml", "*.yml"]:
            yaml_files.extend(plans_dir.rglob(pattern))

        print(f"🔍 Loading {len(yaml_files)} YAML files...")

        for yaml_file in yaml_files:
            self._load_yaml_file(yaml_file)

        print(f"📊 Loaded {len(self.nodes)} nodes")

    def _load_yaml_file(self, file_path: Path) -> None:
        """Load a single YAML file and extract node information."""
        try:
            with open(file_path) as f:
                yaml_data = yaml.safe_load(f)

            if not yaml_data:
                return

            # Extract required fields
            node_id = yaml_data.get("id")
            layer = yaml_data.get("layer")
            title = yaml_data.get("title", "")

            if not node_id or not layer:
                print(f"⚠️  Skipping {file_path}: missing id or layer")
                return

            # Create node
            node = TraceabilityNode(node_id, layer, title, file_path)

            # Extract metadata
            if "metadata" in yaml_data:
                node.metadata = yaml_data["metadata"]

            # Extract links
            links = yaml_data.get("links", {})
            for parent_id in links.get("parents", []):
                node.add_parent(parent_id)

            for child_id in links.get("children", []):
                node.add_child(child_id)

            # Store node
            self.nodes[node_id] = node

        except Exception as e:
            print(f"❌ Error loading {file_path}: {e}")

    def build_traceability_matrix(self) -> list[dict[str, Any]]:
        """Build the traceability matrix."""
        matrix = []

        for node in self.nodes.values():
            # Forward traceability (this node to children)
            if node.children:
                for child_id in node.children:
                    matrix.append(
                        {
                            "from_id": node.id,
                            "from_layer": node.layer,
                            "from_title": node.title,
                            "to_id": child_id,
                            "to_layer": self.nodes.get(
                                child_id, TraceabilityNode("", "", "", Path(""))
                            ).layer,
                            "to_title": self.nodes.get(
                                child_id, TraceabilityNode("", "", "", Path(""))
                            ).title,
                            "relationship": "parent_to_child",
                            "valid": child_id in self.nodes,
                        }
                    )
            else:
                # Leaf node
                matrix.append(
                    {
                        "from_id": node.id,
                        "from_layer": node.layer,
                        "from_title": node.title,
                        "to_id": "",
                        "to_layer": "",
                        "to_title": "",
                        "relationship": "leaf",
                        "valid": True,
                    }
                )

            # Backward traceability (parents to this node)
            if node.parents:
                for parent_id in node.parents:
                    if parent_id not in [m["from_id"] for m in matrix if m["to_id"] == node.id]:
                        matrix.append(
                            {
                                "from_id": parent_id,
                                "from_layer": self.nodes.get(
                                    parent_id, TraceabilityNode("", "", "", Path(""))
                                ).layer,
                                "from_title": self.nodes.get(
                                    parent_id, TraceabilityNode("", "", "", Path(""))
                                ).title,
                                "to_id": node.id,
                                "to_layer": node.layer,
                                "to_title": node.title,
                                "relationship": "child_to_parent",
                                "valid": parent_id in self.nodes,
                            }
                        )
            elif not any(node.id in n.children for n in self.nodes.values()):
                # Orphan node (no parents and not referenced as child)
                self.orphan_nodes.add(node.id)

        return matrix

    def build_dependency_graph(self) -> dict[str, Any]:
        """Build the dependency graph."""
        edges = []
        node_data = {}

        for node in self.nodes.values():
            # Add node data
            node_data[node.id] = {
                "layer": node.layer,
                "title": node.title,
                "file_path": str(node.file_path),
                "metadata": node.metadata,
            }

            # Add edges for parent-child relationships
            for child_id in node.children:
                edges.append({"from": node.id, "to": child_id, "type": "parent_child"})

        return {
            "nodes": node_data,
            "edges": edges,
            "statistics": {
                "total_nodes": len(self.nodes),
                "total_edges": len(edges),
                "orphan_nodes": list(self.orphan_nodes),
                "missing_references": list(self.missing_references),
            },
        }

    def validate_traceability(self) -> list[str]:
        """Validate traceability and return issues."""
        issues = []

        # Check for missing references
        all_referenced_ids = set()
        for node in self.nodes.values():
            all_referenced_ids.update(node.parents)
            all_referenced_ids.update(node.children)

        missing_refs = all_referenced_ids - set(self.nodes.keys())
        for missing_ref in missing_refs:
            issues.append(f"Missing reference: {missing_ref}")
            self.missing_references.add(missing_ref)

        # Check for cycles
        cycles = self._detect_cycles()
        for cycle in cycles:
            issues.append(f"Circular dependency: {' -> '.join(cycle)}")

        # Check for orphan nodes
        for orphan in self.orphan_nodes:
            issues.append(f"Orphan node (no parents, not referenced): {orphan}")

        return issues

    def _detect_cycles(self) -> list[list[str]]:
        """Detect circular dependencies using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node_id: str, path: list[str]) -> None:
            if node_id in rec_stack:
                # Found a cycle
                cycle_start = path.index(node_id)
                cycle = path[cycle_start:] + [node_id]
                cycles.append(cycle)
                return

            if node_id in visited:
                return

            visited.add(node_id)
            rec_stack.add(node_id)

            # Visit children
            if node_id in self.nodes:
                for child_id in self.nodes[node_id].children:
                    dfs(child_id, path + [node_id])

            rec_stack.remove(node_id)

        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id, [])

        return cycles

    def write_csv_matrix(self, output_path: Path, matrix: list[dict[str, Any]]) -> None:
        """Write traceability matrix to CSV file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="") as f:
            if matrix:
                writer = csv.DictWriter(f, fieldnames=matrix[0].keys())
                writer.writeheader()
                writer.writerows(matrix)

        print(f"📄 Traceability matrix written to {output_path}")

    def write_graph_json(self, output_path: Path, graph: dict[str, Any]) -> None:
        """Write dependency graph to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(graph, f, indent=2)

        print(f"📊 Dependency graph written to {output_path}")


def main() -> None:
    """Main traceability function."""
    parser = argparse.ArgumentParser(
        description="Build TodoWrite traceability matrix and dependency graph"
    )
    parser.add_argument(
        "--plans",
        type=Path,
        default=Path("plans"),
        help="Plans directory containing YAML files (default: plans)",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=Path("trace/trace.csv"),
        help="Output CSV file for traceability matrix (default: trace/trace.csv)",
    )
    parser.add_argument(
        "--out-graph",
        type=Path,
        default=Path("trace/graph.json"),
        help="Output JSON file for dependency graph (default: trace/graph.json)",
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate traceability and report issues"
    )

    args = parser.parse_args()

    # Build traceability
    builder = TraceabilityBuilder()
    builder.load_plans(args.plans)

    # Build matrix and graph
    matrix = builder.build_traceability_matrix()
    graph = builder.build_dependency_graph()

    # Write outputs
    builder.write_csv_matrix(args.out_csv, matrix)
    builder.write_graph_json(args.out_graph, graph)

    # Validate if requested
    if args.validate:
        issues = builder.validate_traceability()
        if issues:
            print(f"\n⚠️  Traceability Issues ({len(issues)}):")
            for issue in issues:
                print(f"   ❌ {issue}")
            sys.exit(1)
        else:
            print("\n✅ Traceability validation passed!")

    # Print summary
    print("\n📊 Traceability Summary:")
    print(f"   Nodes: {len(builder.nodes)}")
    print(f"   Matrix entries: {len(matrix)}")
    print(f"   Graph edges: {len(graph['edges'])}")
    if builder.orphan_nodes:
        print(f"   Orphan nodes: {len(builder.orphan_nodes)}")
    if builder.missing_references:
        print(f"   Missing references: {len(builder.missing_references)}")


if __name__ == "__main__":
    main()
