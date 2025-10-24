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
        SPNs with out-of-range values are skipped rather than failing the entire message.
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

        # Skip SPNs with out-of-range values rather than failing entire message
        # This allows partial parsing when some SPNs have invalid/not-available data
        if not (spec.min_value <= scaled_value <= spec.max_value):
            logger.debug(
                f"SPN {spec.spn} ({spec.name}) value {scaled_value} "
                f"out of range [{spec.min_value}, {spec.max_value}], skipping"
            )
            continue

        parsed_data[spec.name] = scaled_value

    # Return parsed data if at least one SPN was successfully parsed
    return parsed_data if parsed_data else None
