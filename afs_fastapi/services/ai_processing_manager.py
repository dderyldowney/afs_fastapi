#!/usr/bin/env python3
"""
AI Processing Manager for AFS FastAPI Platform Integration.

Provides centralized management and integration of AI processing pipeline
capabilities across the agricultural robotics platform. Handles configuration,
lifecycle management, and cross-service coordination.

Agricultural Context:
Manages token optimization and AI processing for safety-critical agricultural
operations, ensuring compliance with ISO 11783 and ISO 18497 standards
while optimizing communication efficiency across multi-tractor fleets.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .ai_processing_pipeline import AIProcessingPipeline, OptimizationLevel, PipelineResult


class AIProcessingManager:
    """
    Platform-wide AI Processing Pipeline Manager.

    Provides centralized access to AI processing capabilities with
    configuration management, service integration, and agricultural
    compliance monitoring.
    """

    def __init__(self, project_root: Path | None = None, config_path: Path | None = None):
        """Initialize AI Processing Manager with platform integration."""
        self.project_root = project_root or Path.cwd()
        self.config_path = config_path or (
            self.project_root / ".claude" / "ai_processing_config.json"
        )

        # Load configuration
        self.config = self._load_configuration()

        # Initialize core pipeline
        self.pipeline = AIProcessingPipeline(project_root=self.project_root)

        # Platform integration settings
        self.agricultural_safety_mode = self.config.get("agricultural_safety_mode", True)
        self.default_optimization_level = OptimizationLevel(
            self.config.get("default_optimization_level", "standard")
        )
        self.token_budget = self.config.get("token_budget", 4000)

        # Service integration tracking
        self._registered_services: dict[str, dict[str, Any]] = {}
        self._processing_stats: dict[str, Any] = {
            "total_requests": 0,
            "tokens_saved": 0,
            "agricultural_requests": 0,
            "safety_critical_requests": 0,
        }

    def _load_configuration(self) -> dict[str, Any]:
        """Load AI processing configuration from platform settings."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                pass

        # Default configuration for agricultural robotics platform
        return {
            "agricultural_safety_mode": True,
            "default_optimization_level": "standard",
            "token_budget": 4000,
            "enable_metrics_tracking": True,
            "safety_keyword_protection": True,
            "services": {
                "equipment": {"optimization_level": "conservative", "priority": "high"},
                "monitoring": {"optimization_level": "standard", "priority": "medium"},
                "fleet": {"optimization_level": "aggressive", "priority": "medium"},
            },
        }

    def register_service(
        self,
        service_name: str,
        optimization_level: OptimizationLevel = OptimizationLevel.STANDARD,
        priority: str = "medium",
    ) -> None:
        """Register a platform service for AI processing integration."""
        self._registered_services[service_name] = {
            "optimization_level": optimization_level,
            "priority": priority,
            "requests_processed": 0,
            "tokens_saved": 0,
        }

    def process_agricultural_request(
        self,
        user_input: str,
        service_name: str = "platform",
        optimization_level: OptimizationLevel | None = None,
        context_data: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """
        Process agricultural robotics request with AI optimization.

        Args:
            user_input: Input text to process (commands, queries, data)
            service_name: Calling service for tracking and configuration
            optimization_level: Override default optimization level
            context_data: Additional context for processing

        Returns:
            PipelineResult with optimized output and metrics
        """
        # Update processing statistics
        self._processing_stats["total_requests"] += 1

        # Determine optimization level
        if optimization_level is None:
            if service_name in self._registered_services:
                optimization_level = self._registered_services[service_name]["optimization_level"]
            else:
                optimization_level = self.default_optimization_level

        # Check for agricultural and safety keywords
        is_agricultural = self._is_agricultural_request(user_input)
        is_safety_critical = self._is_safety_critical_request(user_input)

        if is_agricultural:
            self._processing_stats["agricultural_requests"] += 1
        if is_safety_critical:
            self._processing_stats["safety_critical_requests"] += 1
            # Use conservative optimization for safety-critical requests
            optimization_level = OptimizationLevel.CONSERVATIVE

        # Process through AI pipeline
        result = self.pipeline.process_complete_pipeline(user_input, optimization_level)

        # Update service statistics
        if service_name in self._registered_services:
            service_stats = self._registered_services[service_name]
            service_stats["requests_processed"] += 1
            service_stats["tokens_saved"] += result.total_tokens_saved

        # Update global statistics
        self._processing_stats["tokens_saved"] += result.total_tokens_saved

        return result

    def process_with_budget_constraint(
        self, user_input: str, token_budget: int, service_name: str = "platform"
    ) -> PipelineResult:
        """Process request within specified token budget constraints."""
        self._processing_stats["total_requests"] += 1

        result = self.pipeline.process_with_budget(user_input, token_budget)

        # Update statistics
        self._processing_stats["tokens_saved"] += result.total_tokens_saved
        if service_name in self._registered_services:
            service_stats = self._registered_services[service_name]
            service_stats["requests_processed"] += 1
            service_stats["tokens_saved"] += result.total_tokens_saved

        return result

    def optimize_equipment_communication(self, message: str) -> PipelineResult:
        """Optimize equipment communication messages (ISOBUS, safety protocols)."""
        # Equipment communication requires conservative optimization for safety
        return self.process_agricultural_request(
            message, service_name="equipment", optimization_level=OptimizationLevel.CONSERVATIVE
        )

    def optimize_monitoring_data(self, sensor_data: str) -> PipelineResult:
        """Optimize monitoring data processing (soil, water quality readings)."""
        # Monitoring data can use standard optimization
        return self.process_agricultural_request(
            sensor_data, service_name="monitoring", optimization_level=OptimizationLevel.STANDARD
        )

    def optimize_fleet_coordination(self, coordination_message: str) -> PipelineResult:
        """Optimize fleet coordination messages and commands."""
        # Fleet coordination can use aggressive optimization for routine operations
        return self.process_agricultural_request(
            coordination_message,
            service_name="fleet",
            optimization_level=OptimizationLevel.AGGRESSIVE,
        )

    def _is_agricultural_request(self, user_input: str) -> bool:
        """Check if request contains agricultural robotics keywords."""
        agricultural_keywords = [
            "tractor",
            "equipment",
            "farm",
            "agricultural",
            "crop",
            "soil",
            "irrigation",
            "harvest",
            "planting",
            "field",
            "cultivation",
        ]
        return any(keyword in user_input.lower() for keyword in agricultural_keywords)

    def _is_safety_critical_request(self, user_input: str) -> bool:
        """Check if request involves safety-critical operations."""
        safety_keywords = [
            "emergency",
            "stop",
            "safety",
            "critical",
            "fault",
            "collision",
            "iso",
            "compliance",
            "alert",
            "warning",
            "malfunction",
        ]
        return any(keyword in user_input.lower() for keyword in safety_keywords)

    def get_platform_statistics(self) -> dict[str, Any]:
        """Get comprehensive platform AI processing statistics."""
        return {
            "global_stats": self._processing_stats.copy(),
            "service_stats": self._registered_services.copy(),
            "configuration": {
                "agricultural_safety_mode": self.agricultural_safety_mode,
                "default_optimization_level": self.default_optimization_level.value,
                "token_budget": self.token_budget,
            },
            "pipeline_health": {
                "total_services_registered": len(self._registered_services),
                "agricultural_request_ratio": (
                    self._processing_stats["agricultural_requests"]
                    / max(1, self._processing_stats["total_requests"])
                ),
                "average_tokens_saved": (
                    self._processing_stats["tokens_saved"]
                    / max(1, self._processing_stats["total_requests"])
                ),
            },
        }

    def save_configuration(self) -> None:
        """Save current configuration to platform settings."""
        config_to_save = {
            "agricultural_safety_mode": self.agricultural_safety_mode,
            "default_optimization_level": self.default_optimization_level.value,
            "token_budget": self.token_budget,
            "enable_metrics_tracking": True,
            "safety_keyword_protection": True,
            "services": {},
        }

        # Add service configurations
        for service_name, service_data in self._registered_services.items():
            config_to_save["services"][service_name] = {
                "optimization_level": service_data["optimization_level"].value,
                "priority": service_data["priority"],
            }

        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w") as f:
            json.dump(config_to_save, f, indent=2)

    def health_check(self) -> dict[str, Any]:
        """Perform AI processing pipeline health check."""
        try:
            # Test basic pipeline functionality
            test_result = self.pipeline.process_complete_pipeline(
                "health check test", OptimizationLevel.CONSERVATIVE
            )

            return {
                "status": "healthy",
                "pipeline_operational": True,
                "services_registered": len(self._registered_services),
                "total_requests_processed": self._processing_stats["total_requests"],
                "test_processing_success": test_result.optimization_applied,
                "agricultural_safety_mode": self.agricultural_safety_mode,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "pipeline_operational": False,
                "error": str(e),
                "agricultural_safety_mode": self.agricultural_safety_mode,
            }


# Global AI Processing Manager instance for platform-wide access
ai_processing_manager = AIProcessingManager()
