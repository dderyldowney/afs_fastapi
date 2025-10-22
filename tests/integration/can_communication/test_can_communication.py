import threading
import time

from tests.integration.can_communication.platform_test import platform_test
from tests.integration.can_communication.tractor_simulator import tractor_simulator


def test_can_communication():
    """Tests the CAN communication integration scenario."""
    # Start the tractor simulator in a separate thread
    tractor_thread = threading.Thread(target=tractor_simulator)
    tractor_thread.start()

    # Give the simulator a moment to start up
    time.sleep(1)

    # Run the platform test
    platform_test()

    # Wait for the tractor simulator to finish
    tractor_thread.join(timeout=5)

    # Assert that the tractor simulator thread has finished
    assert not tractor_thread.is_alive()
