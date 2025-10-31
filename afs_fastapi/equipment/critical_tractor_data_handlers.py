"""
Critical tractor data handlers for speed, fuel level, and GPS coordinates.

This module provides specialized handlers for the most critical agricultural
equipment data streams, including validation, filtering, alerting, and
precision agriculture features.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from afs_fastapi.core.can_frame_codec import CANFrameCodec, DecodedPGN
from afs_fastapi.equipment.can_error_handling import CANErrorHandler, CANErrorType

# Configure logging for critical data handlers
logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels for critical data."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class DataQuality(Enum):
    """Data quality assessment levels."""

    EXCELLENT = "excellent"  # <1% variance, high frequency
    GOOD = "good"  # <5% variance, normal frequency
    FAIR = "fair"  # <10% variance, reduced frequency
    POOR = "poor"  # >10% variance, irregular frequency
    INVALID = "invalid"  # Failed validation


@dataclass
class DataPoint:
    """Base class for critical data points."""

    timestamp: datetime
    value: float
    units: str
    source_address: int
    quality: DataQuality = DataQuality.GOOD
    confidence: float = 1.0  # 0.0 to 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SpeedData(DataPoint):
    """Vehicle speed data with agricultural context."""

    working_speed: bool = False  # Is this a working speed vs transport
    terrain_factor: float = 1.0  # Terrain difficulty adjustment
    implement_engaged: bool = False
    gps_speed: float | None = None  # For comparison/validation


@dataclass
class FuelData(DataPoint):
    """Fuel level and consumption data."""

    fuel_level_percent: float = 0.0
    fuel_rate_lh: float = 0.0  # Liters per hour
    fuel_remaining_liters: float | None = None
    consumption_efficiency: float | None = None  # L/hectare
    operational_mode: str = "unknown"  # idle, working, transport


@dataclass
class GPSData(DataPoint):
    """GPS coordinate data with precision agriculture features."""

    latitude: float = 0.0
    longitude: float = 0.0
    altitude: float | None = None
    heading: float | None = None  # degrees
    speed_over_ground: float | None = None  # km/h

    # Precision agriculture features
    field_id: str | None = None
    zone_id: str | None = None
    distance_to_boundary: float | None = None  # meters
    guidance_error: float | None = None  # meters from desired path

    # Quality indicators
    satellite_count: int | None = None
    hdop: float | None = None  # Horizontal Dilution of Precision
    rtk_status: str | None = None  # RTK correction status


@dataclass
class Alert:
    """Critical data alert."""

    level: AlertLevel
    message: str
    data_type: str
    source_address: int
    timestamp: datetime
    value: float | None = None
    threshold: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SpeedDataHandler:
    """Handler for vehicle speed data with agricultural validation."""

    def __init__(self, error_handler: CANErrorHandler) -> None:
        """Initialize speed data handler.

        Parameters
        ----------
        error_handler : CANErrorHandler
            Error handling system
        """
        self.error_handler = error_handler
        self._speed_history: dict[int, list[SpeedData]] = {}
        self._alert_callbacks: list[Callable[[Alert], None]] = []

        # Configuration
        self.max_working_speed = 25.0  # km/h
        self.max_transport_speed = 80.0  # km/h
        self.min_working_speed = 0.5  # km/h
        self.speed_variance_threshold = 0.15  # 15% variance
        self.history_window = timedelta(minutes=5)

    def process_speed_message(self, decoded_msg: DecodedPGN) -> SpeedData | None:
        """Process a vehicle speed CAN message.

        Parameters
        ----------
        decoded_msg : DecodedPGN
            Decoded speed message (PGN 65265 - WVS)

        Returns
        -------
        SpeedData | None
            Processed speed data
        """
        try:
            # Extract speed SPN (84 - Wheel-Based Vehicle Speed)
            speed_spn = next((spn for spn in decoded_msg.spn_values if spn.spn == 84), None)

            if not speed_spn or not speed_spn.is_valid:
                return None

            speed_kmh = speed_spn.value

            # Validate speed range
            quality = self._assess_speed_quality(speed_kmh, decoded_msg.source_address)

            # Determine if this is working speed
            working_speed = self._detect_working_speed(speed_kmh, decoded_msg.source_address)

            # Create speed data point
            speed_data = SpeedData(
                timestamp=decoded_msg.timestamp,
                value=speed_kmh,
                units="km/h",
                source_address=decoded_msg.source_address,
                quality=quality,
                working_speed=working_speed,
                implement_engaged=self._detect_implement_status(decoded_msg),
            )

            # Update history and check for alerts
            self._update_speed_history(speed_data)
            self._check_speed_alerts(speed_data)

            logger.debug(
                f"Processed speed: {speed_kmh:.1f} km/h from {decoded_msg.source_address:02X}"
            )
            return speed_data

        except Exception as e:
            logger.error(f"Failed to process speed message: {e}")
            self.error_handler.handle_error(
                CANErrorType.DATA_CORRUPTION,
                f"Speed processing error: {e}",
                decoded_msg.source_address,
            )
            return None

    def _assess_speed_quality(self, speed: float, source_address: int) -> DataQuality:
        """Assess the quality of speed data.

        Parameters
        ----------
        speed : float
            Speed value in km/h
        source_address : int
            Source address

        Returns
        -------
        DataQuality
            Quality assessment
        """
        # Range validation
        if speed < 0 or speed > 200:  # Physically impossible speeds
            return DataQuality.INVALID

        # Get recent history for variance analysis
        history = self._speed_history.get(source_address, [])
        if len(history) < 3:
            return DataQuality.GOOD

        recent_speeds = [data.value for data in history[-10:]]
        mean_speed = sum(recent_speeds) / len(recent_speeds)

        if mean_speed > 0:
            variance = abs(speed - mean_speed) / mean_speed

            if variance < 0.01:
                return DataQuality.EXCELLENT
            elif variance < 0.05:
                return DataQuality.GOOD
            elif variance < 0.10:
                return DataQuality.FAIR
            else:
                return DataQuality.POOR

        return DataQuality.GOOD

    def _detect_working_speed(self, speed: float, source_address: int) -> bool:
        """Detect if the vehicle is at working speed.

        Parameters
        ----------
        speed : float
            Speed in km/h
        source_address : int
            Source address

        Returns
        -------
        bool
            True if at working speed
        """
        return self.min_working_speed <= speed <= self.max_working_speed

    def _detect_implement_status(self, decoded_msg: DecodedPGN) -> bool:
        """Detect if implement is engaged based on available data.

        Parameters
        ----------
        decoded_msg : DecodedPGN
            Decoded message

        Returns
        -------
        bool
            True if implement appears to be engaged
        """
        # Look for implement control messages or power take-off status
        # This is a simplified implementation
        return False  # Would need additional PGN data

    def _update_speed_history(self, speed_data: SpeedData) -> None:
        """Update speed history for trend analysis.

        Parameters
        ----------
        speed_data : SpeedData
            New speed data point
        """
        source_address = speed_data.source_address

        if source_address not in self._speed_history:
            self._speed_history[source_address] = []

        history = self._speed_history[source_address]
        history.append(speed_data)

        # Cleanup old data
        cutoff_time = datetime.now(UTC) - self.history_window
        self._speed_history[source_address] = [
            data for data in history if data.timestamp > cutoff_time
        ]

    def _check_speed_alerts(self, speed_data: SpeedData) -> None:
        """Check for speed-related alerts.

        Parameters
        ----------
        speed_data : SpeedData
            Speed data to check
        """
        alerts = []

        # Overspeed alerts
        if speed_data.working_speed and speed_data.value > self.max_working_speed:
            alerts.append(
                Alert(
                    level=AlertLevel.WARNING,
                    message=f"Working speed exceeded: {speed_data.value:.1f} km/h",
                    data_type="speed",
                    source_address=speed_data.source_address,
                    timestamp=speed_data.timestamp,
                    value=speed_data.value,
                    threshold=self.max_working_speed,
                )
            )

        if speed_data.value > self.max_transport_speed:
            alerts.append(
                Alert(
                    level=AlertLevel.CRITICAL,
                    message=f"Transport speed exceeded: {speed_data.value:.1f} km/h",
                    data_type="speed",
                    source_address=speed_data.source_address,
                    timestamp=speed_data.timestamp,
                    value=speed_data.value,
                    threshold=self.max_transport_speed,
                )
            )

        # Quality alerts
        if speed_data.quality == DataQuality.POOR:
            alerts.append(
                Alert(
                    level=AlertLevel.WARNING,
                    message="Speed data quality degraded",
                    data_type="speed_quality",
                    source_address=speed_data.source_address,
                    timestamp=speed_data.timestamp,
                )
            )

        # Send alerts
        for alert in alerts:
            self._send_alert(alert)

    def _send_alert(self, alert: Alert) -> None:
        """Send alert to registered callbacks.

        Parameters
        ----------
        alert : Alert
            Alert to send
        """
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """Add an alert callback.

        Parameters
        ----------
        callback : Callable[[Alert], None]
            Alert callback function
        """
        self._alert_callbacks.append(callback)


class FuelDataHandler:
    """Handler for fuel level and consumption data."""

    def __init__(self, error_handler: CANErrorHandler) -> None:
        """Initialize fuel data handler.

        Parameters
        ----------
        error_handler : CANErrorHandler
            Error handling system
        """
        self.error_handler = error_handler
        self._fuel_history: dict[int, list[FuelData]] = {}
        self._alert_callbacks: list[Callable[[Alert], None]] = []

        # Configuration
        self.low_fuel_threshold = 20.0  # percent
        self.critical_fuel_threshold = 10.0  # percent
        self.max_fuel_rate = 50.0  # L/h (reasonable maximum)
        self.tank_capacity = 400.0  # liters (typical tractor)
        self.history_window = timedelta(hours=1)

    def process_fuel_message(self, decoded_msg: DecodedPGN) -> FuelData | None:
        """Process a fuel economy CAN message.

        Parameters
        ----------
        decoded_msg : DecodedPGN
            Decoded fuel message (PGN 65266 - LFE)

        Returns
        -------
        FuelData | None
            Processed fuel data
        """
        try:
            # Extract fuel rate SPN (183 - Engine Fuel Rate)
            fuel_rate_spn = next((spn for spn in decoded_msg.spn_values if spn.spn == 183), None)

            if not fuel_rate_spn or not fuel_rate_spn.is_valid:
                return None

            fuel_rate_lh = fuel_rate_spn.value

            # Estimate fuel level (would need dedicated fuel level sensor in real implementation)
            fuel_level_percent = self._estimate_fuel_level(fuel_rate_lh, decoded_msg.source_address)

            # Assess data quality
            quality = self._assess_fuel_quality(fuel_rate_lh, decoded_msg.source_address)

            # Create fuel data point
            fuel_data = FuelData(
                timestamp=decoded_msg.timestamp,
                value=fuel_rate_lh,
                units="L/h",
                source_address=decoded_msg.source_address,
                quality=quality,
                fuel_level_percent=fuel_level_percent,
                fuel_rate_lh=fuel_rate_lh,
                fuel_remaining_liters=self.tank_capacity * fuel_level_percent / 100.0,
                operational_mode=self._detect_operational_mode(fuel_rate_lh),
            )

            # Update history and check for alerts
            self._update_fuel_history(fuel_data)
            self._check_fuel_alerts(fuel_data)

            logger.debug(
                f"Processed fuel: {fuel_rate_lh:.1f} L/h, {fuel_level_percent:.1f}% from {decoded_msg.source_address:02X}"
            )
            return fuel_data

        except Exception as e:
            logger.error(f"Failed to process fuel message: {e}")
            self.error_handler.handle_error(
                CANErrorType.DATA_CORRUPTION,
                f"Fuel processing error: {e}",
                decoded_msg.source_address,
            )
            return None

    def _estimate_fuel_level(self, fuel_rate: float, source_address: int) -> float:
        """Estimate fuel level based on consumption history.

        Parameters
        ----------
        fuel_rate : float
            Current fuel rate in L/h
        source_address : int
            Source address

        Returns
        -------
        float
            Estimated fuel level percentage
        """
        # Simplified fuel level estimation
        # In a real implementation, this would integrate fuel consumption over time
        # and track from last known fuel level

        history = self._fuel_history.get(source_address, [])
        if not history:
            return 75.0  # Default assumption

        # Calculate average consumption and estimate remaining time
        recent_rates = [data.fuel_rate_lh for data in history[-10:] if data.fuel_rate_lh > 0]
        if recent_rates:
            avg_rate = sum(recent_rates) / len(recent_rates)
            # This is a simplified estimation - real implementation would be more sophisticated
            estimated_hours_remaining = 8.0  # Default 8 hours remaining
            estimated_fuel_remaining = min(
                100.0, (estimated_hours_remaining * avg_rate / self.tank_capacity) * 100
            )
            return max(0.0, estimated_fuel_remaining)

        return 50.0  # Default middle value

    def _assess_fuel_quality(self, fuel_rate: float, source_address: int) -> DataQuality:
        """Assess fuel data quality.

        Parameters
        ----------
        fuel_rate : float
            Fuel rate in L/h
        source_address : int
            Source address

        Returns
        -------
        DataQuality
            Quality assessment
        """
        # Range validation
        if fuel_rate < 0 or fuel_rate > self.max_fuel_rate:
            return DataQuality.INVALID

        # Stability check
        history = self._fuel_history.get(source_address, [])
        if len(history) >= 3:
            recent_rates = [data.fuel_rate_lh for data in history[-5:]]
            mean_rate = sum(recent_rates) / len(recent_rates)

            if mean_rate > 0:
                variance = abs(fuel_rate - mean_rate) / mean_rate

                if variance < 0.05:
                    return DataQuality.EXCELLENT
                elif variance < 0.15:
                    return DataQuality.GOOD
                elif variance < 0.30:
                    return DataQuality.FAIR
                else:
                    return DataQuality.POOR

        return DataQuality.GOOD

    def _detect_operational_mode(self, fuel_rate: float) -> str:
        """Detect operational mode based on fuel consumption.

        Parameters
        ----------
        fuel_rate : float
            Fuel rate in L/h

        Returns
        -------
        str
            Operational mode
        """
        if fuel_rate < 2.0:
            return "idle"
        elif fuel_rate < 8.0:
            return "light_work"
        elif fuel_rate < 20.0:
            return "normal_work"
        else:
            return "heavy_work"

    def _update_fuel_history(self, fuel_data: FuelData) -> None:
        """Update fuel history for trend analysis.

        Parameters
        ----------
        fuel_data : FuelData
            New fuel data point
        """
        source_address = fuel_data.source_address

        if source_address not in self._fuel_history:
            self._fuel_history[source_address] = []

        history = self._fuel_history[source_address]
        history.append(fuel_data)

        # Cleanup old data
        cutoff_time = datetime.now(UTC) - self.history_window
        self._fuel_history[source_address] = [
            data for data in history if data.timestamp > cutoff_time
        ]

    def _check_fuel_alerts(self, fuel_data: FuelData) -> None:
        """Check for fuel-related alerts.

        Parameters
        ----------
        fuel_data : FuelData
            Fuel data to check
        """
        alerts = []

        # Low fuel alerts
        if fuel_data.fuel_level_percent <= self.critical_fuel_threshold:
            alerts.append(
                Alert(
                    level=AlertLevel.CRITICAL,
                    message=f"Critical fuel level: {fuel_data.fuel_level_percent:.1f}%",
                    data_type="fuel_level",
                    source_address=fuel_data.source_address,
                    timestamp=fuel_data.timestamp,
                    value=fuel_data.fuel_level_percent,
                    threshold=self.critical_fuel_threshold,
                )
            )
        elif fuel_data.fuel_level_percent <= self.low_fuel_threshold:
            alerts.append(
                Alert(
                    level=AlertLevel.WARNING,
                    message=f"Low fuel level: {fuel_data.fuel_level_percent:.1f}%",
                    data_type="fuel_level",
                    source_address=fuel_data.source_address,
                    timestamp=fuel_data.timestamp,
                    value=fuel_data.fuel_level_percent,
                    threshold=self.low_fuel_threshold,
                )
            )

        # High consumption alerts
        if fuel_data.fuel_rate_lh > 30.0:  # High consumption threshold
            alerts.append(
                Alert(
                    level=AlertLevel.WARNING,
                    message=f"High fuel consumption: {fuel_data.fuel_rate_lh:.1f} L/h",
                    data_type="fuel_consumption",
                    source_address=fuel_data.source_address,
                    timestamp=fuel_data.timestamp,
                    value=fuel_data.fuel_rate_lh,
                    threshold=30.0,
                )
            )

        # Send alerts
        for alert in alerts:
            self._send_alert(alert)

    def _send_alert(self, alert: Alert) -> None:
        """Send alert to registered callbacks."""
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """Add an alert callback."""
        self._alert_callbacks.append(callback)


class GPSDataHandler:
    """Handler for GPS coordinate data with precision agriculture features."""

    def __init__(self, error_handler: CANErrorHandler) -> None:
        """Initialize GPS data handler.

        Parameters
        ----------
        error_handler : CANErrorHandler
            Error handling system
        """
        self.error_handler = error_handler
        self._gps_history: dict[int, list[GPSData]] = {}
        self._alert_callbacks: list[Callable[[Alert], None]] = []

        # Configuration
        self.position_accuracy_threshold = 5.0  # meters
        self.max_speed_over_ground = 100.0  # km/h
        self.min_satellite_count = 4
        self.max_hdop = 2.0  # Good HDOP threshold
        self.history_window = timedelta(minutes=10)

    def process_gps_message(self, decoded_msg: DecodedPGN) -> GPSData | None:
        """Process a GPS position CAN message.

        Parameters
        ----------
        decoded_msg : DecodedPGN
            Decoded GPS message (PGN 65267 - VP)

        Returns
        -------
        GPSData | None
            Processed GPS data
        """
        try:
            # Extract latitude and longitude SPNs
            lat_spn = next((spn for spn in decoded_msg.spn_values if spn.spn == 584), None)
            lon_spn = next((spn for spn in decoded_msg.spn_values if spn.spn == 585), None)

            if not lat_spn or not lon_spn or not lat_spn.is_valid or not lon_spn.is_valid:
                return None

            latitude = lat_spn.value
            longitude = lon_spn.value

            # Validate coordinates
            if not self._validate_coordinates(latitude, longitude):
                return None

            # Calculate additional metrics
            speed_over_ground = self._calculate_speed_over_ground(
                latitude, longitude, decoded_msg.source_address
            )

            # Assess data quality
            quality = self._assess_gps_quality(latitude, longitude, decoded_msg.source_address)

            # Create GPS data point
            gps_data = GPSData(
                timestamp=decoded_msg.timestamp,
                value=0.0,  # Not applicable for GPS
                units="degrees",
                source_address=decoded_msg.source_address,
                quality=quality,
                latitude=latitude,
                longitude=longitude,
                speed_over_ground=speed_over_ground,
                satellite_count=self._estimate_satellite_count(quality),
                hdop=self._estimate_hdop(quality),
            )

            # Add precision agriculture features
            self._enhance_with_precision_ag_features(gps_data)

            # Update history and check for alerts
            self._update_gps_history(gps_data)
            self._check_gps_alerts(gps_data)

            logger.debug(
                f"Processed GPS: {latitude:.6f}, {longitude:.6f} from {decoded_msg.source_address:02X}"
            )
            return gps_data

        except Exception as e:
            logger.error(f"Failed to process GPS message: {e}")
            self.error_handler.handle_error(
                CANErrorType.DATA_CORRUPTION,
                f"GPS processing error: {e}",
                decoded_msg.source_address,
            )
            return None

    def _validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """Validate GPS coordinates.

        Parameters
        ----------
        latitude : float
            Latitude in degrees
        longitude : float
            Longitude in degrees

        Returns
        -------
        bool
            True if coordinates are valid
        """
        return (-90.0 <= latitude <= 90.0) and (-180.0 <= longitude <= 180.0)

    def _calculate_speed_over_ground(
        self, latitude: float, longitude: float, source_address: int
    ) -> float | None:
        """Calculate speed over ground from position history.

        Parameters
        ----------
        latitude : float
            Current latitude
        longitude : float
            Current longitude
        source_address : int
            Source address

        Returns
        -------
        float | None
            Speed over ground in km/h
        """
        history = self._gps_history.get(source_address, [])
        if not history:
            return None

        # Get most recent position
        last_pos = history[-1]
        time_delta = (datetime.now(UTC) - last_pos.timestamp).total_seconds()

        if time_delta <= 0:
            return None

        # Calculate distance using Haversine formula
        distance_km = self._haversine_distance(
            last_pos.latitude, last_pos.longitude, latitude, longitude
        )

        # Calculate speed
        speed_kmh = (distance_km / time_delta) * 3600  # Convert to km/h

        return min(speed_kmh, self.max_speed_over_ground)  # Cap at maximum

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS coordinates using Haversine formula.

        Parameters
        ----------
        lat1, lon1 : float
            First coordinate
        lat2, lon2 : float
            Second coordinate

        Returns
        -------
        float
            Distance in kilometers
        """
        R = 6371.0  # Earth radius in kilometers

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _assess_gps_quality(
        self, latitude: float, longitude: float, source_address: int
    ) -> DataQuality:
        """Assess GPS data quality.

        Parameters
        ----------
        latitude : float
            Latitude
        longitude : float
            Longitude
        source_address : int
            Source address

        Returns
        -------
        DataQuality
            Quality assessment
        """
        # Position stability check
        history = self._gps_history.get(source_address, [])
        if len(history) >= 3:
            recent_positions = history[-5:]
            position_variance = 0.0

            for pos in recent_positions:
                distance = self._haversine_distance(
                    latitude, longitude, pos.latitude, pos.longitude
                )
                position_variance += distance * 1000  # Convert to meters

            avg_variance = position_variance / len(recent_positions)

            if avg_variance < 1.0:  # < 1 meter
                return DataQuality.EXCELLENT
            elif avg_variance < 3.0:  # < 3 meters
                return DataQuality.GOOD
            elif avg_variance < 10.0:  # < 10 meters
                return DataQuality.FAIR
            else:
                return DataQuality.POOR

        return DataQuality.GOOD

    def _estimate_satellite_count(self, quality: DataQuality) -> int:
        """Estimate satellite count based on quality.

        Parameters
        ----------
        quality : DataQuality
            GPS quality

        Returns
        -------
        int
            Estimated satellite count
        """
        quality_map = {
            DataQuality.EXCELLENT: 12,
            DataQuality.GOOD: 8,
            DataQuality.FAIR: 6,
            DataQuality.POOR: 4,
            DataQuality.INVALID: 0,
        }
        return quality_map.get(quality, 6)

    def _estimate_hdop(self, quality: DataQuality) -> float:
        """Estimate HDOP based on quality.

        Parameters
        ----------
        quality : DataQuality
            GPS quality

        Returns
        -------
        float
            Estimated HDOP
        """
        quality_map = {
            DataQuality.EXCELLENT: 0.8,
            DataQuality.GOOD: 1.2,
            DataQuality.FAIR: 2.0,
            DataQuality.POOR: 3.5,
            DataQuality.INVALID: 99.0,
        }
        return quality_map.get(quality, 2.0)

    def _enhance_with_precision_ag_features(self, gps_data: GPSData) -> None:
        """Enhance GPS data with precision agriculture features.

        Parameters
        ----------
        gps_data : GPSData
            GPS data to enhance
        """
        # Field boundary detection (simplified implementation)
        # In real implementation, this would use field maps and boundaries
        gps_data.field_id = f"field_{hash((gps_data.latitude, gps_data.longitude)) % 1000:03d}"

        # Zone detection for variable rate applications
        # This would typically integrate with prescription maps
        gps_data.zone_id = (
            f"zone_{hash((gps_data.latitude // 0.001, gps_data.longitude // 0.001)) % 100:02d}"
        )

        # Guidance error estimation (would require guidance system integration)
        gps_data.guidance_error = 0.5  # Default 0.5m guidance error

    def _update_gps_history(self, gps_data: GPSData) -> None:
        """Update GPS history for trend analysis.

        Parameters
        ----------
        gps_data : GPSData
            New GPS data point
        """
        source_address = gps_data.source_address

        if source_address not in self._gps_history:
            self._gps_history[source_address] = []

        history = self._gps_history[source_address]
        history.append(gps_data)

        # Cleanup old data
        cutoff_time = datetime.now(UTC) - self.history_window
        self._gps_history[source_address] = [
            data for data in history if data.timestamp > cutoff_time
        ]

    def _check_gps_alerts(self, gps_data: GPSData) -> None:
        """Check for GPS-related alerts.

        Parameters
        ----------
        gps_data : GPSData
            GPS data to check
        """
        alerts = []

        # Poor GPS quality
        if gps_data.quality == DataQuality.POOR:
            alerts.append(
                Alert(
                    level=AlertLevel.WARNING,
                    message="GPS signal quality degraded",
                    data_type="gps_quality",
                    source_address=gps_data.source_address,
                    timestamp=gps_data.timestamp,
                )
            )

        # Low satellite count
        if gps_data.satellite_count and gps_data.satellite_count < self.min_satellite_count:
            alerts.append(
                Alert(
                    level=AlertLevel.WARNING,
                    message=f"Low satellite count: {gps_data.satellite_count}",
                    data_type="gps_satellites",
                    source_address=gps_data.source_address,
                    timestamp=gps_data.timestamp,
                    value=float(gps_data.satellite_count),
                    threshold=float(self.min_satellite_count),
                )
            )

        # High HDOP (poor accuracy)
        if gps_data.hdop and gps_data.hdop > self.max_hdop:
            alerts.append(
                Alert(
                    level=AlertLevel.WARNING,
                    message=f"Poor GPS accuracy (HDOP: {gps_data.hdop:.1f})",
                    data_type="gps_hdop",
                    source_address=gps_data.source_address,
                    timestamp=gps_data.timestamp,
                    value=gps_data.hdop,
                    threshold=self.max_hdop,
                )
            )

        # Send alerts
        for alert in alerts:
            self._send_alert(alert)

    def _send_alert(self, alert: Alert) -> None:
        """Send alert to registered callbacks."""
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """Add an alert callback."""
        self._alert_callbacks.append(callback)


