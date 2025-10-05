"""CommunicationLossFailSafe - Network Partition Safety for Agricultural Fleet Coordination.

This module implements the CommunicationLossFailSafe system, which ensures safe
autonomous agricultural operations during network partitions and communication
failures between fleet coordination systems.

Agricultural Context
--------------------
Agricultural tractors often operate in rural areas with poor connectivity.
When network communication is lost between tractors, the system must:
- Detect communication health status accurately
- Implement safe fail-safe behaviors for different loss scenarios
- Maintain operational capability where safe to do so
- Restore coordination safely when connectivity returns

The system implements ISO 18497 fail-safe requirements for autonomous
agricultural equipment, ensuring no unsafe conditions during communication loss.

Implementation follows TDD GREEN phase - minimal implementation
to satisfy test requirements with agricultural domain focus.
"""

from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CommunicationLossType(Enum):
    """Types of communication loss scenarios in agricultural fleet operations."""

    SINGLE_TRACTOR_LOSS = "SINGLE_TRACTOR_LOSS"
    MULTIPLE_TRACTOR_LOSS = "MULTIPLE_TRACTOR_LOSS"
    COMPLETE_NETWORK_LOSS = "COMPLETE_NETWORK_LOSS"
    DEGRADED_CONNECTIVITY = "DEGRADED_CONNECTIVITY"
    EMERGENCY_WITH_LOSS = "EMERGENCY_WITH_LOSS"


class FailSafeMode(Enum):
    """Operational modes for communication loss fail-safe behavior."""

    FULL_CONNECTIVITY = "FULL_CONNECTIVITY"
    DEGRADED = "DEGRADED"
    ISOLATED = "ISOLATED"
    EMERGENCY_ISOLATED = "EMERGENCY_ISOLATED"


class CommunicationHealth:
    """Communication health status for agricultural fleet coordination."""

    def __init__(
        self,
        active_tractors: set[str],
        lost_tractors: set[str],
        overall_health_score: float,
        network_partition_detected: bool,
        loss_type: CommunicationLossType,
    ) -> None:
        """Initialize communication health status.

        Parameters
        ----------
        active_tractors : Set[str]
            Set of tractor IDs with active communication
        lost_tractors : Set[str]
            Set of tractor IDs with lost communication
        overall_health_score : float
            Overall fleet communication health (0.0 to 1.0)
        network_partition_detected : bool
            Whether network partition has been detected
        loss_type : CommunicationLossType
            Type of communication loss detected
        """
        self.active_tractors = active_tractors
        self.lost_tractors = lost_tractors
        self.overall_health_score = overall_health_score
        self.network_partition_detected = network_partition_detected
        self.loss_type = loss_type


class FailSafeAction:
    """Fail-safe actions to take during communication loss."""

    def __init__(
        self,
        continue_operations: bool,
        operational_mode: FailSafeMode,
        operational_speed_reduction: float,
        safety_margin_expansion_factor: float,
        safety_actions: list[str],
        requires_operator_intervention: bool,
    ) -> None:
        """Initialize fail-safe action plan.

        Parameters
        ----------
        continue_operations : bool
            Whether to continue autonomous operations
        operational_mode : FailSafeMode
            Operational mode to transition to
        operational_speed_reduction : float
            Speed reduction factor (0.0 to 1.0)
        safety_margin_expansion_factor : float
            Safety zone expansion factor (>= 1.0)
        safety_actions : List[str]
            List of safety actions to execute
        requires_operator_intervention : bool
            Whether operator intervention is required
        """
        self.continue_operations = continue_operations
        self.operational_mode = operational_mode
        self.operational_speed_reduction = operational_speed_reduction
        self.safety_margin_expansion_factor = safety_margin_expansion_factor
        self.safety_actions = safety_actions
        self.requires_operator_intervention = requires_operator_intervention


