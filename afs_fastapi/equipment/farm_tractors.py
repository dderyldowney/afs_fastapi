import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Literal

from pydantic import BaseModel

# ==============================================================================
# ISOBUS Communication Interfaces (ISO 11783 Compliance)
# ==============================================================================


@dataclass
class ISOBUSMessage:
    """Standard ISOBUS message structure."""

    pgn: int  # Parameter Group Number
    source_address: int
    destination_address: int
    data: bytes
    timestamp: datetime


class ISOBUSDevice(ABC):
    """Abstract base class for ISOBUS-compatible devices."""

    @abstractmethod
    def get_device_name(self) -> str:
        """Return standardized device name."""
        pass

    @abstractmethod
    def send_message(self, message: ISOBUSMessage) -> bool:
        """Send ISOBUS message."""
        pass

    @abstractmethod
    def receive_message(self) -> ISOBUSMessage | None:
        """Receive ISOBUS message."""
        pass


# ==============================================================================
# Vision & Optical Sensor Interfaces
# ==============================================================================


@dataclass
class CameraConfig:
    """Camera system configuration."""

    resolution: tuple[int, int]  # width, height
    frame_rate: int
    field_of_view: float  # degrees
    exposure_mode: str
    color_space: str


@dataclass
class LiDARPoint:
    """3D point from LiDAR sensor."""

    x: float
    y: float
    z: float
    intensity: float
    timestamp: datetime


class VisionSensorInterface(ABC):
    """Abstract interface for vision sensors."""

    @abstractmethod
    def capture_frame(self) -> bytes | None:
        """Capture a single frame."""
        pass

    @abstractmethod
    def get_point_cloud(self) -> list[LiDARPoint]:
        """Get LiDAR point cloud data."""
        pass

    @abstractmethod
    def detect_obstacles(self, max_distance: float) -> list[tuple[float, float, float]]:
        """Detect obstacles within specified distance."""
        pass


# ==============================================================================
# Safety & Compliance Interfaces (ISO 18497 Series)
# ==============================================================================


class SafetyLevel(str, Enum):
    """ISO 18497 safety levels."""

    PERFORMANCE_LEVEL_C = "PLc"
    PERFORMANCE_LEVEL_D = "PLd"
    PERFORMANCE_LEVEL_E = "PLe"


@dataclass
class SafetyZone:
    """Defined safety zone around equipment."""

    zone_id: str
    boundary_points: list[tuple[float, float]]  # GPS coordinates
    safety_level: SafetyLevel
    max_speed: float  # mph
    detection_required: bool


class SafetySystemInterface(ABC):
    """Abstract interface for ISO 18497 safety systems."""

    @abstractmethod
    def emergency_stop(self) -> bool:
        """Trigger emergency stop per ISO 18497."""
        pass

    @abstractmethod
    def validate_safety_zone(self, position: tuple[float, float]) -> bool:
        """Validate position is within safe operating zone."""
        pass

    @abstractmethod
    def get_safety_status(self) -> dict[str, bool]:
        """Get comprehensive safety system status."""
        pass


# ==============================================================================
# Motor Control & Actuation Interfaces
# ==============================================================================


class MotorType(str, Enum):
    """Types of motor actuators."""

    BRUSHLESS_DC = "bldc"
    SERVO = "servo"
    STEPPER = "stepper"
    LINEAR_ACTUATOR = "linear"
    QDD_ACTUATOR = "qdd"


@dataclass
class MotorCommand:
    """Motor control command structure."""

    motor_id: str
    command_type: str  # position, velocity, torque
    target_value: float
    max_velocity: float | None = None
    max_acceleration: float | None = None


class MotorControlInterface(ABC):
    """Abstract interface for precision motor control."""

    @abstractmethod
    def send_motor_command(self, command: MotorCommand) -> bool:
        """Send command to specific motor."""
        pass

    @abstractmethod
    def get_motor_status(self, motor_id: str) -> dict[str, float]:
        """Get current motor status and position."""
        pass

    @abstractmethod
    def calibrate_motor(self, motor_id: str) -> bool:
        """Perform motor calibration sequence."""
        pass


# ==============================================================================
# Data Management & Connectivity Interfaces
# ==============================================================================


@dataclass
class TaskData:
    """ISO XML task data structure."""

    task_id: str
    field_id: str
    operation_type: str
    prescription_map: dict[str, float] | None
    start_time: datetime
    end_time: datetime | None = None


class DataManagementInterface(ABC):
    """Abstract interface for agricultural data management."""

    @abstractmethod
    def export_iso_xml(self, task_data: TaskData) -> str:
        """Export data in ISO XML format."""
        pass

    @abstractmethod
    def import_prescription_map(self, map_data: bytes) -> dict[str, float]:
        """Import variable rate prescription map."""
        pass

    @abstractmethod
    def log_operation_data(self, data_point: dict[str, float]) -> bool:
        """Log operational data point."""
        pass


# ==============================================================================
# Power & Energy Management Interfaces
# ==============================================================================


@dataclass
class PowerSource:
    """Power source configuration."""

    source_type: str  # solar, fuel_cell, battery, grid
    voltage: float
    max_current: float
    efficiency: float


class PowerManagementInterface(ABC):
    """Abstract interface for power system management."""

    @abstractmethod
    def get_power_status(self) -> dict[str, float]:
        """Get comprehensive power system status."""
        pass

    @abstractmethod
    def set_power_priority(self, device_priorities: dict[str, int]) -> bool:
        """Set power allocation priorities."""
        pass

    @abstractmethod
    def enable_regenerative_mode(self) -> bool:
        """Enable energy recovery from motion."""
        pass


class ImplementPosition(str, Enum):
    """Implement position states."""

    RAISED = "raised"
    LOWERED = "lowered"
    TRANSPORT = "transport"


class FieldMode(str, Enum):
    """Field operation modes."""

    TRANSPORT = "transport"
    TILLAGE = "tillage"
    PLANTING = "planting"
    SPRAYING = "spraying"
    HARVESTING = "harvesting"
    MAINTENANCE = "maintenance"


