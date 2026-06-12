"""Configuration loader for CAN bus monitoring configurations."""

import json
import os
from typing import List, Dict, Any, Union
from utils.resource_path import resource_path


class ConfigurationLoader:
    """Loads and manages CAN bus monitoring configurations from JSON files."""

    def __init__(self, config_file: str = "config/configurations.json"):
        """
        Initialize the configuration loader.

        Args:
            config_file: Path to the JSON configuration file
        """
        # Use resource_path for PyInstaller compatibility
        self.config_file = resource_path(config_file)
        self.configurations = []

    def _parse_value(self, value: Union[str, int]) -> int:
        """
        Parse a value that can be either an integer or a hex string.
        
        Args:
            value: Integer or hex string (e.g., 291 or "0x123")
        
        Returns:
            Integer value
        
        Raises:
            ValueError: If value type is invalid or cannot be parsed
        """
        if isinstance(value, str):
            # Handle hex string (e.g., "0x123" or "0xFF")
            if value.lower().startswith('0x'):
                try:
                    return int(value, 16)
                except ValueError:
                    raise ValueError(f"Invalid hex string: {value}")
            else:
                # Handle decimal string (e.g., "291")
                try:
                    return int(value)
                except ValueError:
                    raise ValueError(f"Invalid decimal string: {value}")
        elif isinstance(value, int):
            # Already an integer
            return value
        else:
            raise ValueError(f"Invalid value type: {type(value)}. Expected int or hex string.")

    def load_configurations(self) -> List[Dict[str, Any]]:
        """
        Load configurations from JSON file.

        Returns:
            List of configuration dictionaries

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")

        with open(self.config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.configurations = data.get('configurations', [])
        
        # Parse hex values in configurations and validate info_pdf paths
        for config in self.configurations:
            if 'signals' in config:
                for signal in config['signals']:
                    # Parse CAN ID (support both hex string and decimal)
                    if 'can_id' in signal:
                        signal['can_id'] = self._parse_value(signal['can_id'])
                    
                    # Parse data array (support both hex strings and decimals)
                    if 'data' in signal and isinstance(signal['data'], list):
                        signal['data'] = [
                            self._parse_value(val) for val in signal['data']
                        ]
                    
                    # Parse mask array (support both hex strings and decimals)
                    if 'mask' in signal and isinstance(signal['mask'], list):
                        signal['mask'] = [
                            self._parse_value(val) for val in signal['mask']
                        ]
                    
                    # Parse range values (support both hex strings and decimals)
                    if 'min_value' in signal:
                        signal['min_value'] = self._parse_value(signal['min_value'])
                    if 'max_value' in signal:
                        signal['max_value'] = self._parse_value(signal['max_value'])
                    
                    # Parse bit match values (support both hex strings and decimals)
                    if 'byte_index' in signal:
                        signal['byte_index'] = self._parse_value(signal['byte_index'])
                    if 'bit_index' in signal:
                        signal['bit_index'] = self._parse_value(signal['bit_index'])
                    if 'bit_value' in signal:
                        signal['bit_value'] = self._parse_value(signal['bit_value'])

            # Parse pgn_channels: convert pgn hex string to int
            for channel in config.get('pgn_channels', []):
                if 'pgn' in channel:
                    channel['pgn'] = self._parse_value(channel['pgn'])
        
        return self.configurations

    def get_configuration_names(self) -> List[str]:
        """
        Get list of configuration names.

        Returns:
            List of configuration names
        """
        return [config.get('name', 'Unnamed') for config in self.configurations]

    def get_configuration_by_name(self, name: str) -> Dict[str, Any]:
        """
        Get configuration by name.

        Args:
            name: Configuration name

        Returns:
            Configuration dictionary or None if not found
        """
        for config in self.configurations:
            if config.get('name') == name:
                return config
        return None

    def validate_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration structure.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(config, dict):
            return False

        if 'name' not in config or 'signals' not in config:
            return False

        if not isinstance(config['signals'], list):
            return False

        for signal in config['signals']:
            if not self._validate_signal(signal):
                return False

        return True

    def _validate_signal(self, signal: Dict[str, Any]) -> bool:
        """
        Validate individual signal configuration.

        Args:
            signal: Signal dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['name', 'can_id', 'match_type']
        for field in required_fields:
            if field not in signal:
                return False

        match_type = signal['match_type']
        if match_type == 'exact':
            if 'data' not in signal or not isinstance(signal['data'], list):
                return False
        elif match_type == 'range':
            # Accept either 'byte_index' or 'data_byte_index' for backwards compatibility
            has_byte_index = 'byte_index' in signal or 'data_byte_index' in signal
            if not has_byte_index:
                return False
            if 'min_value' not in signal or 'max_value' not in signal:
                return False
        elif match_type == 'bit':
            required_bit_fields = ['byte_index', 'bit_index', 'bit_value']
            for field in required_bit_fields:
                if field not in signal:
                    return False
        else:
            return False

        return True
