from typing import Any


class CanParser:
    def __init__(self) -> None:
        pass

    def parse_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        pgn = message["pgn"]
        spn = message["spn"]
        value = message["value"]
        data_type = message["data_type"]

        parsed_data = {}

        if pgn == 61444 and spn == 190:  # Engine Speed
            if not (0 <= value <= 8191.875):
                return None
            parsed_data["engine_speed"] = value
        elif pgn == 65265 and spn == 84:  # Vehicle Speed
            parsed_data["vehicle_speed"] = value
        elif pgn == 65276 and spn == 96:  # Fuel Level
            parsed_data["fuel_level"] = value
        elif pgn == 65267 and spn == 162:  # GPS Coordinates (Latitude, simplified)
            parsed_data["gps_coordinates"] = value  # Simplified for now
        else:
            return None  # Unknown PGN/SPN combination

        return {
            "pgn": pgn,
            "spn": spn,
            "value": value,
            "data_type": data_type,
            "parsed_data": parsed_data,
        }