class RestorationProtocol:
    """Protocol for safely restoring communication after loss."""

    def __init__(
        self,
        state_sync_required: bool = True,
        crdt_merge_required: bool = True,
        vector_clock_update_required: bool = True,
        emergency_validation_required: bool = True,
        gradual_resumption_required: bool = True,
        expanded_safety_zones_during_restoration: bool = True,
        work_progress_validation_required: bool = False,
        estimated_restoration_time: float = 30.0,
    ) -> None:
        """Initialize restoration protocol.

        Parameters
        ----------
        state_sync_required : bool
            Whether fleet state synchronization is required
        crdt_merge_required : bool
            Whether CRDT merge is required
        vector_clock_update_required : bool
            Whether vector clock update is required
        emergency_validation_required : bool
            Whether emergency status validation is required
        gradual_resumption_required : bool
            Whether gradual operation resumption is required
        expanded_safety_zones_during_restoration : bool
            Whether to expand safety zones during restoration
        work_progress_validation_required : bool
            Whether work progress validation is required
        estimated_restoration_time : float
            Estimated time for full restoration (seconds)
        """
        self.state_sync_required = state_sync_required
        self.crdt_merge_required = crdt_merge_required
        self.vector_clock_update_required = vector_clock_update_required
        self.emergency_validation_required = emergency_validation_required
        self.gradual_resumption_required = gradual_resumption_required
        self.expanded_safety_zones_during_restoration = expanded_safety_zones_during_restoration
        self.work_progress_validation_required = work_progress_validation_required
        self.estimated_restoration_time = estimated_restoration_time


class SafeOperatingEnvelope:
    """Safe operating parameters based on communication health."""

    def __init__(
        self,
        max_autonomous_speed: float,
        min_safety_zone_radius: float,
        obstacle_detection_sensitivity: float,
        emergency_stop_threshold: float,
    ) -> None:
        """Initialize safe operating envelope.

        Parameters
        ----------
        max_autonomous_speed : float
            Maximum autonomous operation speed
        min_safety_zone_radius : float
            Minimum safety zone radius
        obstacle_detection_sensitivity : float
            Obstacle detection sensitivity level
        emergency_stop_threshold : float
            Threshold for emergency stop activation
        """
        self.max_autonomous_speed = max_autonomous_speed
        self.min_safety_zone_radius = min_safety_zone_radius
        self.obstacle_detection_sensitivity = obstacle_detection_sensitivity
        self.emergency_stop_threshold = emergency_stop_threshold


