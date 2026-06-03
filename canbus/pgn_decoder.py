"""PGN decoder for J1939 CAN bus live data."""

from typing import Dict, List, Tuple, Any


class PGNDecoder:
    """Decodes J1939 PGN data from CAN messages into human-readable values."""

    def __init__(self, pgn_channels: List[Dict[str, Any]]):
        """
        Initialise the decoder with a list of PGN channel definitions.

        Args:
            pgn_channels: List of channel dicts (pgn already parsed to int by config_loader)
        """
        self._channels = pgn_channels
        # Build lookup: pgn_int -> [channel, ...]
        self._pgn_map: Dict[int, List[Dict[str, Any]]] = {}
        for ch in pgn_channels:
            pgn_int = ch['pgn']  # already an int after config_loader processing
            self._pgn_map.setdefault(pgn_int, []).append(ch)

        # Ordered list of labels (preserves JSON order for GUI layout)
        self._labels: List[str] = [ch['label'] for ch in pgn_channels]

        # Format string lookup: label -> format
        self._formats: Dict[str, str] = {
            ch['label']: ch.get('format', '{:.1f}') for ch in pgn_channels
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def decode(self, can_id: int, data: List[int]) -> Dict[str, Tuple[float, str]]:
        """
        Decode a CAN message and return physical values for matching channels.

        Args:
            can_id: 29-bit J1939 CAN identifier
            data:   List of data bytes (as ints)

        Returns:
            Dict mapping label -> (physical_value, unit) for every channel
            whose PGN matches the received message.  Empty dict if no match.
        """
        received_pgn = self._extract_pgn(can_id)
        channels = self._pgn_map.get(received_pgn)
        if not channels:
            return {}

        result: Dict[str, Tuple[float, str]] = {}
        for ch in channels:
            try:
                raw = self._assemble_raw(data, ch['bytes'], ch.get('byte_order', 'little_endian'))
                if raw is None:
                    continue
                physical = raw * ch['scale'] + ch['offset']
                result[ch['label']] = (physical, ch['unit'])
            except Exception:
                # Skip any channel that fails (bad config, bad data, etc.)
                continue

        return result

    def get_channel_labels(self) -> List[str]:
        """Return all channel labels in definition order."""
        return list(self._labels)

    def get_format(self, label: str) -> str:
        """
        Return the format string for a channel label.

        Args:
            label: Channel label

        Returns:
            Python format string, e.g. '{:.0f}'.  Defaults to '{:.1f}'.
        """
        return self._formats.get(label, '{:.1f}')

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_pgn(can_id: int) -> int:
        """Extract PGN from a 29-bit J1939 CAN ID (bits 8-25)."""
        return (can_id >> 8) & 0x3FFFF

    @staticmethod
    def _assemble_raw(data: List[int], byte_indices: List[int], byte_order: str):
        """
        Assemble a raw integer from the specified byte indices.

        Args:
            data:         CAN message bytes
            byte_indices: Ordered list of byte indices to combine
            byte_order:   'little_endian' or 'big_endian'

        Returns:
            Assembled integer, or None if any index is out of range.
        """
        # Validate all indices before assembling
        for idx in byte_indices:
            if idx >= len(data):
                return None

        raw_bytes = [data[i] for i in byte_indices]

        if byte_order == 'big_endian':
            # MSB first
            value = 0
            for b in raw_bytes:
                value = (value << 8) | b
        else:
            # little_endian: first index is LSB
            value = 0
            for shift, b in enumerate(raw_bytes):
                value |= b << (8 * shift)

        return value
