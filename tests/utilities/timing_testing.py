"""
Timing utilities for testing without mocks.

This module provides utilities for testing time-based functionality
without mocking time.time(), using timing with controlled delays.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from collections.abc import Callable


@dataclass
class TimeSnapshot:
    """Represents a point in time with associated test data."""

    timestamp: float
    test_data: dict[str, Any]


class TimeTestController:
    """Controller for time-based tests using timing without mocks."""

    def __init__(self, precision: float = 0.01) -> None:
        """Initialize time test controller.

        Parameters
        ----------
        precision : float, default 0.01
            Precision for timing assertions in seconds
        """
        self.precision = precision
        self.snapshots: list[TimeSnapshot] = []
        self._start_time = time.time()

    def get_timestamp(self) -> float:
        """Get current timestamp relative to test start."""
        return time.time() - self._start_time

    def take_snapshot(self, test_data: dict[str, Any] | None = None) -> TimeSnapshot:
        """Take a timestamp snapshot with optional test data.

        Parameters
        ----------
        test_data : Dict[str, Any], optional
            Test data to associate with this timestamp

        Returns
        -------
        TimeSnapshot
            Snapshot of current time and data
        """
        snapshot = TimeSnapshot(timestamp=self.get_timestamp(), test_data=test_data or {})
        self.snapshots.append(snapshot)
        return snapshot

    def wait_until(self, target_time: float) -> float:
        """Wait until a specific relative time is reached.

        Parameters
        ----------
        target_time : float
            Target time relative to test start in seconds

        Returns
        -------
        float
            Actual timestamp when wait completed
        """
        current = self.get_timestamp()
        if current < target_time:
            time.sleep(target_time - current)
        return self.get_timestamp()

    def wait_for_duration(self, duration: float) -> float:
        """Wait for a specific duration.

        Parameters
        ----------
        duration : float
            Duration to wait in seconds

        Returns
        -------
        float
            Timestamp after waiting
        """
        time.sleep(duration)
        return self.get_timestamp()

    def assert_time_between(
        self, actual: float, expected: float, tolerance: float | None = None
    ) -> None:
        """Assert that a time is within tolerance of expected value.

        Parameters
        ----------
        actual : float
            Actual timestamp
        expected : float
            Expected timestamp
        tolerance : float, optional
            Tolerance for assertion (uses controller precision if None)
        """
        tol = tolerance or self.precision
        assert (
            abs(actual - expected) <= tol
        ), f"Time {actual} not within {tol} of expected {expected}"

    def assert_time_after(self, actual: float, minimum: float) -> None:
        """Assert that a time is after minimum threshold.

        Parameters
        ----------
        actual : float
            Actual timestamp
        minimum : float
            Minimum expected timestamp
        """
        assert actual >= minimum, f"Time {actual} is before minimum {minimum}"

    def get_interval_between_snapshots(self, index1: int, index2: int) -> float:
        """Get time interval between two snapshots.

        Parameters
        ----------
        index1 : int
            Index of first snapshot
        index2 : int
            Index of second snapshot

        Returns
        -------
        float
            Time interval between snapshots
        """
        if index1 >= len(self.snapshots) or index2 >= len(self.snapshots):
            raise IndexError("Snapshot index out of range")

        return self.snapshots[index2].timestamp - self.snapshots[index1].timestamp


class DeterministicTimer:
    """Timer that provides deterministic behavior without mocking system time."""

    def __init__(self, initial_time: float = 0.0) -> None:
        """Initialize deterministic timer.

        Parameters
        ----------
        initial_time : float, default 0.0
            Initial timer value in seconds
        """
        self._initial_offset = time.time() - initial_time
        self._adjustments: list[float] = []

    def get_time(self) -> float:
        """Get current timer value."""
        return time.time() - self._initial_offset + sum(self._adjustments)

    def advance_time(self, duration: float) -> float:
        """Advance the timer by a specific duration.

        This simulates time passage without actually sleeping,
        useful for testing timing-dependent logic.

        Parameters
        ----------
        duration : float
            Duration to advance time by in seconds

        Returns
        -------
        float
            New timer value
        """
        self._adjustments.append(duration)
        return self.get_time()

    def reset_to(self, target_time: float) -> float:
        """Reset timer to specific target time.

        Parameters
        ----------
        target_time : float
            Target time value in seconds

        Returns
        -------
        float
            New timer value
        """
        current_real = time.time()
        self._initial_offset = current_real - target_time
        self._adjustments = []
        return self.get_time()


def run_timing_test(
    test_func: Callable[[TimeTestController], Any], max_duration: float = 10.0
) -> Any:
    """Run a timing test with time control.

    Parameters
    ----------
    test_func : Callable[[TimeTestController], Any]
        Test function that receives a time controller
    max_duration : float, default 10.0
        Maximum test duration in seconds

    Returns
    -------
    Any
        Result from test function
    """
    controller = TimeTestController()
    start_time = time.time()

    try:
        result = test_func(controller)

        # Ensure test doesn't run too long
        actual_duration = time.time() - start_time
        if actual_duration > max_duration:
            raise AssertionError(
                f"Timing test exceeded maximum duration: {actual_duration:.2f}s > {max_duration:.2f}s"
            )

        return result

    except Exception as e:
        # Add timing context to any test failure
        raise RuntimeError(f"Timing test failed after {time.time() - start_time:.2f}s: {e}") from e


# Convenience functions for common time testing patterns
def assert_retry_timing(
    test_tracker: Any, expected_interval: float, tolerance: float = 0.01
) -> None:
    """Assert that retry timing is correct without mocking time.

    Parameters
    ----------
    test_tracker : Any
        Object with retry queue and timing logic
    expected_interval : float
        Expected retry interval in seconds
    tolerance : float, default 0.01
        Timing tolerance in seconds
    """
    controller = TimeTestController()

    # Track message and note scheduling time
    start_time = controller.get_timestamp()

    # Extract retry time from tracker implementation
    if hasattr(test_tracker, "_retry_queue") and test_tracker._retry_queue:
        retry_time, _, _, _ = test_tracker._retry_queue[0]

        # Calculate actual interval
        actual_interval = retry_time - start_time

        # Assert timing is correct
        assert abs(actual_interval - expected_interval) <= tolerance, (
            f"Retry interval {actual_interval:.3f}s not within {tolerance:.3f}s "
            f"of expected {expected_interval:.3f}s"
        )
    else:
        raise AssertionError("No retry queue found or queue is empty")


def simulate_message_delivery(controller: TimeTestController, delays: list[float]) -> list[float]:
    """Simulate message delivery with specified delays.

    Parameters
    ----------
    controller : TimeTestController
        Time controller for the simulation
    delays : List[float]
        List of delays for each message delivery

    Returns
    -------
    List[float]
        Actual delivery timestamps
    """
    delivery_times = []

    for delay in delays:
        delivery_time = controller.wait_for_duration(delay)
        delivery_times.append(delivery_time)

    return delivery_times
