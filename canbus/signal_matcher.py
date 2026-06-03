"""Signal matching logic for CAN bus messages."""

from typing import Dict, Any, List


class SignalMatcher:
    """Matches received CAN messages against configured signal definitions."""

    @staticmethod
    def _extract_pgn(can_id: int) -> int:
        """
        Extract PGN (Parameter Group Number) from a 29-bit J1939 CAN ID.
        
        J1939 CAN ID structure (29-bit):
        - Bits 0-7: Source Address
        - Bits 8-25: PGN (Parameter Group Number)
        - Bits 26-28: Priority
        
        Args:
            can_id: 29-bit CAN identifier
            
        Returns:
            18-bit PGN value extracted from bits 8-25
        """
        # Extract bits 8-25 (shift right by 8, mask with 0x3FFFF to get 18 bits)
        pgn = (can_id >> 8) & 0x3FFFF
        return pgn

    @staticmethod
    def match_signal(signal_config: Dict[str, Any], can_id: int, data: List[int]) -> bool:
        """
        Check if a received CAN message matches the signal configuration.

        Args:
            signal_config: Signal configuration dictionary (with parsed integer values)
            can_id: Received CAN message ID
            data: Received CAN message data bytes

        Returns:
            True if message matches signal configuration, False otherwise
        """
        # Get config CAN ID (already parsed to int by ConfigurationLoader)
        config_can_id = signal_config.get('can_id')
        
        # Check protocol type for J1939 PGN matching
        protocol = signal_config.get('protocol', None)
        
        if protocol == 'j1939':
            # For J1939, match by PGN only (ignore priority and source address)
            received_pgn = SignalMatcher._extract_pgn(can_id)
            config_pgn = SignalMatcher._extract_pgn(config_can_id)
            
            if received_pgn != config_pgn:
                return False
        else:
            # Standard CAN matching - exact CAN ID match
            if can_id != config_can_id:
                return False

        # Check match type
        match_type = signal_config.get('match_type', 'exact')

        if match_type == 'exact':
            return SignalMatcher._match_exact(signal_config, data)
        elif match_type == 'range':
            return SignalMatcher._match_range(signal_config, data)
        elif match_type == 'bit':
            # Check individual bit within a specific byte
            return SignalMatcher._match_bit(signal_config, data)
        else:
            return False

    @staticmethod
    def _match_exact(signal_config: Dict[str, Any], data: List[int]) -> bool:
        """
        Check for exact data match with optional mask support.

        Args:
            signal_config: Signal configuration dictionary
            data: Received CAN message data bytes

        Returns:
            True if data matches exactly (or matches with mask), False otherwise
        """
        expected_data = signal_config.get('data', [])
        mask = signal_config.get('mask', None)

        # If mask is provided, apply it to both expected and received data
        if mask is not None:
            if len(mask) != len(expected_data) or len(data) != len(expected_data):
                return False
            
            # Compare only masked bits
            for i in range(len(expected_data)):
                if (data[i] & mask[i]) != (expected_data[i] & mask[i]):
                    return False
            return True
        
        # Check if data matches exactly (Python handles element-wise comparison)
        return data == expected_data

    @staticmethod
    def _match_range(signal_config: Dict[str, Any], data: List[int]) -> bool:
        """
        Check if specific byte is within configured range.

        Args:
            signal_config: Signal configuration dictionary
            data: Received CAN message data bytes

        Returns:
            True if byte value is within range, False otherwise
        """
        # Support both 'byte_index' and 'data_byte_index' for backwards compatibility
        byte_index = signal_config.get('byte_index', signal_config.get('data_byte_index', 0))
        min_value = signal_config.get('min_value', 0)
        max_value = signal_config.get('max_value', 255)

        # Check if byte index is valid
        if byte_index >= len(data):
            return False

        # Check if value is within range
        byte_value = data[byte_index]
        return min_value <= byte_value <= max_value

    @staticmethod
    def _match_bit(signal_config: Dict[str, Any], data: List[int]) -> bool:
        """
        Check if a specific bit within a byte matches the expected value.

        Args:
            signal_config: Signal configuration dictionary
            data: Received CAN message data bytes

        Returns:
            True if bit matches expected value, False otherwise
        """
        byte_index = signal_config.get('byte_index', 0)
        bit_index = signal_config.get('bit_index', 0)
        bit_value = signal_config.get('bit_value', 0)

        # Check if byte index is valid
        if byte_index >= len(data):
            return False

        # Check if bit index is valid (0-7)
        if bit_index < 0 or bit_index > 7:
            return False

        # Get the byte value
        byte_value = data[byte_index]

        # Extract the specific bit (bit 0 is LSB)
        actual_bit = (byte_value >> bit_index) & 1

        # Check if bit matches expected value
        return actual_bit == bit_value
