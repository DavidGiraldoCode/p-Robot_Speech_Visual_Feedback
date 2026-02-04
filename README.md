# p-Robot_Speech_Visual_Feedback

## 🏗️ Architecture

```bash
[Furhat Robot] ──WebSocket──► [Python GUI] ──Serial COM──► [Arduino LED]
                  Audio PCM                   [0,255] values
```

Flow:
1. Python GUI connects to Furhat via WebSocket (input Robot IP)
2. Furhat streams audio continuously
3. Python processes audio → calculates intensity
4. Python sends normalized values [0,255] via Serial
5. Arduino controls LED brightness based on received values

```bash
Furhat Robot                Python Desktop App              Arduino + LED
(WS Server)                 (WS Client + Serial)           (Serial Device)
     │                              │                             │
     │      (1) User Input Robot IP │                             │
     │◄──(2) WS Connect Request─────│                             │
     │                              │                             │
     │──(3) Audio Stream ──────────►│                             │
     │    (continuous PCM/WAV)      │──(4) Open Serial Port ─────►│
     │                              │                             │
     │──(4) Audio Chunks ──────────►│──(5) Intensity [0,255] ────►│─► 💡 LED
     │                              │    (post-processed)         │
     │◄──(5) Close WS ──────────────│                             │
     │                              │                             │
```

## ⚙️ Settup

Change directory to the Python app
```bash
cd /DesktopApp
```

Create virtual environment
```bash
python3 -m venv venv
```

Activate virtual environment before installing libraries
```bash
source venv/bin/activate
```

Install
```bash
pip install numpy
pip install scipy
pip install matplotlib
pip install pyserial
pip install PySide6
pip install qasync
pip install websockets
pip install furhat-realtime-api
```

Deactivate
```bash
deactivate
```

To run it
```bash
python3 main.py
```

## 📚 References
1. [Realtime API Python client for Furhat](https://docs.furhat.io/realtime-api/python_client) 