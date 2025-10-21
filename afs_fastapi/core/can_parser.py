from typing import Any

from .j1939_parser import parse_j1939_message


class CanParser:
    def __init__(self) -> None:
        pass

    def parse_message(self, pgn: int, data: list[int]) -> dict[str, Any] | None:
        parsed_data = parse_j1939_message(pgn, data)

        if parsed_data is None:
            return None

        return {
            "pgn": pgn,
            "parsed_data": parsed_data,
        }
