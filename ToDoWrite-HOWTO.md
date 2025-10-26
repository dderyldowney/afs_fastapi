# ToDoWrite: Standalone Package & Python Module Usage Guide

> **Complete guide for using ToDoWrite as a standalone package in other projects and as an includable Python module**

## 📋 Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Standalone Package Usage](#standalone-package-usage)
3. [Python Module Integration](#python-module-integration)
4. [CLI Reference](#cli-reference)
5. [Integration Patterns](#integration-patterns)
6. [Project Templates](#project-templates)
7. [API Reference](#api-reference)
8. [Examples & Workflows](#examples--workflows)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Installation & Setup

### Prerequisites

```bash
# Required dependencies
pip install pyyaml jsonschema

# Optional but recommended
pip install rich  # Enhanced CLI output
pip install click  # CLI framework support
```

### Installation Methods

#### Method 1: Standalone Package Installation

```bash
# Install from PyPI (when available)
pip install todowrite

# Or install from source
git clone https://github.com/your-org/todowrite.git
cd todowrite
pip install -e .
```

#### Method 2: Copy Module into Project

```bash
# Copy the todowrite module into your project
cp -r /path/to/afs_fastapi/todowrite ./your_project/
```

#### Method 3: Git Submodule (Recommended for Teams)

```bash
# Add as submodule
git submodule add https://github.com/your-org/todowrite.git vendor/todowrite

# Initialize in new clones
git submodule update --init --recursive
```

---

## Standalone Package Usage

### Quick Start in New Project

#### 1. Initialize ToDoWrite Structure

```bash
# Create project directory
mkdir my-agricultural-project
cd my-agricultural-project

# Initialize git if needed
git init

# Create ToDoWrite structure
mkdir -p ToDoWrite/configs/{plans,commands,schemas}
mkdir -p ToDoWrite/configs/plans/{goals,concepts,contexts,constraints,requirements,acceptance_criteria,interface_contracts,phases,steps,tasks,subtasks}
mkdir -p trace results

# Create basic Makefile with ToDoWrite targets
curl -o Makefile https://raw.githubusercontent.com/your-org/todowrite/main/templates/Makefile.template
```

#### 2. Create Makefile Integration

```make
# Makefile for ToDoWrite integration

# ToDoWrite targets
tw-init:
	@echo "🏗️  Initializing ToDoWrite..."
	@todowrite init --project-dir .
	@echo "✅ ToDoWrite initialized"

tw-validate:
	@echo "✅ Validating ToDoWrite files..."
	@todowrite validate --plans ToDoWrite/configs/plans
	@echo "✅ Validation complete"

tw-trace:
	@echo "🔗 Building traceability..."
	@todowrite trace --plans ToDoWrite/configs/plans --output trace/
	@echo "✅ Traceability complete"

tw-status:
	@todowrite status --plans ToDoWrite/configs/plans

tw-dev: tw-validate tw-trace
	@echo "💻 Development workflow complete"

.PHONY: tw-init tw-validate tw-trace tw-status tw-dev
```

#### 3. Project Configuration

```yaml
# .todowrite.yml - Project configuration
project:
  name: "Agricultural Automation System"
  version: "1.0.0"
  domain: "agriculture"

structure:
  plans_dir: "ToDoWrite/configs/plans"
  commands_dir: "ToDoWrite/configs/commands"
  schemas_dir: "ToDoWrite/configs/schemas"
  trace_dir: "trace"
  results_dir: "results"

validation:
  enforce_soc: true
  require_traceability: true

git:
  hooks: true
  commit_format: "conventional"
```

### Daily Workflow

```bash
# Morning: Check project status
make tw-status

# Create new planning nodes
todowrite create goal --id GOAL-FIELD-OPS --title "Automate field operations"
todowrite create requirement --id R-GPS-001 --parent GOAL-FIELD-OPS

# Validate as you go
make tw-validate

# Build traceability
make tw-trace

# End of day: Full development check
make tw-dev
```

---

## Python Module Integration

### Basic Import and Usage

```python
"""
Example: Using ToDoWrite as a Python module
"""
import todowrite
from todowrite.core import ToDoWriteManager
from todowrite.models import Goal, Requirement, AcceptanceCriteria, Command
from todowrite.validators import SchemaValidator
from todowrite.tracers import TraceabilityBuilder

# Initialize ToDoWrite manager
manager = ToDoWriteManager(
    plans_dir="ToDoWrite/configs/plans",
    commands_dir="ToDoWrite/configs/commands"
)

# Create planning nodes programmatically
goal = Goal(
    id="GOAL-AUTONOMOUS-TRACTORS",
    title="Implement autonomous tractor coordination",
    description="Enable multiple tractors to work fields autonomously",
    metadata={
        "owner": "automation-team",
        "labels": ["autonomous", "tractors", "coordination"],
        "severity": "high",
        "work_type": "architecture"
    }
)

# Save to filesystem
manager.save_node(goal)

# Create child requirement
requirement = Requirement(
    id="R-CAN-COMM-001",
    title="CAN bus communication protocol",
    description="Implement ISO 11783 CAN bus communication",
    parents=[goal.id],
    metadata={
        "owner": "firmware-team",
        "labels": ["can", "iso11783", "communication"],
        "work_type": "spec"
    }
)

manager.save_node(requirement)
```

### Advanced Integration Patterns

#### 1. Custom Domain Models

```python
"""
Agricultural-specific ToDoWrite extensions
"""
from todowrite.core import ToDoWriteManager
from todowrite.models import Goal, Requirement
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class AgriculturalGoal(Goal):
    """Goal with agricultural-specific metadata"""
    crop_types: List[str] = None
    field_size_acres: Optional[float] = None
    equipment_required: List[str] = None

    def __post_init__(self):
        super().__post_init__()
        if self.crop_types:
            self.metadata["crop_types"] = self.crop_types
        if self.field_size_acres:
            self.metadata["field_size_acres"] = self.field_size_acres

@dataclass
class TractorRequirement(Requirement):
    """Requirement for tractor-specific functionality"""
    tractor_models: List[str] = None
    can_bus_speed: Optional[str] = None
    iso_compliance: List[str] = None

    def __post_init__(self):
        super().__post_init__()
        if self.tractor_models:
            self.metadata["tractor_models"] = self.tractor_models
        if self.can_bus_speed:
            self.metadata["can_bus_speed"] = self.can_bus_speed

# Usage
class AgriculturalToDoWriteManager(ToDoWriteManager):
    """Extended manager for agricultural development"""

    def create_field_operation_goal(self, field_name: str, crop_type: str, acres: float) -> AgriculturalGoal:
        goal = AgriculturalGoal(
            id=f"GOAL-FIELD-{field_name.upper()}",
            title=f"Automate {field_name} field operations",
            description=f"Implement autonomous {crop_type} operations for {acres} acre field",
            crop_types=[crop_type],
            field_size_acres=acres,
            equipment_required=["tractor", "implements", "gps"]
        )
        self.save_node(goal)
        return goal

    def create_tractor_communication_requirement(self, parent_goal: str) -> TractorRequirement:
        req = TractorRequirement(
            id="R-TRACTOR-COMM-001",
            title="Tractor CAN bus communication",
            description="Implement reliable CAN bus communication between tractors",
            parents=[parent_goal],
            tractor_models=["John Deere 8R", "Case IH Magnum"],
            can_bus_speed="250kbps",
            iso_compliance=["ISO 11783", "J1939"]
        )
        self.save_node(req)
        return req
```

#### 2. Integration with Existing Systems

```python
"""
Integration with existing project management systems
"""
import todowrite
from todowrite.integrations import JiraIntegration, GitHubIntegration

class ProjectIntegration:
    def __init__(self, project_dir: str):
        self.tw_manager = todowrite.ToDoWriteManager(project_dir)
        self.jira = JiraIntegration(api_key="your-key")
        self.github = GitHubIntegration(token="your-token")

    def sync_requirements_to_jira(self):
        """Sync ToDoWrite requirements to Jira tickets"""
        requirements = self.tw_manager.get_nodes_by_layer("Requirements")

        for req in requirements:
            jira_ticket = self.jira.create_ticket(
                summary=req.title,
                description=req.description,
                labels=req.metadata.get("labels", []),
                epic_link=req.parents[0] if req.parents else None
            )

            # Update ToDoWrite with Jira ticket ID
            req.metadata["jira_ticket"] = jira_ticket.key
            self.tw_manager.save_node(req)

    def create_github_issues_from_tasks(self):
        """Create GitHub issues from ToDoWrite tasks"""
        tasks = self.tw_manager.get_nodes_by_layer("Task")

        for task in tasks:
            issue = self.github.create_issue(
                title=task.title,
                body=task.description,
                labels=task.metadata.get("labels", []),
                assignee=task.metadata.get("owner")
            )

            task.metadata["github_issue"] = issue.number
            self.tw_manager.save_node(task)
```

#### 3. Real-time Validation and Monitoring

```python
"""
Real-time ToDoWrite validation and monitoring
"""
from todowrite.validators import RealtimeValidator
from todowrite.monitors import ProjectMonitor
import watchdog.observers
import watchdog.events

class ToDoWriteWatcher(watchdog.events.FileSystemEventHandler):
    def __init__(self, project_dir: str):
        self.validator = RealtimeValidator(project_dir)
        self.monitor = ProjectMonitor(project_dir)

    def on_modified(self, event):
        if event.is_directory:
            return

        if event.src_path.endswith('.yaml'):
            # Validate changed file
            try:
                self.validator.validate_file(event.src_path)
                print(f"✅ Validated: {event.src_path}")

                # Update traceability
                self.monitor.update_traceability()

            except ValidationError as e:
                print(f"❌ Validation failed: {event.src_path}")
                print(f"   Error: {e}")

# Usage
def start_monitoring(project_dir: str):
    event_handler = ToDoWriteWatcher(project_dir)
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, project_dir, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

---

## CLI Reference

### Core Commands

#### Initialize New Project

```bash
# Initialize ToDoWrite in current directory
todowrite init

# Initialize with specific configuration
todowrite init --project-name "Agricultural Automation" --domain agriculture

# Initialize with custom structure
todowrite init --plans-dir custom/plans --commands-dir custom/commands
```

#### Node Management

```bash
# Create new nodes
todowrite create goal --id GOAL-001 --title "Your goal title"
todowrite create requirement --id R-001 --parent GOAL-001 --title "Requirement title"
todowrite create command --id CMD-001 --parent AC-001 --script "./scripts/test.sh"

# List nodes
todowrite list goals
todowrite list requirements --parent GOAL-001
todowrite list all --format table

# Get node details
todowrite show GOAL-001
todowrite show R-001 --format yaml

# Update nodes
todowrite update R-001 --title "Updated title" --add-label "priority:high"

# Delete nodes (with dependency checking)
todowrite delete CMD-001
todowrite delete R-001 --force  # Skip dependency checks
```

#### Validation and Quality

```bash
# Validate all nodes
todowrite validate

# Validate specific layer
todowrite validate --layer requirements

# Validate with strict mode
todowrite validate --strict

# Check separation of concerns
todowrite lint

# Check traceability
todowrite trace --validate
```

#### Traceability and Reporting

```bash
# Build traceability matrix
todowrite trace --output trace/matrix.csv

# Generate dependency graph
todowrite trace --graph trace/deps.json

# Create reports
todowrite report --type summary
todowrite report --type coverage --layer requirements
todowrite report --type progress --format html
```

#### Integration Commands

```bash
# Git integration
todowrite git hooks install
todowrite git commit-check

# Export/Import
todowrite export --format json --output backup.json
todowrite import --file backup.json --merge

# Template generation
todowrite template --type makefile > Makefile
todowrite template --type gitignore > .gitignore
todowrite template --type config > .todowrite.yml
```

### Advanced CLI Usage

#### Batch Operations

```bash
# Create multiple nodes from CSV
todowrite batch create --file requirements.csv --type requirement

# Bulk updates
todowrite batch update --query "layer:requirement" --set-label "sprint:2"

# Bulk validation
todowrite batch validate --pattern "R-CAN-*"
```

#### Query and Filtering

```bash
# Query by metadata
todowrite query --owner "firmware-team"
todowrite query --label "can" --label "critical"
todowrite query --work-type "implementation"

# Complex queries
todowrite query --filter "metadata.severity == 'high' and 'agriculture' in metadata.labels"

# Get statistics
todowrite stats --layer all
todowrite stats --by-owner
todowrite stats --completion-rate
```

---

## Integration Patterns

### Pattern 1: Microservice Architecture

```python
"""
ToDoWrite in microservice architecture
"""
# requirements-service/main.py
from fastapi import FastAPI
from todowrite import ToDoWriteManager

app = FastAPI()
tw_manager = ToDoWriteManager("/shared/todowrite")

@app.get("/requirements")
async def get_requirements():
    return tw_manager.get_nodes_by_layer("Requirements")

@app.post("/requirements")
async def create_requirement(requirement_data: dict):
    req = tw_manager.create_requirement(**requirement_data)
    return {"id": req.id, "status": "created"}

# traceability-service/main.py
from todowrite.tracers import TraceabilityBuilder

@app.get("/trace/{node_id}")
async def get_trace(node_id: str):
    tracer = TraceabilityBuilder("/shared/todowrite")
    return tracer.get_full_trace(node_id)
```

### Pattern 2: CI/CD Integration

```yaml
# .github/workflows/todowrite-validation.yml
name: ToDoWrite Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install ToDoWrite
      run: pip install todowrite

    - name: Validate ToDoWrite Structure
      run: |
        todowrite validate --strict
        todowrite lint
        todowrite trace --validate

    - name: Generate Reports
      run: |
        todowrite report --type coverage --output reports/coverage.html
        todowrite trace --graph reports/dependencies.json

    - name: Upload Reports
      uses: actions/upload-artifact@v2
      with:
        name: todowrite-reports
        path: reports/
```

### Pattern 3: Development Environment Integration

```python
"""
IDE/Editor integration for ToDoWrite
"""
# vscode-extension/todowrite-provider.py
import vscode
from todowrite import ToDoWriteManager

class ToDoWriteProvider:
    def __init__(self, workspace_path: str):
        self.manager = ToDoWriteManager(workspace_path)

    def provide_completions(self, document, position):
        """Provide autocompletion for ToDoWrite IDs"""
        line = document.lineAt(position).text

        if "parents:" in line or "children:" in line:
            # Return available node IDs
            return [
                vscode.CompletionItem(node.id, vscode.CompletionItemKind.Reference)
                for node in self.manager.get_all_nodes()
            ]

    def provide_hover(self, document, position):
        """Show node details on hover"""
        word = document.getWordRangeAtPosition(position)
        if word and word.text.startswith(('GOAL-', 'R-', 'AC-', 'CMD-')):
            node = self.manager.get_node(word.text)
            if node:
                return vscode.Hover(f"**{node.title}**\n\n{node.description}")
```

---

## Project Templates

### Agricultural Robotics Template

```bash
# Create new agricultural project
todowrite template agricultural-robotics --name "Precision Farming System"
```

Generated structure:
```
precision-farming-system/
├── ToDoWrite/
│   ├── configs/
│   │   ├── plans/
│   │   │   ├── goals/
│   │   │   │   └── GOAL-PRECISION-FARMING.yaml
│   │   │   ├── requirements/
│   │   │   │   ├── R-GPS-001.yaml
│   │   │   │   ├── R-CAN-001.yaml
│   │   │   │   └── R-SENSORS-001.yaml
│   │   │   └── acceptance_criteria/
│   │   │       ├── AC-GPS-001.yaml
│   │   │       └── AC-CAN-001.yaml
│   │   └── commands/
│   │       └── CMD-GPS-TEST.yaml
├── Makefile
├── .todowrite.yml
└── README.md
```

### Example Goal Template

```yaml
# ToDoWrite/configs/plans/goals/GOAL-PRECISION-FARMING.yaml
id: GOAL-PRECISION-FARMING
layer: Goal
title: Implement precision farming automation
description: >
  Develop autonomous farming system with GPS-guided tractors,
  real-time soil monitoring, and variable rate application
  for maximized crop yield and resource efficiency.
metadata:
  owner: precision-ag-team
  labels: [precision-farming, autonomous, gps, sensors]
  severity: high
  work_type: architecture
  domain: agriculture
  estimated_timeline: "6 months"
  budget_category: "research-development"
links:
  parents: []
  children: [R-GPS-001, R-CAN-001, R-SENSORS-001]
```

---

## API Reference

### Core Classes

#### ToDoWriteManager

```python
class ToDoWriteManager:
    """Main interface for ToDoWrite operations"""

    def __init__(self, project_dir: str, config_file: str = None):
        """Initialize manager with project directory"""

    def create_node(self, layer: str, **kwargs) -> Node:
        """Create new node of specified layer"""

    def get_node(self, node_id: str) -> Node:
        """Get node by ID"""

    def get_nodes_by_layer(self, layer: str) -> List[Node]:
        """Get all nodes of specified layer"""

    def save_node(self, node: Node) -> None:
        """Save node to filesystem"""

    def delete_node(self, node_id: str, force: bool = False) -> None:
        """Delete node and handle dependencies"""

    def validate_all(self) -> ValidationResult:
        """Validate entire project structure"""

    def build_traceability(self) -> TraceMatrix:
        """Build complete traceability matrix"""
```

#### Node Models

```python
@dataclass
class Node:
    """Base class for all ToDoWrite nodes"""
    id: str
    layer: str
    title: str
    description: str
    metadata: Dict[str, Any]
    links: Dict[str, List[str]]  # parents, children

@dataclass
class Goal(Node):
    """Strategic goal node"""
    layer: str = "Goal"

@dataclass
class Requirement(Node):
    """Requirement specification node"""
    layer: str = "Requirements"

@dataclass
class Command(Node):
    """Executable command node"""
    layer: str = "Command"
    command: Dict[str, Any]  # ac_ref, run, artifacts
```

### Utility Functions

```python
# Validation utilities
from todowrite.validators import validate_node, validate_hierarchy

# Traceability utilities
from todowrite.tracers import build_trace_matrix, get_ancestry

# Export/Import utilities
from todowrite.io import export_to_json, import_from_json

# Template utilities
from todowrite.templates import create_project_template, get_available_templates
```

---

## Examples & Workflows

### Example 1: Complete Agricultural Project Setup

```python
"""
Complete example: Setting up agricultural automation project
"""
from todowrite import ToDoWriteManager
from todowrite.models import Goal, Requirement, AcceptanceCriteria, Command

# Initialize project
manager = ToDoWriteManager("./precision-farming")

# Create strategic goal
goal = Goal(
    id="GOAL-AUTONOMOUS-HARVEST",
    title="Autonomous Harvesting System",
    description="Develop fully autonomous harvesting with yield monitoring",
    metadata={
        "owner": "autonomy-team",
        "labels": ["autonomous", "harvesting", "yield-monitoring"],
        "severity": "high",
        "work_type": "architecture",
        "timeline": "12 months",
        "budget": "$2M"
    }
)
manager.save_node(goal)

# Create technical requirements
gps_req = Requirement(
    id="R-GPS-001",
    title="High-precision GPS navigation",
    description="Implement RTK GPS with <2cm accuracy for field navigation",
    parents=[goal.id],
    metadata={
        "owner": "navigation-team",
        "labels": ["gps", "rtk", "navigation"],
        "work_type": "spec",
        "priority": "critical"
    }
)
manager.save_node(gps_req)

# Create acceptance criteria
gps_ac = AcceptanceCriteria(
    id="AC-GPS-001",
    title="GPS accuracy validation",
    description="""
    Given RTK GPS system is operational
    When harvester navigates field rows
    Then position accuracy must be <2cm (95th percentile)
    And heading accuracy must be <1 degree
    """,
    parents=[gps_req.id],
    metadata={
        "owner": "test-team",
        "work_type": "validation"
    }
)
manager.save_node(gps_ac)

# Create executable command
gps_test = Command(
    id="CMD-GPS-001",
    title="GPS accuracy test",
    description="Execute GPS accuracy measurement test",
    parents=[gps_ac.id],
    command={
        "ac_ref": gps_ac.id,
        "run": {
            "shell": """
            # Start GPS logging
            gps_logger --output test_data/gps_accuracy.log --duration 3600

            # Run accuracy analysis
            python scripts/analyze_gps_accuracy.py test_data/gps_accuracy.log
            """,
            "workdir": ".",
            "env": {"GPS_PORT": "/dev/ttyUSB0"}
        },
        "artifacts": [
            "test_data/gps_accuracy.log",
            "reports/gps_accuracy_report.json"
        ]
    },
    metadata={
        "owner": "test-team",
        "work_type": "implementation"
    }
)
manager.save_node(gps_test)

# Validate complete hierarchy
validation_result = manager.validate_all()
if validation_result.is_valid:
    print("✅ Project structure is valid")
else:
    print("❌ Validation errors:", validation_result.errors)

# Build traceability
trace_matrix = manager.build_traceability()
print(f"📊 Traceability: {trace_matrix.coverage_percentage:.1f}% coverage")
```

### Example 2: Integration with Testing Framework

```python
"""
Integration with pytest for ToDoWrite command validation
"""
import pytest
from todowrite import ToDoWriteManager
import subprocess
import json

class TestToDoWriteCommands:
    """Test all ToDoWrite commands are executable and valid"""

    @pytest.fixture
    def tw_manager(self):
        return ToDoWriteManager("./test_project")

    def test_all_commands_executable(self, tw_manager):
        """Test that all commands can be executed"""
        commands = tw_manager.get_nodes_by_layer("Command")

        for cmd in commands:
            # Validate command structure
            assert "command" in cmd.__dict__
            assert "run" in cmd.command
            assert "shell" in cmd.command["run"]

            # Test command execution (dry run)
            shell_script = cmd.command["run"]["shell"]
            try:
                result = subprocess.run(
                    ["bash", "-n", "-c", shell_script],
                    capture_output=True,
                    text=True
                )
                assert result.returncode == 0, f"Command {cmd.id} has syntax errors"
            except Exception as e:
                pytest.fail(f"Command {cmd.id} validation failed: {e}")

    def test_traceability_complete(self, tw_manager):
        """Test that all commands trace back to requirements"""
        commands = tw_manager.get_nodes_by_layer("Command")

        for cmd in commands:
            # Check that command has valid parent chain
            ancestry = tw_manager.get_ancestry(cmd.id)

            # Should trace back to at least acceptance criteria
            has_ac_parent = any(
                node.layer == "AcceptanceCriteria"
                for node in ancestry
            )
            assert has_ac_parent, f"Command {cmd.id} missing AC parent"

            # Should ultimately trace to goal
            has_goal_ancestor = any(
                node.layer == "Goal"
                for node in ancestry
            )
            assert has_goal_ancestor, f"Command {cmd.id} missing Goal ancestor"
```

---

## Best Practices

### 1. Project Organization

```bash
# Recommended project structure
my-project/
├── ToDoWrite/                 # ToDoWrite files
│   ├── configs/
│   │   ├── plans/            # Layers 1-11 (declarative)
│   │   ├── commands/         # Layer 12 (executable)
│   │   └── schemas/          # Validation schemas
├── src/                      # Source code
├── tests/                    # Test files
├── scripts/                  # Utility scripts
├── docs/                     # Documentation
├── Makefile                  # Build automation
├── .todowrite.yml           # ToDoWrite configuration
└── README.md
```

### 2. Naming Conventions

```yaml
# Node ID conventions
goals: "GOAL-{PROJECT}-{ASPECT}"          # GOAL-FARMING-AUTOMATION
concepts: "CON-{ARCHITECTURE}-{PATTERN}"  # CON-MICROSERVICE-FLEET
requirements: "R-{DOMAIN}-{NUMBER}"       # R-CAN-001
acceptance_criteria: "AC-{REQ_ID}"        # AC-CAN-001
commands: "CMD-{FUNCTION}-{NUMBER}"       # CMD-GPS-TEST-001

# File naming
{layer}/{id}.yaml                         # requirements/R-CAN-001.yaml
```

### 3. Metadata Standards

```yaml
# Standard metadata fields
metadata:
  owner: "team-name"           # Responsible team
  labels: ["domain", "type"]   # Categorization tags
  severity: "high|med|low"     # Priority level
  work_type: "architecture|spec|implementation|validation|docs"
  estimated_effort: "2w"      # Time estimate
  dependencies: ["R-GPS-001"] # External dependencies
  status: "planning|active|complete|blocked"
```

### 4. Validation Rules

```python
# Custom validation rules
from todowrite.validators import CustomValidator

class AgriculturalValidator(CustomValidator):
    def validate_goal(self, goal):
        """Agricultural-specific goal validation"""
        required_labels = ["agriculture", "safety"]

        if not any(label in goal.metadata.get("labels", [])
                  for label in required_labels):
            self.add_error(f"Goal {goal.id} missing required agricultural labels")

        if goal.metadata.get("severity") != "high":
            self.add_warning(f"Agricultural goals should typically be high severity")

    def validate_requirement(self, req):
        """Requirement validation for safety-critical systems"""
        if "safety" in req.metadata.get("labels", []):
            if not req.metadata.get("safety_standard"):
                self.add_error(f"Safety requirement {req.id} missing safety_standard")
```

---

## Troubleshooting

### Common Issues

#### 1. Module Import Errors

```bash
# Error: ModuleNotFoundError: No module named 'todowrite'
# Solution: Check installation
pip list | grep todowrite
pip install -e /path/to/todowrite

# For development installs
export PYTHONPATH="${PYTHONPATH}:/path/to/todowrite"
```

#### 2. File Permissions

```bash
# Error: Permission denied when creating files
# Solution: Check directory permissions
chmod -R 755 ToDoWrite/
sudo chown -R $USER:$USER ToDoWrite/
```

#### 3. Validation Failures

```python
# Debug validation errors
from todowrite.validators import validate_node
from todowrite.models import Goal

goal = Goal(id="TEST", title="Test", description="Test")
result = validate_node(goal)

if not result.is_valid:
    for error in result.errors:
        print(f"Validation error: {error}")
```

#### 4. Circular Dependencies

```bash
# Error: Circular dependency detected
# Solution: Use traceability tools to debug
todowrite trace --validate --verbose
todowrite query --circular-deps
```

### Performance Optimization

```python
# For large projects, use caching
from todowrite.cache import NodeCache

manager = ToDoWriteManager(
    project_dir="large_project",
    cache=NodeCache(max_size=1000)
)

# Batch operations for performance
nodes = [create_requirement(...) for i in range(100)]
manager.batch_save(nodes)
```

### Debugging Commands

```bash
# Debug mode for verbose output
todowrite --debug validate
todowrite --verbose trace

# Check internal state
todowrite debug --show-config
todowrite debug --show-cache
todowrite debug --validate-schema
```

---

`★ Insight ─────────────────────────────────────`
- **Dual Usage Patterns**: ToDoWrite excels both as a standalone package for greenfield projects and as an embedded module for existing systems, providing flexibility without sacrificing structure
- **Progressive Integration**: Teams can start with basic CLI usage and gradually adopt Python module integration as their ToDoWrite expertise grows
- **Agricultural Domain Focus**: The examples and patterns emphasize agricultural robotics use cases, demonstrating how the 12-layer hierarchy supports safety-critical agricultural automation development
`─────────────────────────────────────────────────`

This guide provides comprehensive coverage of both standalone package usage and Python module integration, enabling teams to adopt ToDoWrite in the way that best fits their project structure and development workflow.