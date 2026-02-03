# model.py
"""
AppModel: central, thin state holder & coordinator.
 - Owns high-level state and instances of WebSocketClient and SerialCom.
 - Exposes synchronous methods the Controller can call safely (they schedule async tasks).
 - Provides a thread-safe method to get the latest websocket package (a single atomic tuple).
 - Emits Qt signals for UI events.
Design choices explained inline.
"""
import os
import numpy as np
from PySide6.QtCore import QAbstractListModel, Qt, Signal, QTimer
import asyncio

from websocket_client import WebSocketClient
from serial_com import SerialCom

# TODO: Adding Furhat
from furhat_client import FurhatClient

try:
    from scipy.io import wavfile
except Exception:
    wavfile = None  # We gracefully handle missing scipy in load_audio_samples

WEB_SOCKET_SERVER_URL = "ws://127.0.0.1:8765"
SERIAL_BAUDRATE = 9600
DEFAULT_COMBO_OPTIONS = [f"Item {i}" for i in range(1, 11)]

class AppModel(QAbstractListModel):
    # Signals for view/controller
    input_text_commited = Signal()
    input_text_cleared = Signal()
    async_task_completed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # UI dropdown options (simple list model)
        self._dropdown_options = DEFAULT_COMBO_OPTIONS

        # Input text state
        self._live_input_text = ""
        self._committed_input_text = "N/A"

        # Serial and WS clients (separate classes)
        self.serial = SerialCom(baudrate=SERIAL_BAUDRATE)
        # internal asyncio queue for websocket -> model communication
        self._ws_queue = asyncio.Queue()
        self.ws_client = WebSocketClient(WEB_SOCKET_SERVER_URL, self._ws_queue)

        # TODO: Adding Furhat API
        self.furhat_client = FurhatClient("127.0.0.1","")
        self.furhat_client.add_audio_stream_listeners(self.audio_stream_handler)

        # The "latest frame" - atomic access via asyncio tasks (controller polls this synchronously)
        # We keep a simple Python attribute protected by minimal invariants (single-writer in model)
        self._latest_ws_package = (0, 0)

        # Timer used by the Controller/View for regular UI refresh (polling style)
        self.data_for_draw_calls_updated = QTimer()

        # Audio file debug
        self._sample_rate = 44100
        self._samples = np.array([0], dtype=np.int16)

        # Keep references to scheduled tasks (so controller or model can cancel)
        self._worker_tasks = []

    # List model support (for combo box if needed)
    def data(self, index, role=Qt.DisplayRole):
        if 0 <= index.row() < self.rowCount() and role == Qt.DisplayRole:
            return self._dropdown_options[index.row()]
        return None

    def rowCount(self, parent=None):
        return len(self._dropdown_options)

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

    # Audio loader (Model owns filesystem / library calls)
    def load_audio_samples(self, file_path):
        if wavfile is None:
            print("scipy not available; returning silent sample")
            return 44100, np.array([0], dtype=np.int16)
        try:
            absolute_file_path = os.path.join(os.path.dirname(__file__), file_path)
            fs, samples = wavfile.read(absolute_file_path)
            if samples.ndim > 1:
                samples = samples[:, 0]
            self._sample_rate = fs
            self._samples = samples
            return fs, samples
        except Exception as e:
            print("Model: load_audio_samples failed:", e)
            self._samples = np.array([0], dtype=np.int16)
            self._sample_rate = 44100
            return self._sample_rate, self._samples

    # ------------------------------
    # WebSocket scheduling surface (synchronous helpers)
    # Controller calls these methods without using await
    # ------------------------------
    def schedule_ws_connect_toggle(self):
        """Toggle connect/disconnect. Non-blocking."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return "Error: asyncio loop not running (use qasync.run)."

        """""
        if self.ws_client.is_connected:
            loop.create_task(self.ws_client.disconnect())
            return "WS disconnect scheduled"
        else:
            loop.create_task(self.ws_client.connect())
            return "WS connect scheduled"
        """""

        # TODO: Adding Furhat connection
        if self.furhat_client.is_connected:
            loop.create_task(self.furhat_client.disconnect())
            return "Furhat disconnect scheduled"
        else:
            loop.create_task(self.furhat_client.connect())
            return "Furhat connect scheduled"

    def schedule_ws_data_toggle(self):
        """Start/stop the ws fetching loop. Non-blocking. Requires ws connected."""
        #if not self.ws_client.is_connected:
        if not self.furhat_client.is_connected:
            print("Model: cannot start fetch; WS not connected.")
            return False
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return False
        
        if self.furhat_client.is_fetching:
            self.furhat_client.stop_audio_stream()
        else:
            self.furhat_client.start_audio_stream(loop)
            return True
        """"
        if self.ws_client.is_fetching:
            # stop fetching by cancelling tasks inside the client
            self.ws_client.stop_fetching()
            return True
        else:
            # start fetching tasks inside client; client will populate the _ws_queue
            self.ws_client.start_fetching(loop)
            # schedule a local coroutine that consumes the queue and updates latest package
            t = loop.create_task(self._drain_ws_queue_update_latest())
            self._worker_tasks.append(t)
            return True
        """

    async def _drain_ws_queue_update_latest(self):
        """Continuously take freshest frames from the queue and store a single latest package."""
        try:
            while True:
                first = await self._ws_queue.get()
                latest = first
                # empty the queue to get the freshest
                while True:
                    try:
                        latest = self._ws_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                # update the single shared package — controller will read it synchronously
                self._latest_ws_package = latest
                # yield briefly
                await asyncio.sleep(0)
        except asyncio.CancelledError:
            # cleanup if cancelled
            return

    def get_latest_ws_package_thread_safe(self):
        """Synchronous read of the latest package (very cheap, single tuple read)."""
        return self._latest_ws_package

    async def audio_stream_handler(self,data):
        base64_audio_data = data.get('speaker')
    
        # NEW: Print the raw base64 data fragment
        print(f"Getting raw (first 30 chars): {base64_audio_data[:30]}...")
     

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
    # TODO : add the disconnection from Furhat
    async def shutdown(self):
        """Attempt to stop all running tasks and close connections (async)."""
        # cancel any worker tasks
        for t in self._worker_tasks:
            t.cancel()
        self._worker_tasks.clear()

        """
        # stop ws fetching and disconnect
        try:
            if self.ws_client.is_fetching:
                self.ws_client.stop_fetching()
            if self.ws_client.is_connected:
                await self.ws_client.disconnect()
        except Exception as e:
            print("Model.shutdown error:", e)
        """

        #TODO Disconnect from listening to input stream
        try:
            self.furhat_client.disconnect()
        except Exception as e:
            print("Model.shutdown error:", e)
            
        # close serial
        self.serial.disconnect()
        # emit completion
        self.async_task_completed.emit("shutdown_complete")