class FarmTractorResponse(BaseModel):
    """
    Representation of a tractor state suitable for API responses.

    Parameters
    ----------
    make : str
        Manufacturer name.
    model : str
        Model name.
    year : int
        Year of manufacture.
    manual_url : str | None, optional
        URL to the operator's manual, by default None.
    engine_on : bool
        Whether the engine is currently running.
    speed : int
        Current speed in mph.
    gear : int
        Current gear (0–10).
    power_takeoff : bool
        Whether the PTO is engaged.
    hydraulics : bool
        Whether hydraulics are activated.
    gps_latitude : float | None
        Current GPS latitude coordinate.
    gps_longitude : float | None
        Current GPS longitude coordinate.
    auto_steer_enabled : bool
        Whether auto-steer is active.
    implement_position : str
        Current implement position (raised/lowered/transport).
    field_mode : str
        Current field operation mode.
    waypoint_count : int
        Number of navigation waypoints.
    current_heading : float
        Current heading in degrees.
    implement_depth : float
        Working depth in inches.
    implement_width : float
        Working width in feet.
    work_rate : float
        Work rate in acres/hour.
    area_covered : float
        Total area covered in acres.
    engine_temp : float
        Engine temperature in Fahrenheit.
    hydraulic_flow : float
        Hydraulic flow in GPM.
    wheel_slip : float
        Wheel slip percentage.
    ground_speed : float
        Ground speed in mph.
    draft_load : float
        Draft load in pounds.
    autonomous_mode : bool
        Whether autonomous mode is enabled.
    obstacle_detection : bool
        Whether obstacle detection is active.
    emergency_stop_active : bool
        Whether emergency stop is active.
    isobus_address : int
        ISOBUS device address.
    device_name : str
        ISOBUS device name.
    safety_system_active : bool
        Whether safety system is active.
    safety_level : str
        Current safety performance level.
    regenerative_mode : bool
        Whether regenerative power mode is enabled.
    lidar_enabled : bool
        Whether LiDAR sensors are enabled.
    obstacle_count : int
        Number of detected obstacles.
    """

    tractor_id: str | None = None
    make: str
    model: str
    year: int
    manual_url: str | None = None
    engine_on: bool
    speed: int
    gear: int
    power_takeoff: bool
    hydraulics: bool
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    auto_steer_enabled: bool = False
    implement_position: Literal["raised", "lowered", "transport"] = "raised"
    field_mode: Literal[
        "transport", "tillage", "planting", "spraying", "harvesting", "maintenance"
    ] = "transport"
    fuel_level: float = 100.0
    engine_rpm: int = 0
    hydraulic_pressure: float = 0.0

    # Enhanced fields for robotic interfaces
    waypoint_count: int = 0
    current_heading: float = 0.0
    implement_depth: float = 0.0
    implement_width: float = 0.0
    work_rate: float = 0.0
    area_covered: float = 0.0
    engine_temp: float = 180.0
    hydraulic_flow: float = 0.0
    wheel_slip: float = 0.0
    ground_speed: float = 0.0
    draft_load: float = 0.0
    autonomous_mode: bool = False
    obstacle_detection: bool = True
    emergency_stop_active: bool = False
    isobus_address: int = 0x80
    device_name: str = ""
    safety_system_active: bool = True
    safety_level: Literal["PLc", "PLd", "PLe"] = "PLc"
    regenerative_mode: bool = False
    lidar_enabled: bool = False
    obstacle_count: int = 0

    status: str


