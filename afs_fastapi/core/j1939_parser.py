import logging

from .j1939_specs import PGN_SPECS

logger = logging.getLogger(__name__)


def parse_j1939_message(pgn: int, data: list[int]) -> dict[str, float] | None:
    """
    Parses a J1939 message and returns a dictionary of parsed SPN data.

    Args:
        pgn: The Parameter Group Number of the message.
        data: The data payload of the message as a list of bytes.

    Returns:
        A dictionary of parsed SPN data, or None if the PGN is not supported.
    """
    if pgn not in PGN_SPECS:
        logger.warning(f"Unrecognized PGN: {pgn}")
        return None

    parsed_data: dict[str, float] = {}
    spn_specs = PGN_SPECS[pgn]

    for spec in spn_specs:
        if spec.byte_offset + spec.length > len(data):
            continue

        raw_value = 0
        for i in range(spec.length):
            raw_value += data[spec.byte_offset + i] << (8 * i)

        scaled_value = raw_value * spec.scale + spec.offset

        if not (spec.min_value <= scaled_value <= spec.max_value):
            return None  # Validation failed

        parsed_data[spec.name] = scaled_value

    return parsed_data
