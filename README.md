# CAN Bus Monitoring Application

A comprehensive Python application for monitoring CAN bus signals using PCAN drivers and PyQt5. This application provides automatic baud rate detection, configurable signal monitoring, and real-time message logging.

## Features

- **Professional Splash Screen**: Company logo displayed for 3 seconds on startup (configurable)
- **Automatic Baud Rate Detection**: Automatically detects the correct CAN bus baud rate (125k, 250k, 500k, 1000k)
- **Configuration Management**: Load and select from multiple monitoring configurations via JSON
- **Real-time Signal Monitoring**: Visual LED indicators showing signal match status (green = match, red = no match)
  - LED stays solid when condition is met (no flickering)
  - Updates only when match status changes
- **Three Signal Matching Types**:
  - **Exact Match**: Matches specific CAN ID with exact data pattern
  - **Exact Match with Mask**: Check only specific bytes using masks (ignore other bytes)
  - **Range Match**: Matches specific CAN ID with data byte value within a specified range
  - **Bit Match**: Monitors individual bits within a specific byte (e.g., check if bit 0 is set)
- **Live CAN Bus Logging**: Real-time display of all CAN messages with timestamp, ID, and data
- **User-Friendly GUI**: Clean PyQt5 interface with tabbed layout

## Prerequisites

### Hardware
- PCAN USB interface device (e.g., PCAN-USB, PEAK-System)
- CAN bus connection with active traffic

### Software
- Python 3.8 or higher
- PCAN drivers installed on your system

#### Installing PCAN Drivers