class FarmTractor(
    ISOBUSDevice,
    SafetySystemInterface,
    MotorControlInterface,
    DataManagementInterface,
    PowerManagementInterface,
):
    """
    A class representing a farm tractor with various functionalities,
    such as engine control, gear changes, and hydraulic systems.
    """

    # Logger for safety-critical agricultural operations
    logger: ClassVar[logging.Logger] = logging.getLogger("afs_fastapi.equipment.farm_tractors")

    MAX_SPEED: ClassVar[int] = 40  # Maximum speed limit for the tractor.
    MIN_GEAR: ClassVar[int] = 0  # Minimum gear value (e.g., reverse support can be added here).
    MAX_GEAR: ClassVar[int] = 10  # Maximum gear value.

    def __init__(self, make: str, model: str, year: int, manual_url: str | None = None) -> None:
        """
        Initializes a FarmTractor instance.

        Args:
            make (str): The manufacturer of the tractor.
            model (str): The model of the tractor.
            year (int): The manufacturing year of the tractor.
            manual_url (str | None): Optional URL for accessing the tractor's manual.
        """
        self.make: str = make
        self.model: str = model
        self.year: int = year
        self.manual_url: str | None = manual_url
        self.engine_on: bool = False
        self.speed: int = 0
        self.gear: int = 0
        self.power_takeoff: bool = False
        self.hydraulics: bool = False

        # GPS and Navigation
        self.gps_latitude: float | None = None
        self.gps_longitude: float | None = None
        self.auto_steer_enabled: bool = False
        self.waypoints: list[tuple[float, float]] = []
        self.current_heading: float = 0.0  # degrees

        # Implement Controls
        self.implement_position: ImplementPosition = ImplementPosition.RAISED
        self.implement_depth: float = 0.0  # inches
        self.implement_width: float = 0.0  # feet

        # Field Operations
        self.field_mode: FieldMode = FieldMode.TRANSPORT
        self.work_rate: float = 0.0  # acres/hour
        self.area_covered: float = 0.0  # acres

        # Engine and Fuel
        self.fuel_level: float = 100.0  # percentage
        self.engine_rpm: int = 0
        self.engine_temp: float = 180.0  # fahrenheit

        # Hydraulics
        self.hydraulic_pressure: float = 0.0  # psi
        self.hydraulic_flow: float = 0.0  # gpm

        # Sensors
        self.wheel_slip: float = 0.0  # percentage
        self.ground_speed: float = 0.0  # mph
        self.draft_load: float = 0.0  # lbs

        # Autonomous Features
        self.autonomous_mode: bool = False
        self.obstacle_detection: bool = True
        self.emergency_stop_active: bool = False

        # ISOBUS Communication
        self.isobus_address: int = 0x80  # Default address
        self.device_name: str = f"{make}_{model}_{year}"
        self.message_queue: list[ISOBUSMessage] = []

        # Vision & Sensor Systems
        self.camera_config: CameraConfig | None = None
        self.lidar_enabled: bool = False
        self.obstacle_list: list[tuple[float, float, float]] = []

        # Safety Systems (ISO 18497)
        self.safety_zones: list[SafetyZone] = []
        self.safety_level: SafetyLevel = SafetyLevel.PERFORMANCE_LEVEL_C
        self.safety_system_active: bool = True

        # Motor Control Systems
        self.motors: dict[str, dict[str, float]] = {
            "steer_motor": {"position": 0.0, "velocity": 0.0, "torque": 0.0},
            "throttle_motor": {"position": 0.0, "velocity": 0.0, "torque": 0.0},
            "implement_lift": {"position": 0.0, "velocity": 0.0, "torque": 0.0},
        }

        # Data Management
        self.operation_log: list[dict[str, float]] = []
        self.current_task: TaskData | None = None

        # Power Management
        self.power_sources: list[PowerSource] = [
            PowerSource("diesel_engine", 12.0, 200.0, 0.85),
            PowerSource("alternator", 12.0, 100.0, 0.90),
        ]
        self.power_consumption: dict[str, float] = {}
        self.regenerative_mode: bool = False

        # Enhanced Reliable ISOBUS Communication
        from afs_fastapi.equipment.reliable_isobus import ReliableISOBUSDevice

        self.reliable_isobus = ReliableISOBUSDevice(device_address=self.isobus_address)

    def start_engine(self) -> str:
        if self.engine_on:
            raise ValueError("Engine is already running.")
        self.engine_on = True
        return "Engine started."

    def stop_engine(self) -> str:
        if not self.engine_on:
            raise ValueError("Engine is already off.")
        self.engine_on = False
        self.speed = 0  # Reset speed when engine is stopped.
        self.gear = 0  # Return to neutral gear.
        self.power_takeoff = False  # Disengage PTO.
        self.hydraulics = False  # Deactivate hydraulics.
        return "Engine stopped. Tractor is now reset."

    def change_gear(self, gear: int | str) -> str:
        """
        Change the tractor's gear.
        Args:
            gear: The gear to change to (int or string)
        Returns:
            str: Status message
        Raises:
            ValueError: If engine is off or invalid gear
        """
        if not self.engine_on:
            raise ValueError("Cannot change gears while the engine is off.")

        # Convert gear to int if it's a string
        try:
            gear = int(gear)
        except ValueError as e:
            raise ValueError("Invalid gear value") from e

        if not 0 <= gear <= 10:
            raise ValueError("Gear must be between 0 and 10.")

        self.gear = gear
        return f"Gear changed to {gear}."

    def accelerate(self, increase: int) -> str:
        if not self.engine_on:
            raise ValueError("Cannot accelerate while the engine is off.")
        if increase < 0:
            raise ValueError("Acceleration must be a positive value.")
        self.speed = min(self.speed + increase, self.MAX_SPEED)  # Limit speed to MAX_SPEED.
        return f"Speed increased to {self.speed} mph."

    def brake(self, decrease: int) -> str:
        if not self.engine_on:
            raise ValueError("Cannot brake while the engine is off.")
        if decrease < 0:
            raise ValueError("Brake reduction must be a positive value.")
        self.speed = max(0, self.speed - decrease)  # Ensure speed is not negative.
        return f"Speed decreased to {self.speed} mph."

    def engage_power_takeoff(self) -> str:
        if not self.engine_on:
            raise ValueError("Cannot engage PTO while the engine is off.")
        if self.power_takeoff:
            raise ValueError("PTO is already engaged.")
        self.power_takeoff = True
        return "Power Take-Off (PTO) engaged."

    def disengage_power_takeoff(self) -> str:
        if not self.power_takeoff:
            raise ValueError("PTO is already disengaged.")
        self.power_takeoff = False
        return "Power Take-Off (PTO) disengaged."

    def activate_hydraulics(self) -> str:
        if not self.engine_on:
            raise ValueError("Cannot activate hydraulics while the engine is off.")
        if self.hydraulics:
            raise ValueError("Hydraulics are already activated.")
        self.hydraulics = True
        return "Hydraulics activated."

    def deactivate_hydraulics(self) -> str:
        if not self.hydraulics:
            raise ValueError("Hydraulics are already deactivated.")
        self.hydraulics = False
        return "Hydraulics deactivated."

    # GPS and Navigation Controls
    def set_gps_position(self, latitude: float, longitude: float) -> str:
        """Set current GPS coordinates."""
        if not (-90 <= latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90 degrees")
        if not (-180 <= longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180 degrees")

        self.gps_latitude = latitude
        self.gps_longitude = longitude
        return f"GPS position set to {latitude:.6f}, {longitude:.6f}"

    def enable_auto_steer(self) -> str:
        """Enable GPS auto-steer system."""
        if not self.engine_on:
            raise ValueError("Cannot enable auto-steer while engine is off")
        if self.gps_latitude is None or self.gps_longitude is None:
            raise ValueError("GPS position must be set before enabling auto-steer")
        if self.auto_steer_enabled:
            raise ValueError("Auto-steer is already enabled")

        self.auto_steer_enabled = True
        return "Auto-steer enabled"

    def disable_auto_steer(self) -> str:
        """Disable GPS auto-steer system."""
        if not self.auto_steer_enabled:
            raise ValueError("Auto-steer is already disabled")

        self.auto_steer_enabled = False
        return "Auto-steer disabled"

    def add_waypoint(self, latitude: float, longitude: float) -> str:
        """Add a waypoint to the navigation route."""
        if not (-90 <= latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90 degrees")
        if not (-180 <= longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180 degrees")

        self.waypoints.append((latitude, longitude))
        return f"Waypoint added: {latitude:.6f}, {longitude:.6f}. Total waypoints: {len(self.waypoints)}"

    def clear_waypoints(self) -> str:
        """Clear all navigation waypoints."""
        waypoint_count: int = len(self.waypoints)
        self.waypoints.clear()
        return f"Cleared {waypoint_count} waypoints"

    def set_heading(self, heading: float) -> str:
        """Set current heading in degrees (0-359)."""
        if not (0 <= heading < 360):
            raise ValueError("Heading must be between 0 and 359 degrees")

        self.current_heading = heading
        return f"Heading set to {heading:.1f} degrees"

    # Implement Controls
    def raise_implement(self) -> str:
        """Raise the attached implement."""
        if not self.engine_on:
            raise ValueError("Cannot raise implement while engine is off")
        if self.implement_position == ImplementPosition.RAISED:
            raise ValueError("Implement is already raised")

        self.implement_position = ImplementPosition.RAISED
        self.implement_depth = 0.0
        return "Implement raised"

    def lower_implement(self, depth: float = 6.0) -> str:
        """Lower the implement to working position."""
        if not self.engine_on:
            raise ValueError("Cannot lower implement while engine is off")
        if not self.hydraulics:
            raise ValueError("Hydraulics must be activated to lower implement")
        if depth < 0 or depth > 24:
            raise ValueError("Implement depth must be between 0 and 24 inches")

        self.implement_position = ImplementPosition.LOWERED
        self.implement_depth = depth
        return f"Implement lowered to {depth:.1f} inch depth"

    def set_transport_position(self) -> str:
        """Set implement to transport position."""
        if not self.engine_on:
            raise ValueError("Cannot change implement position while engine is off")

        self.implement_position = ImplementPosition.TRANSPORT
        self.implement_depth = 0.0
        return "Implement set to transport position"

    def set_implement_width(self, width: float) -> str:
        """Set the working width of the implement."""
        if width < 0 or width > 80:
            raise ValueError("Implement width must be between 0 and 80 feet")

        self.implement_width = width
        return f"Implement width set to {width:.1f} feet"

    # Field Operation Controls
    def set_field_mode(self, mode: FieldMode) -> str:
        """Set the current field operation mode."""
        if not self.engine_on:
            raise ValueError("Cannot change field mode while engine is off")

        self.field_mode = mode
        return f"Field mode set to {mode.value}"

    def start_field_work(self) -> str:
        """Begin field work operations."""
        if not self.engine_on:
            raise ValueError("Engine must be running to start field work")
        if self.field_mode == FieldMode.TRANSPORT:
            raise ValueError("Must set field mode before starting work")
        if self.implement_position != ImplementPosition.LOWERED:
            raise ValueError("Implement must be lowered to start field work")

        self.area_covered = 0.0
        self.work_rate = self.speed * self.implement_width / 8.25  # rough calculation
        return f"Field work started in {self.field_mode.value} mode"

    def update_work_progress(self, distance: float) -> str:
        """Update work progress based on distance covered."""
        if distance < 0:
            raise ValueError("Distance must be positive")

        if self.implement_width > 0:
            area_increment: float = (distance * self.implement_width) / 43560  # convert to acres
            self.area_covered += area_increment

        return f"Work progress updated. Total area covered: {self.area_covered:.2f} acres"

    # Autonomous Operation Controls
    def enable_autonomous_mode(self) -> str:
        """Enable autonomous operation mode."""
        if not self.engine_on:
            raise ValueError("Engine must be running for autonomous mode")
        if not self.auto_steer_enabled:
            raise ValueError("Auto-steer must be enabled for autonomous mode")
        if len(self.waypoints) == 0:
            raise ValueError("Waypoints must be set for autonomous mode")
        if self.autonomous_mode:
            raise ValueError("Autonomous mode is already enabled")

        self.autonomous_mode = True
        return "Autonomous mode enabled"

    def disable_autonomous_mode(self) -> str:
        """Disable autonomous operation mode."""
        if not self.autonomous_mode:
            raise ValueError("Autonomous mode is already disabled")

        self.autonomous_mode = False
        return "Autonomous mode disabled"

    def reset_emergency_stop(self) -> str:
        """Reset emergency stop condition."""
        if not self.emergency_stop_active:
            raise ValueError("Emergency stop is not active")

        self.emergency_stop_active = False
        return "Emergency stop reset - Manual control restored"

    # Sensor Reading Methods
    def get_engine_diagnostics(self) -> dict[str, float]:
        """Get current engine diagnostic readings."""
        if self.engine_on:
            self.engine_rpm = 1800 + (self.speed * 25)  # simulate RPM based on speed
            self.engine_temp = min(220, 180 + (self.engine_rpm / 100))  # simulate temp
        else:
            self.engine_rpm = 0

        return {
            "rpm": self.engine_rpm,
            "temperature": self.engine_temp,
            "fuel_level": self.fuel_level,
            "oil_pressure": 45.0 if self.engine_on else 0.0,
        }

    def get_hydraulic_status(self) -> dict[str, float]:
        """Get current hydraulic system status."""
        if self.hydraulics and self.engine_on:
            self.hydraulic_pressure = 2500.0
            self.hydraulic_flow = 25.0
        else:
            self.hydraulic_pressure = 0.0
            self.hydraulic_flow = 0.0

        return {
            "pressure": self.hydraulic_pressure,
            "flow_rate": self.hydraulic_flow,
            "temperature": 140.0 if self.hydraulics else 80.0,
        }

    def get_ground_conditions(self) -> dict[str, float]:
        """Get current ground and traction conditions."""
        # Simulate realistic values based on current state
        if self.engine_on and self.speed > 0:
            self.wheel_slip = min(15.0, self.speed * 0.3)  # More slip at higher speeds
            self.ground_speed = self.speed * (1 - self.wheel_slip / 100)
            self.draft_load = (
                self.implement_depth * 500
                if self.implement_position == ImplementPosition.LOWERED
                else 0
            )
        else:
            self.wheel_slip = 0.0
            self.ground_speed = 0.0
            self.draft_load = 0.0

        return {
            "wheel_slip": self.wheel_slip,
            "ground_speed": self.ground_speed,
            "draft_load": self.draft_load,
            "soil_compaction": 2.5 if self.implement_position == ImplementPosition.LOWERED else 1.0,
        }

    # ==============================================================================
    # ISOBUS Communication Interface Implementation
    # ==============================================================================

    def get_device_name(self) -> str:
        """Return standardized ISOBUS device name."""
        return self.device_name

    def send_message(self, message: ISOBUSMessage, use_reliable: bool = False) -> bool:
        """Send ISOBUS message to network with optional guaranteed delivery.

        Parameters
        ----------
        message : ISOBUSMessage
            Message to transmit via ISOBUS.
        use_reliable : bool, default False
            Whether to use guaranteed delivery system.

        Returns
        -------
        bool
            True if message was successfully queued for transmission.

        Notes
        -----
        When use_reliable=True, this method returns immediately but the message
        may still be retrying in the background. Use send_reliable_message methods
        for delivery confirmation callbacks.
        """
        if use_reliable:
            # Route through guaranteed delivery system

            # Determine priority based on PGN
            priority: int = self._get_message_priority(message.pgn)

            try:
                self.reliable_isobus.send_reliable_message(
                    message,
                    requires_ack=True,
                    priority=priority,
                )
                return True
            except Exception as e:
                print(f"ISOBUS Reliable TX Error: {e}")
                return False
        else:
            # Original simulation behavior for backward compatibility
            print(f"ISOBUS TX: PGN={message.pgn:04X} from {message.source_address:02X}")
            return True

    def _get_message_priority(self, pgn: int) -> int:
        """Determine message priority based on PGN for agricultural operations.

        Parameters
        ----------
        pgn : int
            Parameter Group Number from ISOBUS message.

        Returns
        -------
        int
            Priority level (0 = highest priority).
        """
        from afs_fastapi.equipment.reliable_isobus import ISOBUSPriority

        # Map ISOBUS PGNs to agricultural priorities
        if pgn == 0xFE49:  # Emergency messages
            return ISOBUSPriority.EMERGENCY_STOP
        elif pgn in [0xFE47, 0xFE46]:  # Collision avoidance
            return ISOBUSPriority.COLLISION_AVOIDANCE
        elif pgn == 0xEF00:  # Field allocation
            return ISOBUSPriority.FIELD_COORDINATION
        elif pgn in [0xCF00, 0xDF00]:  # Implement control
            return ISOBUSPriority.IMPLEMENT_CONTROL
        elif pgn == 0xFE48:  # Status updates
            return ISOBUSPriority.STATUS_UPDATE
        else:  # Diagnostic and other messages
            return ISOBUSPriority.DIAGNOSTICS

    def receive_message(self) -> ISOBUSMessage | None:
        """Receive ISOBUS message from network with reliable message processing.

        Returns
        -------
        ISOBUSMessage or None
            Received message, or None if no messages available.

        Notes
        -----
        This method automatically processes acknowledgments for the guaranteed
        delivery system and handles reliable message reception.
        """
        # Check for basic queued messages (simulation/testing)
        if self.message_queue:
            message: ISOBUSMessage = self.message_queue.pop(0)

            # Process acknowledgments for guaranteed delivery system
            if message.pgn == 0xE800:  # ACK PGN
                try:
                    self.reliable_isobus.process_acknowledgment(message)
                    # Return None since ACK messages are processed internally
                    return None
                except Exception as e:
                    print(f"ISOBUS ACK Processing Error: {e}")

            return message

        # TODO: In real implementation, would check CAN bus for incoming messages
        # and process them through the reliable message system

        return None

    def send_tractor_status(self, use_reliable: bool = False) -> bool:
        """Send standardized tractor status via ISOBUS.

        Parameters
        ----------
        use_reliable : bool, default False
            Whether to use guaranteed delivery for status broadcast.

        Returns
        -------
        bool
            True if status message was successfully transmitted.

        Notes
        -----
        When use_reliable=True, status updates will be queued for guaranteed
        delivery with automatic retries and acknowledgment tracking. This is
        useful for critical agricultural operations where status confirmation
        is required for safety or coordination purposes.
        """
        status_data: bytes = bytes(
            [
                self.gear,
                int(self.speed),
                int(self.engine_rpm / 10),
                int(self.fuel_level),
                0x01 if self.engine_on else 0x00,
            ]
        )

        message: ISOBUSMessage = ISOBUSMessage(
            pgn=0xFE48,  # Tractor status PGN
            source_address=self.isobus_address,
            destination_address=0xFF,  # Broadcast
            data=status_data,
            timestamp=datetime.now(),
        )

        return self.send_message(message, use_reliable=use_reliable)

    # ==============================================================================
    # Agricultural Implement Control with Guaranteed Delivery
    # ==============================================================================

    def send_implement_command(
        self,
        implement_address: int,
        command_type: str,
        parameters: dict[str, Any],
        use_reliable: bool = True,
        delivery_callback: Callable[[str, str], None] | None = None,
    ) -> str | bool:
        """Send command to agricultural implement with optional guaranteed delivery.

        Parameters
        ----------
        implement_address : int
            ISOBUS address of target implement (0x80-0x87 typical range).
        command_type : str
            Type of command: 'raise', 'lower', 'enable', 'disable', 'configure'.
        parameters : dict[str, Any]
            Command-specific parameters (depth, rate, speed, etc.).
        use_reliable : bool, default True
            Whether to use guaranteed delivery for implement commands.
        delivery_callback : callable, optional
            Called when delivery is confirmed or fails.

        Returns
        -------
        str or bool
            Message ID if using reliable delivery, bool success otherwise.

        Examples
        --------
        >>> # Lower cultivator to 6 inches with guaranteed delivery
        >>> msg_id = tractor.send_implement_command(
        ...     implement_address=0x82,
        ...     command_type="lower",
        ...     parameters={"depth": 6.0, "speed": 8.0},
        ...     delivery_callback=lambda mid, status: print(f"Cultivator: {status}")
        ... )

        >>> # Enable precision planter without guaranteed delivery
        >>> success = tractor.send_implement_command(
        ...     implement_address=0x83,
        ...     command_type="enable",
        ...     parameters={"seed_rate": 32000, "row_spacing": 30},
        ...     use_reliable=False
        ... )
        """
        from afs_fastapi.equipment.reliable_isobus import ISOBUSPriority

        # Encode command parameters for ISOBUS transmission
        command_data: bytes = self._encode_implement_command(command_type, parameters)

        implement_message: ISOBUSMessage = ISOBUSMessage(
            pgn=0xCF00,  # Implement control PGN
            source_address=self.isobus_address,
            destination_address=implement_address,
            data=command_data,
            timestamp=datetime.now(),
        )

        if use_reliable:
            # Use guaranteed delivery for implement commands
            return self.reliable_isobus.send_reliable_message(
                implement_message,
                delivery_callback=delivery_callback,
                requires_ack=True,
                max_retries=3,
                priority=ISOBUSPriority.IMPLEMENT_CONTROL,
            )
        else:
            # Use basic transmission
            return self.send_message(implement_message, use_reliable=False)

    def _encode_implement_command(self, command_type: str, parameters: dict[str, Any]) -> bytes:
        """Encode implement command parameters into ISOBUS data format.

        Parameters
        ----------
        command_type : str
            Command type identifier.
        parameters : dict[str, Any]
            Command parameters to encode.

        Returns
        -------
        bytes
            Encoded command data for ISOBUS transmission.
        """
        # Simplified encoding for demonstration
        # Real implementation would follow ISO 11783 application layer standards

        command_codes: dict[str, int] = {
            "raise": 0x01,
            "lower": 0x02,
            "enable": 0x03,
            "disable": 0x04,
            "configure": 0x05,
        }

        command_code: int = command_codes.get(command_type, 0x00)

        # Pack common agricultural parameters
        depth: int = int(parameters.get("depth", 0) * 10)  # Depth in 0.1 inch units
        rate: int = int(parameters.get("rate", 0))  # Application rate
        speed: int = int(parameters.get("speed", 0) * 10)  # Speed in 0.1 mph units

        return bytes(
            [
                command_code,
                (depth >> 8) & 0xFF,  # Depth high byte
                depth & 0xFF,  # Depth low byte
                (rate >> 8) & 0xFF,  # Rate high byte
                rate & 0xFF,  # Rate low byte
                (speed >> 8) & 0xFF,  # Speed high byte
                speed & 0xFF,  # Speed low byte
                0x00,  # Reserved
            ]
        )

    def coordinate_field_operation(
        self,
        field_crdt: Any,  # FieldAllocationCRDT
        operation_type: str,
        implement_addresses: list[int],
        use_reliable: bool = True,
    ) -> list[str]:
        """Coordinate multi-implement field operation with guaranteed delivery.

        Parameters
        ----------
        field_crdt : FieldAllocationCRDT
            Field allocation state for coordination.
        operation_type : str
            Type of operation: 'planting', 'spraying', 'harvesting', 'tillage'.
        implement_addresses : list[int]
            ISOBUS addresses of implements to coordinate.
        use_reliable : bool, default True
            Whether to use guaranteed delivery for coordination messages.

        Returns
        -------
        list[str]
            List of message IDs for tracking coordination delivery.

        Notes
        -----
        This method demonstrates how guaranteed delivery integrates with field
        allocation CRDTs to ensure coordinated agricultural operations across
        multiple implements without conflicts or work duplication.
        """
        message_ids: list[str] = []

        # Broadcast field allocation state
        if use_reliable:
            allocation_msg_id: str = self.broadcast_field_allocation_reliable(field_crdt)
            message_ids.append(allocation_msg_id)

        # Send operation commands to each implement
        operation_parameters: dict[str, dict[str, float]] = {
            "planting": {"seed_rate": 32000, "depth": 2.0, "speed": 6.0},
            "spraying": {"application_rate": 20, "pressure": 40, "speed": 12.0},
            "harvesting": {"header_height": 24, "ground_speed": 5.0},
            "tillage": {"depth": 8.0, "speed": 7.0, "overlap": 2.0},
        }

        params: dict[str, Any] = operation_parameters.get(operation_type, {})

        for implement_addr in implement_addresses:
            if use_reliable:
                msg_id: str | bool = self.send_implement_command(
                    implement_address=implement_addr,
                    command_type="configure",
                    parameters=params,
                    use_reliable=True,
                )
                if isinstance(msg_id, str):
                    message_ids.append(msg_id)
            else:
                self.send_implement_command(
                    implement_address=implement_addr,
                    command_type="configure",
                    parameters=params,
                    use_reliable=False,
                )

        return message_ids

    # ==============================================================================
    # Safety System Interface Implementation (ISO 18497)
    # ==============================================================================

    def emergency_stop(self) -> bool:
        """Trigger ISO 18497 compliant emergency stop."""
        self.emergency_stop_active = True
        self.speed = 0
        self.autonomous_mode = False
        self.auto_steer_enabled = False

        # Raise implement for safety
        if self.implement_position == ImplementPosition.LOWERED:
            self.implement_position = ImplementPosition.RAISED

        # Log safety event (using numeric codes: 999 = emergency_stop)
        self.log_operation_data(
            {
                "event_code": 999.0,  # Emergency stop event code
                "timestamp": datetime.now().timestamp(),
                "position_lat": self.gps_latitude or 0.0,
                "position_lon": self.gps_longitude or 0.0,
            }
        )

        self.logger.critical(
            "ISO 18497 EMERGENCY STOP ACTIVATED - Tractor %s %s", self.make, self.model
        )
        return True

    def validate_safety_zone(self, position: tuple[float, float]) -> bool:
        """Validate position is within defined safety zones."""
        if not self.safety_zones:
            return True  # No zones defined = unrestricted

        lat, lon = position
        for zone in self.safety_zones:
            # Simple point-in-polygon check (simplified)
            if self._point_in_polygon((lat, lon), zone.boundary_points):
                return True

        return False

    def _point_in_polygon(
        self, point: tuple[float, float], polygon: list[tuple[float, float]]
    ) -> bool:
        """Helper method for point-in-polygon calculation."""
        # Simplified implementation - would use proper geospatial library in production
        # For now, check if we have valid inputs
        if not polygon or len(polygon) < 3:
            return False

        # Simple bounding box check as placeholder
        x, y = point
        min_x: float = min(p[0] for p in polygon)
        max_x: float = max(p[0] for p in polygon)
        min_y: float = min(p[1] for p in polygon)
        max_y: float = max(p[1] for p in polygon)

        return min_x <= x <= max_x and min_y <= y <= max_y

    def get_safety_status(self) -> dict[str, bool]:
        """Get comprehensive ISO 18497 safety status."""
        current_position: tuple[float, float] = (
            self.gps_latitude or 0.0,
            self.gps_longitude or 0.0,
        )

        return {
            "emergency_stop_active": self.emergency_stop_active,
            "safety_system_operational": self.safety_system_active,
            "position_safe": self.validate_safety_zone(current_position),
            "obstacle_detection_active": self.obstacle_detection,
            "speed_limit_compliant": self.speed <= 25,  # Example limit
            "operator_present": not self.autonomous_mode,
        }

    def add_safety_zone(self, zone: SafetyZone) -> str:
        """Add a safety zone for autonomous operation."""
        self.safety_zones.append(zone)
        return f"Safety zone {zone.zone_id} added with {len(zone.boundary_points)} boundary points"

    # ==============================================================================
    # Motor Control Interface Implementation
    # ==============================================================================

    def send_motor_command(self, command: MotorCommand) -> bool:
        """Send precision motor control command."""
        if command.motor_id not in self.motors:
            print(f"Warning: Motor {command.motor_id} not found")
            return False

        motor_status: dict[str, float] = self.motors[command.motor_id]

        # Update motor status based on command
        if command.command_type == "position":
            motor_status["position"] = command.target_value
        elif command.command_type == "velocity":
            motor_status["velocity"] = command.target_value
        elif command.command_type == "torque":
            motor_status["torque"] = command.target_value

        print(f"Motor {command.motor_id} {command.command_type} set to {command.target_value}")
        return True

    def get_motor_status(self, motor_id: str) -> dict[str, float]:
        """Get current motor status and position."""
        if motor_id not in self.motors:
            return {"error": -1.0}

        return self.motors[motor_id].copy()

    def calibrate_motor(self, motor_id: str) -> bool:
        """Perform motor calibration sequence."""
        if motor_id not in self.motors:
            return False

        # Simulate calibration
        self.motors[motor_id]["position"] = 0.0
        self.motors[motor_id]["velocity"] = 0.0
        self.motors[motor_id]["torque"] = 0.0

        print(f"Motor {motor_id} calibrated successfully")
        return True

    # ==============================================================================
    # Data Management Interface Implementation
    # ==============================================================================

    def export_iso_xml(self, task_data: TaskData) -> str:
        """Export agricultural data in ISO 11783-10 XML format."""
        # Simplified ISO XML generation
        xml_data: str = f"""<?xml version="1.0" encoding="UTF-8"?>
<ISO11783_TaskData>
    <TSK A="{task_data.task_id}" B="{task_data.operation_type}"
         C="{task_data.start_time.isoformat()}" D="1" E="{task_data.field_id}">
        <TLG A="{len(self.operation_log)}">
            <!-- Operation log data would be here -->
        </TLG>
    </TSK>
</ISO11783_TaskData>"""
        return xml_data

    def import_prescription_map(self, map_data: bytes) -> dict[str, float]:
        """Import variable rate prescription map."""
        # TODO: Implement proper map parsing
        # For now, validate input and return simulated prescription data
        if not map_data:
            raise ValueError("Map data cannot be empty")

        # Simulate parsing different map sizes
        data_size: int = len(map_data)
        base_rate: float = 30000.0 + (data_size % 5000)  # Vary based on data size

        return {
            "seed_rate": base_rate,  # seeds per acre
            "fertilizer_rate": 150.0,  # lbs per acre
            "spray_rate": 20.0,  # gallons per acre
        }

    def log_operation_data(self, data_point: dict[str, float]) -> bool:
        """Log operational data point for analysis."""
        enhanced_data: dict[str, float] = data_point.copy()
        enhanced_data.update(
            {
                "timestamp": datetime.now().timestamp(),
                "speed": float(self.speed),
                "fuel_level": self.fuel_level,
                "engine_rpm": float(self.engine_rpm),
            }
        )

        self.operation_log.append(enhanced_data)
        return True

    def start_task_recording(self, task_id: str, field_id: str, operation_type: str) -> str:
        """Start recording a new field task."""
        self.current_task = TaskData(
            task_id=task_id,
            field_id=field_id,
            operation_type=operation_type,
            prescription_map=None,
            start_time=datetime.now(),
        )
        return f"Task recording started: {task_id}"

    def stop_task_recording(self) -> str:
        """Stop current task recording."""
        if self.current_task:
            self.current_task.end_time = datetime.now()
            task_id: str = self.current_task.task_id
            self.current_task = None
            return f"Task recording stopped: {task_id}"
        return "No active task to stop"

    # ==============================================================================
    # Power Management Interface Implementation
    # ==============================================================================

    def get_power_status(self) -> dict[str, float]:
        """Get comprehensive power system status."""
        total_available: float = sum(
            ps.voltage * ps.max_current * ps.efficiency for ps in self.power_sources
        )
        total_consumption: float = sum(self.power_consumption.values())

        return {
            "total_available_power": total_available,
            "total_consumption": total_consumption,
            "power_efficiency": (
                (total_available - total_consumption) / total_available
                if total_available > 0
                else 0.0
            ),
            "battery_level": self.fuel_level,  # Simplified
            "regenerative_active": float(self.regenerative_mode),
            "diesel_engine_load": float(self.engine_rpm / 2500.0) if self.engine_on else 0.0,
        }

    def set_power_priority(self, device_priorities: dict[str, int]) -> bool:
        """Set power allocation priorities for different systems."""
        # TODO: Implement actual power management logic
        print(f"Power priorities set: {device_priorities}")
        return True

    def enable_regenerative_mode(self) -> bool:
        """Enable energy recovery from hydraulic and motion systems."""
        if self.engine_on:
            self.regenerative_mode = True
            print("Regenerative energy recovery enabled")
            return True
        return False

    def disable_regenerative_mode(self) -> bool:
        """Disable energy recovery mode."""
        self.regenerative_mode = False
        print("Regenerative energy recovery disabled")
        return True

    def __str__(self) -> str:
        """
        Returns a string representation of the FarmTractor object.

        Returns:
            str: A string summarizing the tractor's details.
        """
        engine_status: str = "On" if self.engine_on else "Off"
        manual_info: str = self.manual_url if self.manual_url else "No manual available"
        gps_info: str = (
            f"GPS: {self.gps_latitude:.6f}, {self.gps_longitude:.6f}"
            if self.gps_latitude
            else "GPS: Not Set"
        )
        return (
            f"Tractor {self.make} {self.model} ({self.year})\n"
            f"Engine: {engine_status}\n"
            f"Speed: {self.speed} mph\n"
            f"Gear: {self.gear}\n"
            f"PTO: {'Engaged' if self.power_takeoff else 'Disengaged'}\n"
            f"Hydraulics: {'Activated' if self.hydraulics else 'Deactivated'}\n"
            f"{gps_info}\n"
            f"Auto-Steer: {'Enabled' if self.auto_steer_enabled else 'Disabled'}\n"
            f"Field Mode: {self.field_mode.value}\n"
            f"Implement: {self.implement_position.value}\n"
            f"Autonomous: {'Active' if self.autonomous_mode else 'Inactive'}\n"
            f"Manual URL: {manual_info}"
        )

    def to_response(self, tractor_id: str | None = None) -> FarmTractorResponse:
        """
        Convert the current tractor state to a Pydantic response model.

        Returns
        -------
        FarmTractorResponse
            A serializable snapshot of the tractor's current state.
        """
        return FarmTractorResponse(
            tractor_id=tractor_id,
            make=self.make,
            model=self.model,
            year=self.year,
            manual_url=self.manual_url,
            engine_on=self.engine_on,
            speed=self.speed,
            gear=self.gear,
            power_takeoff=self.power_takeoff,
            hydraulics=self.hydraulics,
            gps_latitude=self.gps_latitude,
            gps_longitude=self.gps_longitude,
            auto_steer_enabled=self.auto_steer_enabled,
            implement_position=self.implement_position.value,
            field_mode=self.field_mode.value,
            fuel_level=self.fuel_level,
            engine_rpm=self.engine_rpm,
            hydraulic_pressure=self.hydraulic_pressure,
            # Enhanced robotic interface fields
            waypoint_count=len(self.waypoints),
            current_heading=self.current_heading,
            implement_depth=self.implement_depth,
            implement_width=self.implement_width,
            work_rate=self.work_rate,
            area_covered=self.area_covered,
            engine_temp=self.engine_temp,
            hydraulic_flow=self.hydraulic_flow,
            wheel_slip=self.wheel_slip,
            ground_speed=self.ground_speed,
            draft_load=self.draft_load,
            autonomous_mode=self.autonomous_mode,
            obstacle_detection=self.obstacle_detection,
            emergency_stop_active=self.emergency_stop_active,
            isobus_address=self.isobus_address,
            device_name=self.device_name,
            safety_system_active=self.safety_system_active,
            safety_level=self.safety_level.value,
            regenerative_mode=self.regenerative_mode,
            lidar_enabled=self.lidar_enabled,
            obstacle_count=len(self.obstacle_list),
            status=str(self),
        )

    # ==============================================================================
    # Enhanced Reliable ISOBUS Communication Methods
    # ==============================================================================

    def send_tractor_status_reliable(
        self,
        delivery_callback: Callable[[str, str], None] | None = None,
        requires_ack: bool = True,
        max_retries: int = 3,
        priority: int | None = None,
    ) -> str:
        """Send tractor status with guaranteed delivery.

        Parameters
        ----------
        delivery_callback : callable, optional
            Called when delivery is confirmed or fails.
        requires_ack : bool, default True
            Whether acknowledgment is required.
        max_retries : int, default 3
            Maximum retry attempts.
        priority : int, optional
            Message priority (0 = highest). If None, uses STATUS_UPDATE priority.

        Returns
        -------
        str
            Message ID for tracking delivery status.
        """
        from afs_fastapi.equipment.reliable_isobus import ISOBUSPriority

        # Use agricultural priority if not specified
        if priority is None:
            priority = ISOBUSPriority.STATUS_UPDATE

        # Create standard status message
        status_data: bytes = bytes(
            [
                self.gear,
                int(self.speed),
                int(self.engine_rpm / 10),
                int(self.fuel_level),
                0x01 if self.engine_on else 0x00,
            ]
        )

        status_message: ISOBUSMessage = ISOBUSMessage(
            pgn=0xFE48,  # Tractor status PGN
            source_address=self.isobus_address,
            destination_address=0xFF,  # Broadcast
            data=status_data,
            timestamp=datetime.now(),
        )

        # Send with guaranteed delivery
        return self.reliable_isobus.send_reliable_message(
            status_message,
            delivery_callback=delivery_callback,
            requires_ack=requires_ack,
            max_retries=max_retries,
            priority=priority,
        )

    def broadcast_field_allocation_reliable(
        self,
        field_crdt: Any,  # FieldAllocationCRDT
        delivery_callback: Callable[[str, str], None] | None = None,
        requires_ack: bool = True,
        max_retries: int = 3,
        priority: int | None = None,
    ) -> str:
        """Broadcast field allocation CRDT with guaranteed delivery.

        Parameters
        ----------
        field_crdt : FieldAllocationCRDT
            Field allocation state to broadcast.
        delivery_callback : callable, optional
            Called when delivery is confirmed or fails.
        requires_ack : bool, default True
            Whether acknowledgment is required.
        max_retries : int, default 3
            Maximum retry attempts.
        priority : int, optional
            Message priority (0 = highest). If None, uses FIELD_COORDINATION priority.

        Returns
        -------
        str
            Message ID for tracking delivery status.
        """
        from afs_fastapi.equipment.reliable_isobus import ISOBUSPriority

        # Use agricultural priority if not specified
        if priority is None:
            priority = ISOBUSPriority.FIELD_COORDINATION

        # Serialize CRDT for transmission
        serialized_data: str = field_crdt.serialize()

        allocation_message: ISOBUSMessage = ISOBUSMessage(
            pgn=0xEF00,  # Custom PGN for field allocation
            source_address=self.isobus_address,
            destination_address=0xFF,  # Broadcast
            data=str(serialized_data).encode(),
            timestamp=datetime.now(),
        )

        # Send with guaranteed delivery
        return self.reliable_isobus.send_reliable_message(
            allocation_message,
            delivery_callback=delivery_callback,
            requires_ack=requires_ack,
            max_retries=max_retries,
            priority=priority,
        )

    def emergency_stop_reliable(
        self,
        delivery_callback: Callable[[str, str], None] | None = None,
        max_retries: int = 5,
        retry_interval: float = 0.05,
        timeout: float = 1.0,
    ) -> list[str]:
        """Trigger emergency stop with guaranteed delivery broadcast.

        Parameters
        ----------
        delivery_callback : callable, optional
            Called when delivery is confirmed or fails.
        max_retries : int, default 5
            Maximum retry attempts for safety-critical message.
        retry_interval : float, default 0.05
            Faster retry interval for emergency.
        timeout : float, default 1.0
            Shorter timeout for urgency.

        Returns
        -------
        list[str]
            List of message IDs for tracking delivery status.
        """
        # Perform standard emergency stop
        self.emergency_stop()

        # Create emergency broadcast message
        emergency_data: bytes = b"\xff\x00\x00\x00\x01"  # Emergency stop pattern

        # Send emergency broadcast with highest priority and guaranteed delivery
        from afs_fastapi.equipment.reliable_isobus import ISOBUSPriority

        message_ids: list[str] = []

        # Broadcast to multiple recipients for safety redundancy
        for destination in [0xFF, 0x81, 0x82, 0x83]:  # Broadcast + specific implements
            emergency_msg: ISOBUSMessage = ISOBUSMessage(
                pgn=0xFE49,
                source_address=self.isobus_address,
                destination_address=destination,
                data=emergency_data,
                timestamp=datetime.now(),
            )

            message_id: str = self.reliable_isobus.send_reliable_message(
                emergency_msg,
                delivery_callback=delivery_callback,
                requires_ack=True,
                max_retries=max_retries,
                retry_interval=retry_interval,
                timeout=timeout,
                priority=ISOBUSPriority.EMERGENCY_STOP,  # Highest priority for safety
            )
            message_ids.append(message_id)

        return message_ids
