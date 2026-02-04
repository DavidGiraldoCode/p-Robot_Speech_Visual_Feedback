import argparse
import asyncio
from furhat_realtime_api import AsyncFurhatClient, Events
import struct
import logging
import base64


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
        self.furhat.set_logging_level(logging.DEBUG) 

    async def connect(self):
        try:
            await self.furhat.connect()
            self._is_connected = True
        except Exception as e:
            print(e)

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
        self.furhat.add_handler(Events.response_audio_data, handler)
        print(" in Listener")

    async def furhat_microphone_data(data):
        """ Handler for the raw audio stream data.
        'data' is the event dictionary (e.g., {'speaker': 'base64_string', 'type': '...'}). """
        # 2. Safely get the base64 string from the 'speaker' key
        base64_audio_data = data.get('speaker')
        
        # NEW: Print the raw base64 data fragment
        print(f"Getting raw (first 30 chars): {base64_audio_data[:30]}...")
            
        if base64_audio_data:
            try:
                # 3. Decode the base64 string back into raw binary audio bytes
                raw_audio_bytes = base64.b64decode(base64_audio_data)
                
                # Now, raw_audio_bytes is the 16-bit PCM audio you can process
                print(f"Received audio chunk: {len(raw_audio_bytes)} raw bytes.")
                
                # --- NEW LOGIC: Calculate RMS for Left Channel ---
                l_channel_samples = []
                
                # The audio format is 16-bit signed little-endian stereo (L, R)
                # Each stereo frame is 4 bytes (2 bytes for L, 2 bytes for R).
                frame_size = 4
                
                # Iterate over the raw bytes, stepping by the frame size
                for i in range(0, len(raw_audio_bytes) - frame_size + 1, frame_size):
                    # Unpack the first 2 bytes (Left channel sample) as a signed short ('h')
                    # '<' ensures little-endian
                    l_sample = struct.unpack('<h', raw_audio_bytes[i:i+2])[0]
                    l_channel_samples.append(l_sample)
                    
                # Calculate RMS (Root Mean Square) for the left channel samples
                if l_channel_samples:
                    # RMS = sqrt(mean(samples^2)) - This measures the signal energy (loudness)
                    sum_of_squares = sum(s**2 for s in l_channel_samples)
                    rms = (sum_of_squares / len(l_channel_samples))**0.5
                    # The RMS value is printed as a measure of "frequency/activity"
                    print(f"L-Channel Activity (RMS Amplitude): {rms:.2f}")
                else:
                    print("Not enough samples to process L-Channel data.")
                # --- END NEW LOGIC ---
                
            except Exception as e:
                print(f"Failed to decode or process audio data: {e}")
        else:
            print("Received audio event without 'speaker' (Base64 data).")



    
