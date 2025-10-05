#!/usr/bin/env python3
"""
Example: AI Processing Integration with Agricultural Services.

Demonstrates how existing agricultural services can integrate with the
AI Processing Pipeline for token optimization while maintaining safety
compliance and ISO standards.

Agricultural Context:
Shows practical integration patterns for farm equipment communication,
sensor data processing, and fleet coordination with AI optimization.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from afs_fastapi.equipment.farm_tractors import FarmTractor
from afs_fastapi.services import agricultural_ai


def demonstrate_tractor_ai_integration():
    """Demonstrate AI integration with farm tractor operations."""
    print("🚜 Farm Tractor AI Integration Demo")
    print("=" * 50)

    # Create a farm tractor
    tractor = FarmTractor("John Deere", "8RX 410", 2023)
    tractor.start_engine()
    tractor.set_gps_position(42.3601, -71.0589)  # Boston coordinates for demo

    print(f"Created tractor: {tractor.device_name}")
    print()

    # Example 1: Optimize tractor status communication
    print("Example 1: Tractor Status Communication")
    print("-" * 40)

    status_message = f"Tractor {tractor.device_name} operational status: Engine running at {tractor.engine_rpm} RPM, Speed {tractor.speed} mph, Fuel {tractor.fuel_level}%, GPS position {tractor.gps_latitude:.4f},{tractor.gps_longitude:.4f}, Auto-steer {'enabled' if tractor.auto_steer_enabled else 'disabled'}"

    optimized_status = agricultural_ai.optimize_tractor_communication(
        tractor_id=tractor.device_name,
        message=status_message,
        message_type="status",
        is_safety_critical=False,
    )

    print(f"Original: {optimized_status['original_message'][:100]}...")
    print(f"Optimized: {optimized_status['optimized_message']}")
    print(f"Tokens Saved: {optimized_status['tokens_saved']}")
    print(f"Agricultural Compliance: {optimized_status['agricultural_compliance']}")
    print()

    # Example 2: Safety-critical ISOBUS message
    print("Example 2: Safety-Critical ISOBUS Communication")
    print("-" * 50)

    emergency_data = "Emergency stop initiated due to obstacle detection - immediate halt required for safety compliance per ISO 18497 Performance Level D requirements"

    optimized_isobus = agricultural_ai.optimize_isobus_message(
        pgn=0xFE49,  # Emergency message PGN
        source_address=tractor.isobus_address,
        data_payload=emergency_data,
        is_emergency=True,
    )

    print(f"PGN: {optimized_isobus['pgn']:04X}")
    print(f"Original: {optimized_isobus['original_payload']}")
    print(f"Optimized: {optimized_isobus['optimized_payload']}")
    print(f"ISO 11783 Compliant: {optimized_isobus['iso_11783_compliant']}")
    print(f"Emergency Handling: {optimized_isobus['emergency_handled']}")
    print()


def demonstrate_sensor_ai_integration():
    """Demonstrate AI integration with agricultural sensor data."""
    print("📊 Agricultural Sensor AI Integration Demo")
    print("=" * 50)

    # Example: Soil sensor data optimization
    soil_reading = "Soil moisture content 34.2% at 6-inch depth, pH level 6.8 suitable for corn cultivation, nitrogen content 120 ppm indicating moderate fertility, phosphorus 45 ppm adequate, potassium 180 ppm good, temperature 22.1°C optimal for root development, organic matter 3.2% indicating healthy soil structure"

    optimized_sensor = agricultural_ai.optimize_sensor_data_processing(
        sensor_id="SOIL_001",
        sensor_type="soil_quality",
        reading_data=soil_reading,
        field_context="Field A-7 prepared for corn planting, irrigation system active",
    )

    print(f"Sensor: {optimized_sensor['sensor_id']} ({optimized_sensor['sensor_type']})")
    print(f"Original: {optimized_sensor['original_data'][:100]}...")
    print(f"Optimized: {optimized_sensor['optimized_analysis']}")
    print(f"Tokens Saved: {optimized_sensor['tokens_saved']}")
    print(f"Agricultural Context Preserved: {optimized_sensor['agricultural_context_preserved']}")
    print(f"Processing Efficiency: {optimized_sensor['processing_efficiency']:.2%}")
    print()


def demonstrate_fleet_ai_integration():
    """Demonstrate AI integration with fleet coordination."""
    print("🚁 Fleet Coordination AI Integration Demo")
    print("=" * 50)

    # Example: Multi-tractor coordination message
    coordination_msg = "Coordinate cultivation operation across field sectors A1 through A5 with three tractors working in parallel formation, maintaining 30-foot spacing between units, synchronized speed of 8 mph, implement depth set to 6 inches, GPS waypoint navigation active, collision avoidance systems enabled, field boundary detection operational, ensure complete coverage with 2-foot overlap between passes"

    tractors = ["JD_8RX_001", "JD_8RX_002", "JD_8RX_003"]
    field_assignments = {
        "JD_8RX_001": "Sector_A1-A2",
        "JD_8RX_002": "Sector_A3-A4",
        "JD_8RX_003": "Sector_A5",
    }

    optimized_fleet = agricultural_ai.optimize_fleet_coordination(
        coordinator_id="FLEET_CONTROL_01",
        tractors=tractors,
        operation_type="cultivation",
        coordination_message=coordination_msg,
        field_assignments=field_assignments,
    )

    print(f"Fleet Coordinator: {optimized_fleet['coordinator_id']}")
    print(f"Tractors: {optimized_fleet['tractor_count']} units")
    print(f"Operation: {optimized_fleet['operation_type']}")
    print(f"Original: {optimized_fleet['original_coordination'][:100]}...")
    print(f"Optimized: {optimized_fleet['optimized_coordination']}")
    print(f"Tokens Saved: {optimized_fleet['tokens_saved']}")
    print(f"Multi-tractor Sync: {optimized_fleet['multi_tractor_sync']}")
    print(f"Field Allocation: {optimized_fleet['field_allocation_included']}")
    print()


def demonstrate_safety_protocol_ai_integration():
    """Demonstrate AI integration with safety protocols."""
    print("⚠️  Safety Protocol AI Integration Demo")
    print("=" * 50)

    # Example: Emergency stop protocol message
    safety_msg = "Initiate emergency stop protocol immediately due to collision detection system activation - obstacle detected at 15-meter range requiring immediate cessation of all autonomous operations and manual control restoration with operator notification and safety system status verification before operation resumption"

    optimized_safety = agricultural_ai.optimize_safety_protocol_message(
        protocol_type="emergency_stop",
        safety_message=safety_msg,
        iso_standard="ISO_18497",
        emergency_level="critical",
    )

    print(f"Protocol: {optimized_safety['protocol_type']}")
    print(f"ISO Standard: {optimized_safety['iso_standard']}")
    print(f"Emergency Level: {optimized_safety['emergency_level']}")
    print(f"Original: {optimized_safety['original_message'][:100]}...")
    print(f"Optimized: {optimized_safety['optimized_message']}")
    print(f"Tokens Saved: {optimized_safety['tokens_saved']}")
    print(f"Safety Compliance: {optimized_safety['safety_compliance_maintained']}")
    print(f"ISO Standards Preserved: {optimized_safety['iso_standards_preserved']}")
    print()


def display_integration_statistics():
    """Display comprehensive integration statistics."""
    print("📈 AI Integration Statistics")
    print("=" * 50)

    stats = agricultural_ai.get_integration_statistics()

    print("Integration Metrics:")
    for metric, value in stats["integration_metrics"].items():
        print(f"  • {metric.replace('_', ' ').title()}: {value}")

    print("\nAgricultural Compliance:")
    compliance = stats["agricultural_compliance"]
    print(f"  • ISO Compliance Rate: {compliance['iso_compliance_rate']:.1%}")
    print(f"  • Safety Preservation Rate: {compliance['safety_preservation_rate']:.1%}")

    print("\nService Performance:")
    for service, health in stats["service_performance"].items():
        print(
            f"  • {service.replace('_', ' ').title()}: {health['status']} (Score: {health['health_score']:.2f})"
        )

    print()


def demonstrate_health_check():
    """Demonstrate AI integration health check."""
    print("🏥 AI Integration Health Check")
    print("=" * 50)

    health = agricultural_ai.health_check()

    print(f"Integration Status: {health['integration_status'].upper()}")
    print(f"AI Processing Operational: {health['ai_processing_operational']}")
    print(f"Services Integrated: {health['services_integrated']}")
    print(f"Total Optimizations: {health['total_optimizations']}")
    print(f"Agricultural Compliance Active: {health['agricultural_compliance_active']}")
    print(f"ISO Standards Enforced: {health['iso_standards_enforced']}")
    print(f"Safety Critical Handling: {health['safety_critical_handling']}")

    print("\nService Registrations:")
    for service, config in health["service_registrations"].items():
        print(f"  • {service.title()}: {config.replace('_', ' ').title()}")

    print()


def main():
    """Run all AI integration demonstrations."""
    print("🤖 AFS FastAPI AI Processing Integration Examples")
    print("=" * 60)
    print("Demonstrating AI optimization for agricultural robotics platform")
    print("with safety compliance and ISO standards preservation.")
    print()

    # Run all demonstrations
    demonstrate_tractor_ai_integration()
    demonstrate_sensor_ai_integration()
    demonstrate_fleet_ai_integration()
    demonstrate_safety_protocol_ai_integration()
    display_integration_statistics()
    demonstrate_health_check()

    print("✅ AI Integration Demo Complete!")
    print("The AI Processing Pipeline is successfully integrated with")
    print("agricultural services while maintaining safety and compliance.")


if __name__ == "__main__":
    main()
