# model.py
"""
AppModel: central state holder & coordinator.
 - Owns high-level state and instances of FurhatClient and SerialCom.
 - Exposes synchronous methods the Controller can call safely (they schedule async tasks).
 - Provides a thread-safe method to get the latest audio package.
 - Emits Qt signals for UI events.
"""
import struct
import base64
from PySide6.QtCore import QObject, Signal
import asyncio

from serial_com import SerialCom
from furhat_client import FurhatClient

SERIAL_BAUDRATE = 9600

class AppModel(QObject):
    # Signals for view/controller
    input_text_commited = Signal()
    input_text_cleared = Signal()
    async_task_completed = Signal(str)

    # WebSocket connection state signals
    ws_connection_succeeded = Signal()
    ws_connection_failed = Signal(str)  # error message
    ws_disconnected = Signal()

    # Robot speech state signals
    robot_started_talking = Signal()
    robot_stopped_talking = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Input text state
        self._live_input_text = ""
        self._committed_input_text = "N/A"

        # Serial client
        self.serial = SerialCom(baudrate=SERIAL_BAUDRATE)

        # Furhat API - created dynamically on connect with user-specified host
        self.furhat_client = None

        # Latest audio frame (controller polls this synchronously)
        self._latest_ws_package = (0, 0)
        self._silence_message_printed = False  # Debounce flag for silence detection

        # Keep references to scheduled tasks (so controller or model can cancel)
        self._worker_tasks = []

    # Input state methods
    def set_live_input_text(self, text):
        self._live_input_text = text
        if text == "":
            self.input_text_cleared.emit()

    def get_live_input_text(self):
        return self._live_input_text

    def set_committed_input_text(self, text):
        self._committed_input_text = text
        self.input_text_commited.emit()

    def get_committed_input_text(self):
        return self._committed_input_text

    def _get_connection_host(self) -> str:
        """Extract host from committed URL, or return default."""
        url = self._committed_input_text.strip()
        if url and url != "N/A":
            # Handle "ws://host:port" or plain "host" formats
            if url.startswith("ws://"):
                url = url[5:]  # Remove "ws://"
            host = url.split(":")[0]  # Remove port if present
            return host if host else "127.0.0.1"
        return "127.0.0.1"

    # ------------------------------
    # WebSocket scheduling surface (synchronous helpers)
    # Controller calls these methods without using await
    # ------------------------------
    def schedule_ws_connect_toggle(self):
        """Toggle connect/disconnect. Non-blocking."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            self.ws_connection_failed.emit("asyncio loop not running")
            return "Error: asyncio loop not running (use qasync.run)."

        if self.furhat_client and self.furhat_client.is_connected:
            loop.create_task(self._disconnect_furhat())
            return "Furhat disconnect scheduled"
        else:
            loop.create_task(self._connect_furhat())
            return "Furhat connect scheduled"

    async def _connect_furhat(self):
        """Connect to Furhat and emit appropriate signal."""
        host = self._get_connection_host()

        # Create new FurhatClient with user-specified host
        # TODO: Add a input field to add manually the auth key when connecting 
        self.furhat_client = FurhatClient(host, "abc")
        self.furhat_client.add_audio_stream_listeners(self.audio_stream_handler)

        try:
            await self.furhat_client.connect()
            if self.furhat_client.is_connected:
                self.ws_connection_succeeded.emit()
            else:
                self.ws_connection_failed.emit("Connection failed")
        except Exception as e:
            self.ws_connection_failed.emit(str(e))

    async def _disconnect_furhat(self):
        """Disconnect from Furhat and emit signal."""
        if self.furhat_client:
            await self.furhat_client.disconnect()
        self.ws_disconnected.emit()

    def schedule_ws_data_toggle(self):
        """Start/stop the ws fetching loop. Non-blocking. Requires ws connected."""
        if not self.furhat_client or not self.furhat_client.is_connected:
            print("Model: cannot start fetch; WS not connected.")
            return False
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return False
        
        if self.furhat_client.is_fetching:
            loop.create_task(self.furhat_client.stop_audio_stream())
            return True
        else:
            self.furhat_client.start_audio_stream(loop)
            return True

    def get_latest_ws_package_thread_safe(self):
        """Synchronous read of the latest package (very cheap, single tuple read)."""
        return self._latest_ws_package

    async def audio_stream_handler(self, data):
        """Process incoming audio data from Furhat WebSocket."""
        base64_audio_data = data.get('speaker')
        if not base64_audio_data:
            return

        # Silence detection: "AAAA..." is base64 for null bytes
        SILENCE_CHECK_LENGTH = 20
        is_silent = (len(base64_audio_data) >= SILENCE_CHECK_LENGTH and
                     base64_audio_data[:SILENCE_CHECK_LENGTH] == 'A' * SILENCE_CHECK_LENGTH)

        if is_silent:
            if not self._silence_message_printed:
                print("The robot is not talking")
                self._silence_message_printed = True
                self.robot_stopped_talking.emit()
            self._latest_ws_package = (0.0, 0)
            return

        # Reset debounce flag when speech resumes and log state change
        if self._silence_message_printed:
            print("Is Talking")
            self.robot_started_talking.emit()
        self._silence_message_printed = False

        try:
            raw_audio_bytes = base64.b64decode(base64_audio_data)

            # Extract left channel from stereo PCM (16-bit signed, little-endian)
            l_channel_samples = []
            for i in range(0, len(raw_audio_bytes) - 3, 4):
                l_sample = struct.unpack('<h', raw_audio_bytes[i:i+2])[0]
                l_channel_samples.append(l_sample)

            if not l_channel_samples:
                return

            # Calculate RMS amplitude
            sum_of_squares = sum(s**2 for s in l_channel_samples)
            rms = (sum_of_squares / len(l_channel_samples)) ** 0.5

            # Normalize to 0-255 for Arduino
            MAX_RMS = 10000.0
            normalized = min(rms / MAX_RMS, 1.0)
            intensity_byte = int(normalized * 255)

            self._latest_ws_package = (rms, intensity_byte)

        except Exception as e:
            print(f"Audio processing error: {e}")
     

    # ------------------------------
    # Serial surface
    # ------------------------------
    def get_available_ports(self):
        return self.serial.list_ports()

    def connect_serial(self, port_name):
        return self.serial.connect(port_name)

    def disconnect_serial(self):
        self.serial.disconnect()

    def send_serial_data(self, data):
        return self.serial.send(data)

    # ------------------------------
    # Cleanup helpers (called on app exit)
    # ------------------------------
    async def shutdown(self):
        """Stop all running tasks and close connections."""
        # Cancel any worker tasks
        for t in self._worker_tasks:
            t.cancel()
        self._worker_tasks.clear()

        # Disconnect from Furhat if connected
        try:
            if self.furhat_client:
                await self.furhat_client.disconnect()
        except Exception as e:
            print("Model.shutdown error:", e)

        # Close serial
        self.serial.disconnect()
        self.async_task_completed.emit("shutdown_complete")
