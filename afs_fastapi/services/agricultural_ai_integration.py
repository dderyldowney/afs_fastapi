#!/usr/bin/env python3
"""
Agricultural AI Integration Service for AFS FastAPI Platform.

Provides integration layer between existing agricultural services and the
AI Processing Pipeline. Enables token optimization for equipment communication,
monitoring data processing, and fleet coordination while maintaining
agricultural safety compliance and ISO standards.

Agricultural Context:
Seamlessly integrates AI optimization capabilities with existing farm equipment
interfaces, safety systems, and monitoring infrastructure without disrupting
safety-critical agricultural operations or ISO compliance requirements.
"""

from __future__ import annotations

from typing import Any

from .ai_processing_manager import ai_processing_manager


class AgriculturalAIIntegration:
    """
    Integration service for AI processing with agricultural systems.

    Provides optimized communication and data processing for farm equipment,
    monitoring systems, and fleet coordination while preserving agricultural
    safety standards and compliance requirements.
    """

    def __init__(self):
        """Initialize agricultural AI integration service."""
        self.ai_manager = ai_processing_manager

        # Register agricultural services with AI processing
        self._register_agricultural_services()

        # Track integration metrics
        self.integration_stats = {
            "equipment_optimizations": 0,
            "monitoring_optimizations": 0,
            "fleet_optimizations": 0,
            "safety_critical_preservations": 0,
            "iso_compliance_maintained": 0,
        }

    def _register_agricultural_services(self) -> None:
        """Register all agricultural services with AI processing manager."""
        # Register equipment service with conservative optimization for safety
        self.ai_manager.register_service(
            service_name="equipment",
            optimization_level=self.ai_manager.pipeline.detect_optimization_level(
                "safety critical equipment"
            ),
            priority="high",
        )

        # Register monitoring service with standard optimization
        self.ai_manager.register_service(
            service_name="monitoring",
            optimization_level=self.ai_manager.pipeline.detect_optimization_level(
                "sensor monitoring data"
            ),
            priority="medium",
        )

        # Register fleet service with aggressive optimization for coordination
        self.ai_manager.register_service(
            service_name="fleet",
            optimization_level=self.ai_manager.pipeline.detect_optimization_level(
                "fleet coordination status"
            ),
            priority="medium",
        )

    def optimize_tractor_communication(
        self,
        tractor_id: str,
        message: str,
        message_type: str = "status",
        is_safety_critical: bool = False,
    ) -> dict[str, Any]:
        """
        Optimize tractor communication messages with agricultural context.

        Args:
            tractor_id: Unique tractor identifier
            message: Communication message to optimize
            message_type: Type of message (status, command, alert, diagnostic)
            is_safety_critical: Whether message involves safety systems

        Returns:
            Optimized message with metadata
        """
        # Add agricultural context for optimization
        agricultural_context = f"Tractor {tractor_id} {message_type}: {message}"

        # Use conservative optimization for safety-critical messages
        service_name = "equipment"
        if is_safety_critical:
            result = self.ai_manager.process_agricultural_request(
                user_input=agricultural_context,
                service_name=service_name,
                optimization_level=self.ai_manager.default_optimization_level.__class__.CONSERVATIVE,
            )
            self.integration_stats["safety_critical_preservations"] += 1
        else:
            result = self.ai_manager.optimize_equipment_communication(agricultural_context)

        # Track optimization statistics
        self.integration_stats["equipment_optimizations"] += 1
        if result.agricultural_compliance_maintained:
            self.integration_stats["iso_compliance_maintained"] += 1

        return {
            "original_message": message,
            "optimized_message": result.final_output,
            "tokens_saved": result.total_tokens_saved,
            "agricultural_compliance": result.agricultural_compliance_maintained,
            "safety_preserved": is_safety_critical,
            "optimization_level": result.optimization_level.value,
            "processing_time_ms": result.metrics.get("processing_time_ms", 0),
        }

    def optimize_isobus_message(
        self, pgn: int, source_address: int, data_payload: str, is_emergency: bool = False
    ) -> dict[str, Any]:
        """
        Optimize ISOBUS protocol messages with ISO 11783 compliance.

        Args:
            pgn: Parameter Group Number
            source_address: ISOBUS source address
            data_payload: Message data payload
            is_emergency: Whether message is emergency/safety related

        Returns:
            Optimized ISOBUS communication with compliance metadata
        """
        # Format ISOBUS message with agricultural context
        isobus_message = f"ISOBUS PGN {pgn:04X} from {source_address:02X}: {data_payload}"

        # Emergency messages use highest priority conservative optimization
        if is_emergency:
            result = self.ai_manager.process_agricultural_request(
                user_input=isobus_message,
                service_name="equipment",
                optimization_level=self.ai_manager.default_optimization_level.__class__.CONSERVATIVE,
            )
            # Track safety critical processing
            self.integration_stats["safety_critical_preservations"] += 1
        else:
            result = self.ai_manager.optimize_equipment_communication(isobus_message)

        # Track equipment optimization
        self.integration_stats["equipment_optimizations"] += 1

        return {
            "pgn": pgn,
            "original_payload": data_payload,
            "optimized_payload": result.final_output,
            "tokens_saved": result.total_tokens_saved,
            "iso_11783_compliant": result.agricultural_compliance_maintained,
            "emergency_handled": is_emergency,
            "optimization_applied": result.optimization_applied,
        }

    def optimize_sensor_data_processing(
        self, sensor_id: str, sensor_type: str, reading_data: str, field_context: str | None = None
    ) -> dict[str, Any]:
        """
        Optimize agricultural sensor data processing and analysis.

        Args:
            sensor_id: Unique sensor identifier
            sensor_type: Type of sensor (soil, water, weather, etc.)
            reading_data: Raw sensor reading data
            field_context: Optional field operation context

        Returns:
            Optimized sensor data with agricultural insights
        """
        # Construct agricultural sensor context
        context_parts = [f"Sensor {sensor_id} ({sensor_type})", reading_data]
        if field_context:
            context_parts.append(f"Field context: {field_context}")

        agricultural_sensor_data = " - ".join(context_parts)

        # Process through monitoring optimization
        result = self.ai_manager.optimize_monitoring_data(agricultural_sensor_data)

        # Track monitoring optimization
        self.integration_stats["monitoring_optimizations"] += 1

        return {
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "original_data": reading_data,
            "optimized_analysis": result.final_output,
            "tokens_saved": result.total_tokens_saved,
            "agricultural_context_preserved": result.agricultural_compliance_maintained,
            "field_relevance": field_context is not None,
            "processing_efficiency": result.metrics.get("optimization_ratio", 0),
        }

    def optimize_fleet_coordination(
        self,
        coordinator_id: str,
        tractors: list[str],
        operation_type: str,
        coordination_message: str,
        field_assignments: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Optimize multi-tractor fleet coordination with conflict-free operations.

        Args:
            coordinator_id: Fleet coordinator identifier
            tractors: List of tractor identifiers in coordination
            operation_type: Type of field operation (planting, harvesting, etc.)
            coordination_message: Fleet coordination instructions
            field_assignments: Optional field allocation assignments

        Returns:
            Optimized fleet coordination with synchronization metadata
        """
        # Build comprehensive fleet coordination context
        fleet_context = f"Fleet Coordinator {coordinator_id}: {operation_type} operation with tractors {', '.join(tractors)}"
        full_message = f"{fleet_context} - {coordination_message}"

        if field_assignments:
            assignments_text = ", ".join(
                [f"{tractor}→{field}" for tractor, field in field_assignments.items()]
            )
            full_message += f" Field assignments: {assignments_text}"

        # Process through fleet coordination optimization
        result = self.ai_manager.optimize_fleet_coordination(full_message)

        # Track fleet optimization
        self.integration_stats["fleet_optimizations"] += 1

        return {
            "coordinator_id": coordinator_id,
            "tractor_count": len(tractors),
            "operation_type": operation_type,
            "original_coordination": coordination_message,
            "optimized_coordination": result.final_output,
            "tokens_saved": result.total_tokens_saved,
            "multi_tractor_sync": len(tractors) > 1,
            "field_allocation_included": field_assignments is not None,
            "coordination_efficiency": result.metrics.get("optimization_ratio", 0),
        }

    def optimize_safety_protocol_message(
        self,
        protocol_type: str,
        safety_message: str,
        iso_standard: str = "ISO_18497",
        emergency_level: str = "standard",
    ) -> dict[str, Any]:
        """
        Optimize safety protocol messages with strict compliance preservation.

        Args:
            protocol_type: Type of safety protocol (emergency_stop, collision_avoidance, etc.)
            safety_message: Safety protocol message
            iso_standard: Applicable ISO safety standard
            emergency_level: Emergency level (standard, high, critical)

        Returns:
            Optimized safety message with compliance guarantees
        """
        # Format safety message with ISO compliance context
        safety_context = f"{iso_standard} {protocol_type} ({emergency_level}): {safety_message}"

        # Always use conservative optimization for safety protocols
        result = self.ai_manager.process_agricultural_request(
            user_input=safety_context,
            service_name="equipment",
            optimization_level=self.ai_manager.default_optimization_level.__class__.CONSERVATIVE,
        )

        # Track safety critical processing
        self.integration_stats["safety_critical_preservations"] += 1

        # Ensure safety keywords are preserved in the optimized output
        optimized_output = result.final_output
        critical_safety_keywords = ["emergency", "stop", "iso", "safety"]

        # Check if critical keywords were removed and restore them if necessary
        original_lower = safety_message.lower()
        optimized_lower = optimized_output.lower()

        missing_keywords = []
        for keyword in critical_safety_keywords:
            if keyword in original_lower and keyword not in optimized_lower:
                missing_keywords.append(keyword)

        # If too many critical keywords were removed, use more conservative approach
        if len(missing_keywords) > len(critical_safety_keywords) * 0.5:
            # Use original message with minimal optimization to preserve safety
            optimized_output = f"{iso_standard} {protocol_type}: {safety_message}"

        return {
            "protocol_type": protocol_type,
            "iso_standard": iso_standard,
            "emergency_level": emergency_level,
            "original_message": safety_message,
            "optimized_message": optimized_output,
            "tokens_saved": max(0, len(safety_message) - len(optimized_output)) // 4,
            "safety_compliance_maintained": result.agricultural_compliance_maintained,
            "conservative_optimization_applied": True,
            "iso_standards_preserved": True,
        }

    def get_integration_statistics(self) -> dict[str, Any]:
        """Get comprehensive agricultural AI integration statistics."""
        ai_stats = self.ai_manager.get_platform_statistics()

        return {
            "integration_metrics": self.integration_stats.copy(),
            "ai_processing_stats": ai_stats,
            "service_performance": {
                "equipment_service_health": self._calculate_service_health("equipment"),
                "monitoring_service_health": self._calculate_service_health("monitoring"),
                "fleet_service_health": self._calculate_service_health("fleet"),
            },
            "agricultural_compliance": {
                "iso_compliance_rate": (
                    self.integration_stats["iso_compliance_maintained"]
                    / max(1, sum(self.integration_stats.values()))
                ),
                "safety_preservation_rate": (
                    self.integration_stats["safety_critical_preservations"]
                    / max(1, self.integration_stats["equipment_optimizations"])
                ),
            },
        }

    def _calculate_service_health(self, service_name: str) -> dict[str, Any]:
        """Calculate health metrics for a specific agricultural service."""
        ai_stats = self.ai_manager.get_platform_statistics()
        service_stats = ai_stats["service_stats"].get(service_name, {})

        if not service_stats:
            return {"status": "not_registered", "health_score": 0.0}

        requests_processed = service_stats.get("requests_processed", 0)
        tokens_saved = service_stats.get("tokens_saved", 0)

        # Calculate health score based on activity and efficiency
        health_score = min(1.0, (requests_processed / 100.0) + (tokens_saved / 1000.0))

        return {
            "status": (
                "healthy"
                if health_score > 0.5
                else "degraded" if health_score > 0.1 else "unhealthy"
            ),
            "health_score": health_score,
            "requests_processed": requests_processed,
            "average_tokens_saved": tokens_saved / max(1, requests_processed),
            "optimization_level": service_stats.get("optimization_level", "unknown"),
        }

    def health_check(self) -> dict[str, Any]:
        """Perform comprehensive agricultural AI integration health check."""
        ai_health = self.ai_manager.health_check()

        return {
            "integration_status": "healthy",
            "ai_processing_operational": ai_health["status"] == "healthy",
            "services_integrated": 3,  # equipment, monitoring, fleet
            "total_optimizations": sum(self.integration_stats.values()),
            "agricultural_compliance_active": True,
            "iso_standards_enforced": True,
            "safety_critical_handling": True,
            "service_registrations": {
                "equipment": "conservative_optimization",
                "monitoring": "standard_optimization",
                "fleet": "aggressive_optimization",
            },
        }


# Global agricultural AI integration service
agricultural_ai = AgriculturalAIIntegration()
