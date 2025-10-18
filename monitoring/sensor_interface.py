import json
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from afs_fastapi.monitoring.schemas import SensorDataSchema


class SensorInterface(ABC):
    """
    Abstract base class for a generic sensor interface module.
    """

    def __init__(self, device_id: str, sensor_type: str):
        self.device_id = device_id
        self.sensor_type = sensor_type
        self.is_connected = False
        self.schema = SensorDataSchema.get_schema(sensor_type)

    @abstractmethod
    def connect(self):
        """
        Establishes a connection to the sensor.
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        Closes the connection to the sensor.
        """
        pass

    @abstractmethod
    def read_data(self) -> dict:
        """
        Reads data from the sensor and returns it in a standardized format.
        """
        pass


class MQTTSensorInterface(SensorInterface):
    """
    Conceptual MQTT sensor interface.
    """

    def __init__(
        self,
        device_id: str,
        sensor_type: str,
        mqtt_broker: str = "localhost",
        mqtt_port: int = 1883,
    ):
        super().__init__(device_id, sensor_type)
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        # self.mqtt_client = paho.Client() # Conceptual: would use an actual MQTT client library

    def connect(self):
        print(
            f"Connecting to MQTT broker {self.mqtt_broker}:{self.mqtt_port} for device {self.device_id}..."
        )
        # self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
        # self.mqtt_client.loop_start()
        self.is_connected = True
        print("MQTT Sensor Connected.")

    def disconnect(self):
        print(f"Disconnecting MQTT for device {self.device_id}...")
        # self.mqtt_client.loop_stop()
        # self.mqtt_client.disconnect()
        self.is_connected = False
        print("MQTT Sensor Disconnected.")

    def read_data(self) -> dict:
        if not self.is_connected:
            raise ConnectionError("MQTT sensor not connected.")

        # Simulate reading data
        value = (
            round(random.uniform(0.1, 0.9), 2)
            if self.sensor_type == "soil_moisture"
            else round(random.uniform(15.0, 35.0), 2)
        )
        unit = "%" if self.sensor_type == "soil_moisture" else "°C"

        data: dict[str, Any] = {
            "timestamp": datetime.now().isoformat() + "Z",
            "device_id": self.device_id,
            "sensor_type": self.sensor_type,
            "value": value,
            "unit": unit,
            "metadata": {
                "location": {"latitude": 34.0522, "longitude": -118.2437},
            },
        }

        if self.sensor_type == "soil_moisture":
            data["metadata"]["depth_cm"] = random.randint(5, 30)
        elif self.sensor_type == "air_temperature":
            data["metadata"]["elevation_m"] = random.randint(50, 500)

        # In a real scenario, this would involve subscribing to an MQTT topic and receiving data
        # For now, we just return simulated data formatted according to the schema
        return data


class LoRaWANSensorInterface(SensorInterface):
    """
    Conceptual LoRaWAN sensor interface.
    """

    def __init__(self, device_id: str, sensor_type: str, lorawan_gateway_id: str = "GW-001"):
        super().__init__(device_id, sensor_type)
        self.lorawan_gateway_id = lorawan_gateway_id

    def connect(self):
        print(
            f"Connecting to LoRaWAN gateway {self.lorawan_gateway_id} for device {self.device_id}..."
        )
        # Conceptual: would involve LoRaWAN specific connection setup
        self.is_connected = True
        print("LoRaWAN Sensor Connected.")

    def disconnect(self):
        print(f"Disconnecting LoRaWAN for device {self.device_id}...")
        # Conceptual: would involve LoRaWAN specific disconnection
        self.is_connected = False
        print("LoRaWAN Sensor Disconnected.")

    def read_data(self) -> dict:
        if not self.is_connected:
            raise ConnectionError("LoRaWAN sensor not connected.")

        # Simulate reading data
        value = (
            round(random.uniform(0.1, 0.9), 2)
            if self.sensor_type == "soil_moisture"
            else round(random.uniform(15.0, 35.0), 2)
        )
        unit = "%" if self.sensor_type == "soil_moisture" else "°C"

        data: dict[str, Any] = {
            "timestamp": datetime.now().isoformat() + "Z",
            "device_id": self.device_id,
            "sensor_type": self.sensor_type,
            "value": value,
            "unit": unit,
            "metadata": {
                "location": {"latitude": 34.0522, "longitude": -118.2437},
            },
        }

        if self.sensor_type == "soil_moisture":
            data["metadata"]["depth_cm"] = random.randint(5, 30)
        elif self.sensor_type == "air_temperature":
            data["metadata"]["elevation_m"] = random.randint(50, 500)

        # In a real scenario, this would involve receiving data from a LoRaWAN network server
        # For now, we just return simulated data formatted according to the schema
        return data


# Example Usage:
if __name__ == "__main__":
    # MQTT Sensor Example
    mqtt_soil_sensor = MQTTSensorInterface(device_id="MQTT-SM-001", sensor_type="soil_moisture")
    mqtt_soil_sensor.connect()
    for _ in range(3):
        data = mqtt_soil_sensor.read_data()
        print(f"MQTT Soil Sensor Data: {json.dumps(data)}")
        time.sleep(1)
    mqtt_soil_sensor.disconnect()

    print("\n" + "=" * 30 + "\n")

    # LoRaWAN Sensor Example
    lorawan_air_sensor = LoRaWANSensorInterface(
        device_id="LoRa-AT-001", sensor_type="air_temperature"
    )
    lorawan_air_sensor.connect()
    for _ in range(3):
        data = lorawan_air_sensor.read_data()
        print(f"LoRaWAN Air Sensor Data: {json.dumps(data)}")
        time.sleep(1)
    lorawan_air_sensor.disconnect()