class CriticalDataAggregator:
    """Unified critical data aggregator and alerting system."""

    def __init__(self, codec: CANFrameCodec, error_handler: CANErrorHandler) -> None:
        """Initialize critical data aggregator.

        Parameters
        ----------
        codec : CANFrameCodec
            CAN frame codec
        error_handler : CANErrorHandler
            Error handling system
        """
        self.codec = codec
        self.error_handler = error_handler

        # Data handlers
        self.speed_handler = SpeedDataHandler(error_handler)
        self.fuel_handler = FuelDataHandler(error_handler)
        self.gps_handler = GPSDataHandler(error_handler)

        # Aggregated data storage
        self._current_data: dict[int, dict[str, Any]] = {}  # source_address -> data
        self._alert_history: list[Alert] = []

        # Callbacks
        self._data_callbacks: list[Callable[[int, dict[str, Any]], None]] = []
        self._alert_callbacks: list[Callable[[Alert], None]] = []

        # Setup alert forwarding
        self.speed_handler.add_alert_callback(self._handle_alert)
        self.fuel_handler.add_alert_callback(self._handle_alert)
        self.gps_handler.add_alert_callback(self._handle_alert)

    def process_message(self, decoded_msg: DecodedPGN) -> bool:
        """Process a decoded CAN message for critical data extraction.

        Parameters
        ----------
        decoded_msg : DecodedPGN
            Decoded CAN message

        Returns
        -------
        bool
            True if message was processed
        """
        try:
            processed = False
            source_address = decoded_msg.source_address

            # Ensure source address is tracked
            if source_address not in self._current_data:
                self._current_data[source_address] = {
                    "last_update": datetime.now(UTC),
                    "speed": None,
                    "fuel": None,
                    "gps": None,
                }

            # Process based on PGN
            if decoded_msg.pgn == 0xFEF1:  # Wheel-Based Vehicle Speed
                speed_data = self.speed_handler.process_speed_message(decoded_msg)
                if speed_data:
                    self._current_data[source_address]["speed"] = speed_data
                    processed = True

            elif decoded_msg.pgn == 0xFEF2:  # Fuel Economy
                fuel_data = self.fuel_handler.process_fuel_message(decoded_msg)
                if fuel_data:
                    self._current_data[source_address]["fuel"] = fuel_data
                    processed = True

            elif decoded_msg.pgn == 0xFEF3:  # Vehicle Position
                gps_data = self.gps_handler.process_gps_message(decoded_msg)
                if gps_data:
                    self._current_data[source_address]["gps"] = gps_data
                    processed = True

            if processed:
                self._current_data[source_address]["last_update"] = datetime.now(UTC)
                self._notify_data_update(source_address)

            return processed

        except Exception as e:
            logger.error(f"Failed to process critical data message: {e}")
            return False

    def get_current_data(self, source_address: int | None = None) -> dict[int, dict[str, Any]]:
        """Get current critical data for equipment.

        Parameters
        ----------
        source_address : int | None
            Specific source address, or None for all

        Returns
        -------
        dict[int, dict[str, Any]]
            Current critical data by source address
        """
        if source_address is not None:
            return {source_address: self._current_data.get(source_address, {})}
        return self._current_data.copy()

    def get_equipment_summary(self, source_address: int) -> dict[str, Any]:
        """Get comprehensive summary for a specific equipment.

        Parameters
        ----------
        source_address : int
            Equipment source address

        Returns
        -------
        dict[str, Any]
            Equipment summary
        """
        data = self._current_data.get(source_address, {})

        summary = {
            "source_address": source_address,
            "last_update": data.get("last_update"),
            "online": self._is_equipment_online(source_address),
            "speed": None,
            "fuel": None,
            "gps": None,
            "alerts": self._get_active_alerts(source_address),
            "overall_status": "unknown",
        }

        # Speed summary
        if data.get("speed"):
            speed_data = data["speed"]
            summary["speed"] = {
                "current_speed": speed_data.value,
                "working_speed": speed_data.working_speed,
                "quality": speed_data.quality.value,
            }

        # Fuel summary
        if data.get("fuel"):
            fuel_data = data["fuel"]
            summary["fuel"] = {
                "level_percent": fuel_data.fuel_level_percent,
                "consumption_rate": fuel_data.fuel_rate_lh,
                "remaining_liters": fuel_data.fuel_remaining_liters,
                "operational_mode": fuel_data.operational_mode,
            }

        # GPS summary
        if data.get("gps"):
            gps_data = data["gps"]
            summary["gps"] = {
                "latitude": gps_data.latitude,
                "longitude": gps_data.longitude,
                "quality": gps_data.quality.value,
                "field_id": gps_data.field_id,
                "satellite_count": gps_data.satellite_count,
            }

        # Overall status assessment
        summary["overall_status"] = self._assess_overall_status(source_address)

        return summary

    def _is_equipment_online(self, source_address: int) -> bool:
        """Check if equipment is considered online.

        Parameters
        ----------
        source_address : int
            Equipment source address

        Returns
        -------
        bool
            True if equipment is online
        """
        data = self._current_data.get(source_address, {})
        last_update = data.get("last_update")

        if not last_update:
            return False

        return (datetime.now(UTC) - last_update).total_seconds() < 30.0  # 30 second timeout

    def _get_active_alerts(self, source_address: int) -> list[dict[str, Any]]:
        """Get active alerts for equipment.

        Parameters
        ----------
        source_address : int
            Equipment source address

        Returns
        -------
        list[dict[str, Any]]
            Active alerts
        """
        # Get recent alerts (last 5 minutes)
        cutoff_time = datetime.now(UTC) - timedelta(minutes=5)
        recent_alerts = [
            alert
            for alert in self._alert_history
            if alert.source_address == source_address and alert.timestamp > cutoff_time
        ]

        return [
            {
                "level": alert.level.value,
                "message": alert.message,
                "data_type": alert.data_type,
                "timestamp": alert.timestamp,
                "value": alert.value,
                "threshold": alert.threshold,
            }
            for alert in recent_alerts
        ]

    def _assess_overall_status(self, source_address: int) -> str:
        """Assess overall equipment status.

        Parameters
        ----------
        source_address : int
            Equipment source address

        Returns
        -------
        str
            Overall status (healthy, warning, critical, offline)
        """
        if not self._is_equipment_online(source_address):
            return "offline"

        # Check for critical alerts
        active_alerts = self._get_active_alerts(source_address)
        critical_alerts = [alert for alert in active_alerts if alert["level"] == "critical"]
        warning_alerts = [alert for alert in active_alerts if alert["level"] == "warning"]

        if critical_alerts:
            return "critical"
        elif warning_alerts:
            return "warning"
        else:
            return "healthy"

    def _handle_alert(self, alert: Alert) -> None:
        """Handle incoming alert from data handlers.

        Parameters
        ----------
        alert : Alert
            Alert to handle
        """
        # Store alert in history
        self._alert_history.append(alert)

        # Cleanup old alerts (keep last 1000)
        if len(self._alert_history) > 1000:
            self._alert_history = self._alert_history[-1000:]

        # Forward to callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

    def _notify_data_update(self, source_address: int) -> None:
        """Notify callbacks of data update.

        Parameters
        ----------
        source_address : int
            Source address that was updated
        """
        data = self._current_data[source_address]
        for callback in self._data_callbacks:
            try:
                callback(source_address, data)
            except Exception as e:
                logger.error(f"Data callback error: {e}")

    def add_data_callback(self, callback: Callable[[int, dict[str, Any]], None]) -> None:
        """Add a data update callback.

        Parameters
        ----------
        callback : Callable[[int, dict[str, Any]], None]
            Data callback function
        """
        self._data_callbacks.append(callback)

    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """Add an alert callback.

        Parameters
        ----------
        callback : Callable[[Alert], None]
            Alert callback function
        """
        self._alert_callbacks.append(callback)
