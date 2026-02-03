# websocket_client.py
"""
A compact WebSocket client component.
Responsibility:
 - Manage websocket connection lifecycle (connect/disconnect).
 - Provide start/stop of continuous retrieval (spawns internal listener/processor).
 - Push incoming frames into an asyncio.Queue provided by the Model.
Design rationale:
 - Keep all networking logic isolated so Model remains a coordinator and owner of app state.
 - Exposes 'schedule_connect' and 'schedule_data_retrieval' style helpers (but actual scheduling is done by Model).
"""
import asyncio
import struct
from websockets.asyncio.client import connect

class WebSocketClient:
    def __init__(self, url: str, out_queue: asyncio.Queue):
        self.url = url
        self._out_queue = out_queue
        self._ws = None
        self._listener_task = None
        self._processor_task = None
        self._is_connected = False
        self._is_fetching = False

    @property
    def is_connected(self):
        return self._is_connected

    @property
    def is_fetching(self):
        return self._is_fetching

    async def connect(self):
        if self._ws is not None and not self._ws.closed:
            return
        self._ws = await connect(self.url)
        self._is_connected = True
        # note: do not start fetching automatically; explicit control preferred.

    async def disconnect(self):
        # Cancel fetch tasks first
        if self._listener_task:
            self._listener_task.cancel()
        if self._processor_task:
            self._processor_task.cancel()

        if self._ws:
            await self._ws.close()
            self._ws = None
        self._is_connected = False
        self._is_fetching = False

    async def _listener(self):
        """Read raw frames and put into an internal queue (fast, IO-limited)."""
        self._is_fetching = True
        try:
            if not self._ws:
                return
            while True:
                frame = await self._ws.recv()
                # common format used in your project: two 16-bit little-endian ints
                if len(frame) == 4:
                    left, right = struct.unpack('<hh', frame)
                    await self._out_queue.put((left, right))
                else:
                    # put a marker or ignore
                    await self._out_queue.put((0, 0))
        except asyncio.CancelledError:
            raise
        except Exception as e:
            # swallow/log, let caller decide what's next
            print("WebSocket listener error:", e)
        finally:
            self._is_fetching = False

    async def _processor(self):
        """Optional consumer-style task if you wanted to process before handing to model.
           For this design we keep processing minimal — the Model reads latest frame itself."""
        # simple placeholder that just yields control while the listener populates the queue
        try:
            while True:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            raise

    def start_fetching(self, loop: asyncio.AbstractEventLoop):
        """Start listener and processor tasks (non-blocking)."""
        if not self._ws:
            raise RuntimeError("WebSocket not connected")
        if self._listener_task and not self._listener_task.done():
            # already running
            return
        self._listener_task = loop.create_task(self._listener())
        self._processor_task = loop.create_task(self._processor())

    def stop_fetching(self):
        """Stop the internal tasks (non-blocking)."""
        if self._listener_task:
            self._listener_task.cancel()
            self._listener_task = None
        if self._processor_task:
            self._processor_task.cancel()
            self._processor_task = None
        self._is_fetching = False