class CommunicationLossFailSafe:
    """Ensures safe agricultural operations during communication loss.

    The CommunicationLossFailSafe system monitors fleet communication health
    and implements appropriate fail-safe behaviors when tractors lose
    coordination capability during autonomous field operations.

    Agricultural Context
    --------------------
    This system addresses the reality of rural connectivity challenges
    in autonomous agricultural operations. It ensures that equipment
    failures, weather-related interference, or infrastructure issues
    do not result in unsafe or uncoordinated equipment behavior.

    Attributes
    ----------
    heartbeat_timeout : float
        Timeout for considering tractor communication lost
    emergency_timeout : float
        Timeout for emergency message acknowledgment
    degraded_threshold : float
        Message success rate threshold for degraded mode
    """

    def __init__(
        self,
        heartbeat_timeout: float = 5.0,
        emergency_timeout: float = 2.0,
        degraded_threshold: float = 0.5,
    ) -> None:
        """Initialize CommunicationLossFailSafe system.

        Parameters
        ----------
        heartbeat_timeout : float
            Timeout for heartbeat messages (seconds)
        emergency_timeout : float
            Timeout for emergency messages (seconds)
        degraded_threshold : float
            Success rate threshold for degraded connectivity

        Agricultural Context
        --------------------
        Timeouts must be tuned for rural connectivity conditions while
        maintaining safety requirements for autonomous equipment coordination.
        """
        self.heartbeat_timeout = heartbeat_timeout
        self.emergency_timeout = emergency_timeout
        self.degraded_threshold = degraded_threshold
        self.current_mode = FailSafeMode.FULL_CONNECTIVITY

        # Communication monitoring state
        self._last_health_check = time.time()
        self._communication_history: dict[str, list[float]] = {}

        logger.info(
            f"CommunicationLossFailSafe initialized: "
            f"heartbeat_timeout={heartbeat_timeout}s, "
            f"emergency_timeout={emergency_timeout}s, "
            f"degraded_threshold={degraded_threshold}"
        )

    def monitor_communication_health(
        self, isobus: Any, fleet_status: dict[str, dict[str, Any]]
    ) -> CommunicationHealth:
        """Monitor communication health across agricultural fleet.

        Parameters
        ----------
        isobus : Any
            ISOBUS communication interface
        fleet_status : Dict[str, Dict[str, Any]]
            Current status of all tractors in fleet

        Returns
        -------
        CommunicationHealth
            Current communication health assessment

        Agricultural Context
        --------------------
        Continuously assesses fleet communication health by analyzing
        heartbeat timeliness, message success rates, and response latencies
        to detect various communication failure scenarios.
        """
        current_time = time.time()
        active_tractors: set[str] = set()
        lost_tractors: set[str] = set()
        total_health_score = 0.0
        tractor_count = len(fleet_status)

        # Analyze each tractor's communication status
        for tractor_id, status in fleet_status.items():
            last_heartbeat = status.get("last_heartbeat", 0.0)
            message_success_rate = status.get("message_success_rate", 0.0)

            # Check if tractor is active based on heartbeat timeout
            time_since_heartbeat = current_time - last_heartbeat

            if time_since_heartbeat <= self.heartbeat_timeout and message_success_rate > 0.0:
                active_tractors.add(tractor_id)
                total_health_score += message_success_rate
            else:
                lost_tractors.add(tractor_id)

        # Calculate overall health score
        if tractor_count > 0:
            overall_health_score = total_health_score / tractor_count
        else:
            overall_health_score = 0.0

        # Determine loss type and network partition status
        network_partition_detected = (
            len(lost_tractors) > 0
        )  # Any tractor loss indicates potential partition
        loss_type = CommunicationLossType.SINGLE_TRACTOR_LOSS  # Default

        if tractor_count == 0:
            # No other tractors visible - complete isolation
            loss_type = CommunicationLossType.COMPLETE_NETWORK_LOSS
            network_partition_detected = True
        elif len(lost_tractors) == 0:
            # All tractors active, check for degraded connectivity
            if overall_health_score < self.degraded_threshold:
                loss_type = CommunicationLossType.DEGRADED_CONNECTIVITY
                network_partition_detected = False  # Not a partition, just degraded
            else:
                loss_type = CommunicationLossType.SINGLE_TRACTOR_LOSS  # Normal operation
                network_partition_detected = False  # Normal operation
        elif len(lost_tractors) == 1:
            loss_type = CommunicationLossType.SINGLE_TRACTOR_LOSS
            network_partition_detected = True
        elif len(lost_tractors) > 1:
            loss_type = CommunicationLossType.MULTIPLE_TRACTOR_LOSS
            network_partition_detected = True

        # Check for degraded connectivity in active tractors
        for tractor_id in active_tractors:
            success_rate = fleet_status[tractor_id].get("message_success_rate", 1.0)
            if success_rate < self.degraded_threshold:
                loss_type = CommunicationLossType.DEGRADED_CONNECTIVITY
                break

        health_status = CommunicationHealth(
            active_tractors=active_tractors,
            lost_tractors=lost_tractors,
            overall_health_score=overall_health_score,
            network_partition_detected=network_partition_detected,
            loss_type=loss_type,
        )

        self._last_health_check = current_time

        logger.debug(
            f"Communication health assessed: "
            f"active={len(active_tractors)}, lost={len(lost_tractors)}, "
            f"health_score={overall_health_score:.2f}, type={loss_type.value}"
        )

        return health_status

    async def handle_communication_loss(
        self, loss_type: CommunicationLossType, fleet_coordination: Any
    ) -> FailSafeAction:
        """Handle communication loss with appropriate fail-safe behavior.

        Parameters
        ----------
        loss_type : CommunicationLossType
            Type of communication loss detected
        fleet_coordination : Any
            Fleet coordination engine interface

        Returns
        -------
        FailSafeAction
            Fail-safe actions to execute

        Agricultural Context
        --------------------
        Implements graduated fail-safe responses based on the severity
        and type of communication loss, ensuring safety while maintaining
        agricultural productivity where possible.
        """
        if loss_type == CommunicationLossType.SINGLE_TRACTOR_LOSS:
            # Single tractor lost - continue with enhanced safety margins
            action = FailSafeAction(
                continue_operations=True,
                operational_mode=FailSafeMode.FULL_CONNECTIVITY,
                operational_speed_reduction=0.8,  # 20% speed reduction
                safety_margin_expansion_factor=1.5,  # 50% larger safety zones
                safety_actions=[
                    "expand safety zones",
                    "enhanced obstacle detection",
                    "monitor last known position",
                ],
                requires_operator_intervention=False,
            )

        elif loss_type == CommunicationLossType.MULTIPLE_TRACTOR_LOSS:
            # Multiple tractors lost - degraded mode operations
            self._transition_to_mode(FailSafeMode.DEGRADED)
            action = FailSafeAction(
                continue_operations=True,
                operational_mode=FailSafeMode.DEGRADED,
                operational_speed_reduction=0.5,  # 50% speed reduction
                safety_margin_expansion_factor=2.0,  # Double safety margins
                safety_actions=[
                    "enhanced local obstacle detection",
                    "reduce autonomous operation speed",
                    "conservative path planning",
                    "frequent position reporting",
                ],
                requires_operator_intervention=False,
            )

        elif loss_type == CommunicationLossType.COMPLETE_NETWORK_LOSS:
            # Complete isolation - stop autonomous operations
            self._transition_to_mode(FailSafeMode.ISOLATED)
            action = FailSafeAction(
                continue_operations=False,
                operational_mode=FailSafeMode.ISOLATED,
                operational_speed_reduction=0.0,  # Complete stop
                safety_margin_expansion_factor=1.0,
                safety_actions=[
                    "stop all autonomous operations",
                    "raise implements",
                    "engine idle",
                    "activate position beacon",
                    "await manual intervention",
                ],
                requires_operator_intervention=True,
            )

        elif loss_type == CommunicationLossType.DEGRADED_CONNECTIVITY:
            # Degraded connectivity - cautious continued operation
            self._transition_to_mode(FailSafeMode.DEGRADED)
            action = FailSafeAction(
                continue_operations=True,
                operational_mode=FailSafeMode.DEGRADED,
                operational_speed_reduction=0.7,  # 30% speed reduction
                safety_margin_expansion_factor=1.8,  # 80% larger safety zones
                safety_actions=[
                    "enhanced local obstacle detection",
                    "increase message retry attempts",
                    "conservative operation parameters",
                ],
                requires_operator_intervention=False,
            )

        elif loss_type == CommunicationLossType.EMERGENCY_WITH_LOSS:
            # Emergency during communication loss - maximum safety response
            self._transition_to_mode(FailSafeMode.EMERGENCY_ISOLATED)
            action = FailSafeAction(
                continue_operations=False,
                operational_mode=FailSafeMode.EMERGENCY_ISOLATED,
                operational_speed_reduction=0.0,
                safety_margin_expansion_factor=1.0,
                safety_actions=[
                    "execute local emergency stop",
                    "assume fleet-wide emergency",
                    "periodic emergency beacon",
                    "maximum visibility signals",
                    "await communication restoration",
                ],
                requires_operator_intervention=True,
            )

        else:
            # Default safe action for unknown scenarios
            action = FailSafeAction(
                continue_operations=False,
                operational_mode=FailSafeMode.ISOLATED,
                operational_speed_reduction=0.0,
                safety_margin_expansion_factor=1.0,
                safety_actions=["stop all operations", "await manual intervention"],
                requires_operator_intervention=True,
            )

        logger.info(
            f"Communication loss handled: {loss_type.value} -> {action.operational_mode.value}, "
            f"continue_ops={action.continue_operations}, intervention_required={action.requires_operator_intervention}"
        )

        return action

    def restore_communication(
        self, previous_mode: FailSafeMode, fleet_coordination: Any
    ) -> RestorationProtocol:
        """Restore fleet coordination after communication recovery.

        Parameters
        ----------
        previous_mode : FailSafeMode
            Previous fail-safe mode before restoration
        fleet_coordination : Any
            Fleet coordination engine interface

        Returns
        -------
        RestorationProtocol
            Protocol for safe communication restoration

        Agricultural Context
        --------------------
        Safe restoration requires careful state synchronization to avoid
        conflicts in field allocation, work progress, and safety status
        after network partitions are resolved.
        """
        # Determine restoration requirements based on previous mode
        if previous_mode in [FailSafeMode.ISOLATED, FailSafeMode.EMERGENCY_ISOLATED]:
            # Full restoration required for isolated modes
            restoration = RestorationProtocol(
                state_sync_required=True,
                crdt_merge_required=True,
                vector_clock_update_required=True,
                emergency_validation_required=True,
                gradual_resumption_required=True,
                expanded_safety_zones_during_restoration=True,
                work_progress_validation_required=False,
                estimated_restoration_time=45.0,
            )
        elif previous_mode == FailSafeMode.DEGRADED:
            # Moderate restoration for degraded mode
            restoration = RestorationProtocol(
                state_sync_required=True,
                crdt_merge_required=True,
                vector_clock_update_required=True,
                emergency_validation_required=True,
                gradual_resumption_required=True,
                expanded_safety_zones_during_restoration=True,
                work_progress_validation_required=True,
                estimated_restoration_time=25.0,
            )
        else:
            # Minimal restoration for maintained connectivity
            restoration = RestorationProtocol(
                state_sync_required=True,
                crdt_merge_required=False,
                vector_clock_update_required=True,
                emergency_validation_required=False,
                gradual_resumption_required=False,
                expanded_safety_zones_during_restoration=False,
                work_progress_validation_required=False,
                estimated_restoration_time=10.0,
            )

        # Transition back to full connectivity mode
        self._transition_to_mode(FailSafeMode.FULL_CONNECTIVITY)

        logger.info(
            f"Communication restoration initiated: previous_mode={previous_mode.value}, "
            f"estimated_time={restoration.estimated_restoration_time}s"
        )

        return restoration

    def calculate_safe_operating_envelope(
        self, communication_health: CommunicationHealth, current_operations: list[dict[str, Any]]
    ) -> SafeOperatingEnvelope:
        """Calculate safe operating parameters based on communication health.

        Parameters
        ----------
        communication_health : CommunicationHealth
            Current communication health status
        current_operations : List[Dict[str, Any]]
            Current agricultural operations being performed

        Returns
        -------
        SafeOperatingEnvelope
            Safe operating parameters for current conditions

        Agricultural Context
        --------------------
        Adjusts operational parameters based on communication reliability
        to maintain safety while preserving agricultural productivity
        where possible.
        """
        # Base parameters for normal operations
        base_speed = 8.0  # km/h
        base_safety_radius = 5.0  # meters
        base_detection_sensitivity = 0.5
        base_emergency_threshold = 0.8

        # Adjust parameters based on communication health
        health_factor = communication_health.overall_health_score
        connectivity_penalty = 1.0 - health_factor

        # Calculate adjusted parameters
        max_speed = max(2.0, base_speed * health_factor)  # Minimum 2 km/h
        safety_radius = base_safety_radius * (1.0 + connectivity_penalty * 2.0)
        detection_sensitivity = min(1.0, base_detection_sensitivity + connectivity_penalty)
        emergency_threshold = max(0.1, base_emergency_threshold - connectivity_penalty)

        # Apply additional penalties for lost tractors
        lost_count = len(communication_health.lost_tractors)
        if lost_count > 0:
            max_speed *= 1.0 - (lost_count * 0.1)  # 10% reduction per lost tractor
            safety_radius *= 1.0 + (lost_count * 0.2)  # 20% increase per lost tractor

        envelope = SafeOperatingEnvelope(
            max_autonomous_speed=max_speed,
            min_safety_zone_radius=safety_radius,
            obstacle_detection_sensitivity=detection_sensitivity,
            emergency_stop_threshold=emergency_threshold,
        )

        logger.debug(
            f"Safe operating envelope calculated: speed={max_speed:.1f}km/h, "
            f"safety_radius={safety_radius:.1f}m, sensitivity={detection_sensitivity:.2f}"
        )

        return envelope

    def _transition_to_mode(self, new_mode: FailSafeMode) -> None:
        """Transition to new fail-safe mode.

        Parameters
        ----------
        new_mode : FailSafeMode
            New mode to transition to

        Agricultural Context
        --------------------
        State machine transitions ensure appropriate safety measures
        are applied during different communication conditions.
        """
        old_mode = self.current_mode
        self.current_mode = new_mode

        logger.info(f"Fail-safe mode transition: {old_mode.value} -> {new_mode.value}")
