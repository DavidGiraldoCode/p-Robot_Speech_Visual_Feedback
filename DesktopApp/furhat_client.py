import argparse
import asyncio
from furhat_realtime_api import AsyncFurhatClient, Events


class FurhatClient:
    def __init__(self, host: str, auth_key: str):
        self.host           = host
        self.auth_key       = auth_key
        self._is_connected  = False
        self._is_fectching  = False
        
        # Async taskst to schedule in the async event loop
        self._listner_task  = None

        # Creating the Furhat client request
        self.furhat         = None
        self.__build_web_socket_request()
        

    @property
    def is_connected(self):
        return self._is_connected
    
    @property
    def is_fetching(self):
        return self._is_fectching
    
    def __build_web_socket_request(self):
        """Builds the header arguments of the WebSocket request"""
        parser = argparse.ArgumentParser()
        parser.add_argument("--host", type=str, default=self.host, help="Furhat robot IP address")
        parser.add_argument("--auth_key", type=str, default=self.auth_key, help="Authentication key for Realtime API")
        args = parser.parse_args()
        self.furhat = AsyncFurhatClient(args.host, auth_key=args.auth_key)
        #self.furhat.set_logging_level(logging.DEBUG) 

    async def connect(self):
        try:
            await self.furhat.connect()
            self._is_connected = True
        except Exception as e:
            self._is_connected = False
            print(e)
            raise  # Re-raise so caller can handle

    async def disconnect(self):
        # TODO: Disconnect Tasks

        if self._is_connected:
            await self.furhat.disconnect()
            self._is_connected = False
            self._is_fectching = False
    
    async def __listener(self, ):
        if not self._is_connected: 
            raise RuntimeError("Furhat not connected")
        
        if self._is_fectching:
            return "Already fectching"
        else:
            try:
                await self.furhat.request_audio_start(16000, False, True)
                self._is_fectching = True
            except Exception as e:
                print(e)

    def start_audio_stream(self, loop: asyncio.AbstractEventLoop):
       """Start the listening process (non-blocking)."""
       if not self.furhat:
            raise RuntimeError("Furhat not connected")
       if self._listner_task and not self._listner_task.done():
            #it already running
            return
       self._listner_task = loop.create_task(self.__listener())

    async def stop_audio_stream(self):
        """Stop the listening process (non-blocking)."""
        if self._listner_task:
            self._listner_task.cancel()
            self._listner_task = None
            self._is_fectching = False

    def add_audio_stream_listeners(self, handler: any):
        """Register a handler for audio stream events."""
        self.furhat.add_handler(Events.response_audio_data, handler)

