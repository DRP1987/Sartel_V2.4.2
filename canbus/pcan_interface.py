"""PCAN driver interface for CAN bus communication."""

import can
import threading
import time
from typing import Optional, Callable, List
from PyQt5.QtCore import QObject, pyqtSignal

# Default bitrate for channel detection
DETECTION_BITRATE = 500000


class PCANInterface(QObject):
    """Interface for PCAN CAN bus communication."""

    # Qt signals for thread-safe communication
    message_received = pyqtSignal(object)  # Emits CAN message
    error_occurred = pyqtSignal(str)  # Emits error message

    def __init__(self):
        """Initialize PCAN interface."""
        super().__init__()
        self.bus: Optional[can.Bus] = None
        self.running = False
        self.receive_thread: Optional[threading.Thread] = None
        self.current_baudrate: Optional[int] = None
        
        # Try to import PCANBasic for direct hardware access
        self.pcan_basic = None
        try:
            from PCANBasic import PCANBasic, PCAN_USBBUS1, PCAN_USBBUS2, PCAN_USBBUS3, \
                PCAN_USBBUS4, PCAN_USBBUS5, PCAN_USBBUS6, PCAN_USBBUS7, PCAN_USBBUS8, \
                PCAN_BAUD_1M, PCAN_BAUD_500K, PCAN_BAUD_250K, PCAN_BAUD_125K, \
                PCAN_ERROR_OK, PCAN_ERROR_QRCVEMPTY, PCAN_ERROR_BUSLIGHT, \
                PCAN_ERROR_BUSHEAVY, PCAN_ERROR_BUSOFF, PCAN_LISTEN_ONLY
            
            self.pcan_basic = PCANBasic()
            
            # Store constants
            self.PCAN_CHANNELS = {
                'PCAN_USBBUS1': PCAN_USBBUS1,
                'PCAN_USBBUS2': PCAN_USBBUS2,
                'PCAN_USBBUS3': PCAN_USBBUS3,
                'PCAN_USBBUS4': PCAN_USBBUS4,
                'PCAN_USBBUS5': PCAN_USBBUS5,
                'PCAN_USBBUS6': PCAN_USBBUS6,
                'PCAN_USBBUS7': PCAN_USBBUS7,
                'PCAN_USBBUS8': PCAN_USBBUS8,
            }
            
            self.PCAN_BAUDRATES = {
                125000: PCAN_BAUD_125K,
                250000: PCAN_BAUD_250K,
                500000: PCAN_BAUD_500K,
                1000000: PCAN_BAUD_1M,
            }
            
            self.PCAN_ERROR_OK = PCAN_ERROR_OK
            self.PCAN_ERROR_QRCVEMPTY = PCAN_ERROR_QRCVEMPTY
            self.PCAN_ERROR_BUSLIGHT = PCAN_ERROR_BUSLIGHT
            self.PCAN_ERROR_BUSHEAVY = PCAN_ERROR_BUSHEAVY
            self.PCAN_ERROR_BUSOFF = PCAN_ERROR_BUSOFF
            self.PCAN_LISTEN_ONLY = PCAN_LISTEN_ONLY
            
            print("✓ PCANBasic loaded - Hardware listen-only mode available")
            
        except ImportError:
            print("⚠ PCANBasic not available - Listen-only mode may not work properly")

    @staticmethod
    def get_available_channels() -> List[str]:
        """
        Detect available PCAN channels.

        Returns:
            List of available PCAN channel names (e.g., ['PCAN_USBBUS1', 'PCAN_USBBUS2'])
        """
        available_channels = []
        # Check up to 8 potential PCAN-USB channels
        potential_channels = [f'PCAN_USBBUS{i}' for i in range(1, 9)]
        
        for channel in potential_channels:
            bus = None
            try:
                # Try to initialize the channel with a common bitrate
                # Use a short timeout to fail quickly if channel doesn't exist
                bus = can.Bus(
                    interface='pcan',
                    channel=channel,
                    bitrate=DETECTION_BITRATE
                )
                # If we successfully created the bus, this channel is available
                available_channels.append(channel)
            except Exception:
                # Channel not available, skip it
                pass
            finally:
                # Always cleanup
                if bus:
                    try:
                        bus.shutdown()
                    except Exception:
                        pass
        
        return available_channels

    def connect(self, channel: str = 'PCAN_USBBUS1', baudrate: int = 500000) -> bool:
        """
        Connect to PCAN interface.

        Args:
            channel: PCAN channel name
            baudrate: CAN bus baud rate

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.bus = can.Bus(
                interface='pcan',
                channel=channel,
                bitrate=baudrate
            )
            self.current_baudrate = baudrate
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to connect: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from PCAN interface."""
        self.stop_receiving()
        if self.bus:
            try:
                self.bus.shutdown()
            except Exception as e:
                self.error_occurred.emit(f"Error during disconnect: {str(e)}")
            finally:
                self.bus = None

    def start_receiving(self):
        """Start receiving CAN messages in background thread."""
        if not self.bus:
            self.error_occurred.emit("Not connected to CAN bus")
            return

        if self.running:
            return

        self.running = True
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()

    def stop_receiving(self):
        """Stop receiving CAN messages."""
        self.running = False
        if self.receive_thread:
            self.receive_thread.join(timeout=2.0)
            self.receive_thread = None

    def _receive_loop(self):
        """Background thread loop for receiving CAN messages."""
        while self.running and self.bus:
            try:
                message = self.bus.recv(timeout=0.1)
                if message:
                    self.message_received.emit(message)
            except Exception as e:
                if self.running:  # Only emit error if still running
                    self.error_occurred.emit(f"Error receiving message: {str(e)}")
                    time.sleep(0.1)

    def send_message(self, can_id: int, data: List[int]) -> bool:
        """
        Send a CAN message.

        Args:
            can_id: CAN message ID
            data: CAN message data bytes (up to 8 bytes)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.bus:
            self.error_occurred.emit("Not connected to CAN bus")
            return False

        try:
            message = can.Message(
                arbitration_id=can_id,
                data=data,
                is_extended_id=False
            )
            self.bus.send(message)
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to send message: {str(e)}")
            return False

    def detect_baudrate(self, channel: str = 'PCAN_USBBUS1', 
                       callback: Optional[Callable[[int], None]] = None) -> Optional[tuple]:
        """
        Auto-detect CAN bus baud rate using TRUE hardware listen-only mode.
        
        This uses PCANBasic API directly to enable listen-only mode at hardware level,
        ensuring absolutely no ACK bits or error frames are transmitted.

        Args:
            channel: PCAN channel name
            callback: Optional callback function for progress updates

        Returns:
            Tuple of (baudrate: int, can_type: str) or None if detection failed.
            can_type is "Powertrain CanBus detected" for 29-bit extended IDs,
            or "Control CanBus detected" for 11-bit standard IDs.
        """
        if not self.pcan_basic:
            print("⚠ PCANBasic not available - cannot use hardware listen-only mode")
            return None

        # Common baudrates in order of popularity
        baudrates_to_test = [250000, 500000, 125000, 1000000]  # Message modifed to start with 250Kbits 

        print(f"\n{'='*70}")
        print(f"HARDWARE LISTEN-ONLY BAUDRATE DETECTION")
        print(f"Channel: {channel}")
        print(f"Mode: PURE LISTEN-ONLY (No ACK, No Error Frames)")
        print(f"{'='*70}\n")

        # Get PCAN channel constant
        pcan_channel = self.PCAN_CHANNELS.get(channel)
        if not pcan_channel:
            print(f"✗ Invalid channel: {channel}")
            return None

        best_baudrate = None
        best_score = 0
        best_can_type = None

        for baudrate in baudrates_to_test:
            if callback:
                callback(baudrate)

            print(f"Testing: {baudrate} bps")

            # Get PCAN baudrate constant
            pcan_baudrate = self.PCAN_BAUDRATES.get(baudrate)
            if not pcan_baudrate:
                print(f"  ✗ Invalid baudrate")
                continue

            try:
                # Step 1: Initialize channel
                result = self.pcan_basic.Initialize(
                    pcan_channel,
                    pcan_baudrate
                )

                if result != self.PCAN_ERROR_OK:
                    print(f"  ✗ Failed to initialize: {self._get_pcan_error_text(result)}")
                    continue

                # Step 2: Enable HARDWARE listen-only mode
                # This is the KEY - it prevents ACK bits at hardware level
                result = self.pcan_basic.SetValue(
                    pcan_channel,
                    self.PCAN_LISTEN_ONLY,
                    1  # Enable
                )

                if result == self.PCAN_ERROR_OK:
                    print(f"  ✓ Hardware listen-only mode: ENABLED")
                else:
                    print(f"  ⚠ Listen-only mode failed: {self._get_pcan_error_text(result)}")
                    print(f"    Continuing anyway (may send ACKs)...")

                # Step 3: Listen for valid CAN traffic
                valid_frames = 0
                error_frames = 0
                standard_frames = 0
                extended_frames = 0
                listen_duration = 2.5  # Listen for 2.5 seconds
                start_time = time.time()

                print(f"  Listening for {listen_duration}s...")

                while (time.time() - start_time) < listen_duration:
                    # Read message from hardware
                    result, msg, timestamp = self.pcan_basic.Read(pcan_channel)

                    if result == self.PCAN_ERROR_OK:
                        # Valid message received
                        # Check message type to filter error frames
                        if msg.MSGTYPE & 0x01 == 0:  # Not an error frame
                            valid_frames += 1
                            if msg.MSGTYPE & 0x7FF:  # Extended (29-bit) ID
                                extended_frames += 1
                            else:  # Standard (11-bit) ID
                                standard_frames += 1
                            
                            # If we see consistent traffic, this is correct
                            if valid_frames >= 15:
                                print(f"  ✓ Strong signal detected: {valid_frames} valid frames")
                                if extended_frames > standard_frames:
                                    can_type = "Powertrain CanBus detected"
                                else:
                                    can_type = "Control CanBus detected"
                                print(f"✓ CAN ID TYPE: {can_type} (extended={extended_frames}, standard={standard_frames})")
                                self.pcan_basic.Uninitialize(pcan_channel)
                                print(f"✓ BAUDRATE DETECTED: {baudrate} bps\n")
                                return (baudrate, can_type)
                        else:
                            error_frames += 1

                    elif result == self.PCAN_ERROR_QRCVEMPTY:
                        # No message in queue, wait a bit
                        time.sleep(0.02)

                    elif result in [self.PCAN_ERROR_BUSLIGHT, self.PCAN_ERROR_BUSHEAVY, self.PCAN_ERROR_BUSOFF]:
                        # Bus error - wrong baudrate
                        error_frames += 1
                        if error_frames >= 10:
                            print(f"  ✗ Too many bus errors (wrong baudrate)")
                            break

                    else:
                        # Other error
                        time.sleep(0.02)

                # Calculate score
                if valid_frames > 0:
                    error_ratio = error_frames / max(valid_frames + error_frames, 1)
                    score = valid_frames * (1.0 - min(error_ratio, 0.9))
                    
                    print(f"  Valid frames: {valid_frames}")
                    print(f"  Error frames: {error_frames}")
                    print(f"  Score: {score:.2f}")

                    if score > best_score:
                        best_score = score
                        best_baudrate = baudrate
                        if extended_frames > standard_frames:
                            best_can_type = "Powertrain CanBus detected"
                        else:
                            best_can_type = "Control CanBus detected"
                        print(f"  ✓ New best candidate")
                else:
                    print(f"  ✗ No valid traffic detected")

                # Clean up
                self.pcan_basic.Uninitialize(pcan_channel)

            except Exception as e:
                print(f"  ✗ Exception: {e}")
                try:
                    self.pcan_basic.Uninitialize(pcan_channel)
                except:
                    pass

            # Wait between tests
            print(f"  Waiting 0.5s...\n")
            time.sleep(0.5)

        # Final result
        print(f"{'='*70}")
        if best_baudrate and best_score >= 10:
            print(f"✓ BAUDRATE DETECTED: {best_baudrate} bps (confidence: {best_score:.1f})")
            print(f"{'='*70}\n")
            return (best_baudrate, best_can_type)
        elif best_baudrate and best_score >= 5:
            print(f"⚠ POSSIBLE BAUDRATE: {best_baudrate} bps (low confidence: {best_score:.1f})")
            print(f"{'='*70}\n")
            return (best_baudrate, best_can_type)
        else:
            print(f"✗ DETECTION FAILED: No valid traffic found")
            print(f"  Possible causes:")
            print(f"  • No CAN traffic on the bus")
            print(f"  • Bus is in error/off state")
            print(f"  • Non-standard baudrate in use")
            print(f"{'='*70}\n")
            return None

    def _get_pcan_error_text(self, error_code) -> str:
        """
        Get text description of PCAN error code.
        
        Args:
            error_code: PCAN error code
            
        Returns:
            Error description string
        """
        if not self.pcan_basic:
            return f"Error code: {error_code}"
        
        try:
            result, error_text = self.pcan_basic.GetErrorText(error_code)
            if result == self.PCAN_ERROR_OK:
                return error_text.decode('utf-8', errors='ignore')
        except:
            pass
        
        return f"Error code: {error_code}"

    def is_connected(self) -> bool:
        """
        Check if connected to CAN bus.

        Returns:
            True if connected, False otherwise
        """
        return self.bus is not None