**Windows:**
1. Download PCAN drivers from [PEAK-System](https://www.peak-system.com/Drivers.523.0.html?&L=1)
2. Install the PCAN-Basic driver package
3. Restart your computer

**Linux:**
1. Install SocketCAN and PCAN driver:
   ```bash
   sudo apt-get install can-utils
   sudo modprobe peak_usb
   ```

**macOS:**
1. Download and install PCAN drivers from [PEAK-System](https://www.peak-system.com/Drivers.523.0.html?&L=1)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DRP1987/Canbus-monitoring.git
   cd Canbus-monitoring
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

```bash
python main.py
```

### Application Workflow

1. **Baud Rate Detection Screen**
   - Click "Detect Baud Rate" to automatically scan for the correct baud rate
   - The application will test common rates: 125k, 250k, 500k, 1000k
   - Once detected, click "Confirm" to proceed

2. **Configuration Selection Screen**
   - Select a monitoring configuration from the list
   - Click "Load Configuration" to start monitoring

3. **Monitoring Screen**
   - **Signal Status Tab**: Shows each configured signal with LED indicator
     - Green LED: Signal matched (CAN ID exists and data matches criteria)
     - Red LED: Signal not matched
   - **CAN Bus Log Tab**: Displays all received CAN messages in real-time
     - Format: `Timestamp | CAN ID | Data bytes`
   - Click "Clear Log" to clear the message log

## Configuration File

### Structure

The application uses `configurations.json` to define monitoring configurations. Each configuration contains multiple signals to monitor.

### Hexadecimal Format Support

**NEW**: Configuration files now support hexadecimal notation with the `0x` prefix, which is more intuitive for CAN bus users.

You can use:
- **Hexadecimal strings**: `"0x123"`, `"0xFF"`, `"0xAA"`
- **Decimal integers**: `291`, `255`, `170`
- **Mixed format**: Both in the same configuration

This applies to:
- `can_id` field
- `data` array elements
- `min_value` and `max_value` for range matches

### Example Configuration

```json
{
  "configurations": [
    {
      "name": "Configuration 1",
      "signals": [
        {
          "name": "Signal 1",
          "can_id": "0x123",
          "match_type": "exact",
          "data": ["0xAA", "0x02", 3, 4, "0x05", 6, 7, 8]
        },
        {
          "name": "Signal 2",
          "can_id": "0x456",
          "match_type": "range",
          "data_byte_index": 0,
          "min_value": "0x0A",
          "max_value": "0x32"
        }
      ]
    }
  ]
}
```

### Signal Types

#### Exact Match Signal
Matches when CAN ID and all data bytes match exactly.

```json
{
  "name": "Signal Name",
  "can_id": "0x123",
  "match_type": "exact",
  "data": ["0x01", "0x02", "0x03", "0x04", "0x05", "0x06", "0x07", "0x08"]
}
```

Or using decimal (backward compatible):
```json
{
  "name": "Signal Name",
  "can_id": 291,
  "match_type": "exact",
  "data": [1, 2, 3, 4, 5, 6, 7, 8]
}
```

#### Exact Match Signal with Mask
Matches specific bytes while ignoring others using a mask. This is useful when you only care about certain bytes in the CAN message.

```json
{
  "name": "Signal Name",
  "can_id": "0x119",
  "match_type": "exact",
  "data": ["0x00", "0x00", "0x00", "0x29", "0x00", "0x00", "0x00", "0x00"],
  "mask": ["0x00", "0x00", "0x00", "0xFF", "0x00", "0x00", "0x00", "0x00"]
}
```

**How masks work:**
- `0xFF` (255): Check this byte completely - all bits must match
- `0x00` (0): Ignore this byte completely
- Other values: Partial bit masking (e.g., `0x0F` checks only lower 4 bits)

In the example above:
- Bytes 0, 1, 2, 4, 5, 6, 7: Ignored (mask = 0x00)
- Byte 3: Must equal 0x29 (mask = 0xFF)

This signal will match any message with CAN ID 0x119 where byte 3 equals 0x29, regardless of what the other bytes contain.

#### Range Match Signal
Matches when CAN ID exists and a specific data byte is within the defined range.

```json
{
  "name": "Signal Name",
  "can_id": "0x456",
  "match_type": "range",
  "data_byte_index": 0,
  "min_value": "0x0A",
  "max_value": "0x32"
}
```

Or using decimal:
```json
{
  "name": "Signal Name",
  "can_id": 1110,
  "match_type": "range",
  "data_byte_index": 0,
  "min_value": 10,
  "max_value": 50
}
```

#### Bit Match Signal
Matches when a specific bit within a byte has the expected value. This is useful for monitoring individual status flags or control bits.

```json
{
  "name": "Signal Name",
  "can_id": "0x119",
  "match_type": "bit",
  "byte_index": 3,
  "bit_index": 0,
  "bit_value": 1
}
```

**How bit matching works:**
- `byte_index`: The byte position in the CAN message (0-7)
- `bit_index`: The bit position within the byte (0-7, where 0 is LSB)
- `bit_value`: The expected bit value (0 or 1)

In the example above:
- Monitors CAN ID 0x119
- Checks byte 3, bit 0 (LSB)
- LED turns green when bit 0 = 1
- LED turns red when bit 0 = 0

This is particularly useful for monitoring status flags like:
- Engine status bits
- Door open/close indicators
- Warning light states
- Any binary on/off condition encoded in a CAN message

### Adding Custom Configurations

1. Edit `configurations.json`
2. Add a new configuration object to the `configurations` array
3. Define signals with appropriate match types (exact, range, or bit)
4. Use hexadecimal (`"0x..."`) or decimal format for values
5. Save the file and restart the application

## Project Structure

```
canbus-monitoring/
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # Documentation
├── configurations.json              # Signal configurations
├── assets/
│   ├── icon.png                     # Application icon (Linux/Mac)
│   ├── icon.ico                     # Application icon (Windows)
│   ├── logo.png                     # Splash screen logo
│   └── README.md                    # Assets customization guide
├── gui/
│   ├── __init__.py
│   ├── main_window.py              # Main application window
│   ├── baudrate_screen.py          # Baud rate detection screen
│   ├── config_selection_screen.py  # Configuration selection screen
│   ├── monitoring_screen.py        # Signal monitoring with tabs
│   ├── splash_screen.py            # Startup splash screen
│   └── widgets.py                  # Custom widgets (LED indicator)
├── canbus/
│   ├── __init__.py
│   ├── pcan_interface.py           # PCAN driver interface
│   └── signal_matcher.py           # Signal matching logic
└── config/
    ├── __init__.py
    ├── app_config.py               # Application settings
    └── config_loader.py            # JSON configuration loader
```

## Customization

### Splash Screen

The application displays a professional splash screen with your company logo on startup.

**To customize the splash screen:**

1. Replace `assets/logo.png` with your company logo (recommended: 400x400 to 800x800 pixels)
2. Edit `config/app_config.py` to adjust settings:
   ```python
   SPLASH_DURATION = 3000        # Display time in milliseconds (3 seconds)
   SHOW_SPLASH_SCREEN = True     # Set to False to disable splash screen
   ```

**Splash Screen Features:**
- Displays company branding on startup
- Configurable duration (default: 3 seconds)
- Frameless, centered design
- Graceful fallback if logo is missing
- Can be disabled via configuration

### Application Icon and Logo

See `assets/README.md` for detailed instructions on customizing:
- Application window icon
- Splash screen logo
- Icon sizes and formats

## Troubleshooting

### Issue: "Failed to connect to CAN bus"
**Solution:**
- Ensure PCAN device is properly connected to USB
- Check that PCAN drivers are installed correctly
- Verify CAN bus has proper termination (120Ω resistors)
- Try reconnecting the PCAN device

### Issue: "Baud rate detection failed"
**Solution:**
- Ensure there is active CAN traffic on the bus
- Check physical connections to CAN bus
- Verify bus termination is correct
- Try manually connecting at a known baud rate by modifying the code

### Issue: "Configuration file not found"
**Solution:**
- Ensure `configurations.json` exists in the same directory as `main.py`
- Check file permissions
- Verify JSON syntax is correct

### Issue: "No configurations found"
**Solution:**
- Open `configurations.json` and verify it contains valid configurations
- Check JSON syntax using a JSON validator
- Ensure the file structure matches the example above

### Issue: Python package import errors
**Solution:**
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
- Ensure you're using Python 3.8 or higher: `python --version`
- Try using a virtual environment

## Development

### Code Style
- Follows PEP 8 Python style guidelines
- Docstrings for all classes and methods
- Type hints for function parameters and returns

### Thread Safety
- GUI updates use Qt signals/slots for thread-safe communication
- CAN message reception runs in a background thread
- Proper synchronization between CAN interface and GUI

## License

This project is open-source and available for modification and distribution.

## Author

DRP1987

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository. 
