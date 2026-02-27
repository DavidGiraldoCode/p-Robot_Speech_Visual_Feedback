# p-Robot_Speech_Visual_Feedback

** 📋 TODO: ** Add a password field to allow connection to robots in another network.

## 🪲 Known bugs
- If you disconnect the Arduino and then connect it back on another port, the Desktop App does not update ports. You will have to restart the app to see the new port in the dropdown list.
- There is no guarantee that the robot and this Python app are on the same network during use. Therefore, in the Furhat configuration for real-time, add the key "abc" to allow the Python connection from a different network.

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

## 📦 Project Structure

| File | Description |
|------|-------------|
| `main.py` | Application entry point - initializes Qt event loop with qasync |
| `app_controller.py` | Controller - wires View signals to Model, manages UI state |
| `model.py` | Model - coordinates FurhatClient and SerialCom, processes audio |
| `view.py` | View - Qt GUI widgets and layout |
| `furhat_client.py` | WebSocket client for Furhat robot audio streaming |
| `serial_com.py` | Serial communication with Arduino |
| `plot_view.py` | Matplotlib canvas for audio intensity visualization |

### Key Classes

| Class | File | Description |
|-------|------|-------------|
| `AppController` | app_controller.py | Orchestrates Model-View interaction, handles UI events |
| `AppModel` | model.py | Central state holder, schedules async tasks, processes audio |
| `View` | view.py | Main window with connection controls and status display |
| `FurhatClient` | furhat_client.py | Async WebSocket client for Furhat real-time audio API |
| `SerialCom` | serial_com.py | Manages serial port connection and data transmission |
| `AudioIntensityCanvas` | plot_view.py | Real-time audio intensity visualization widget |

## ⚙️ Setup

> For full cross-platform setup instructions (Windows, macOS, common pitfalls), see [INSTALLATION_DETAILS.md](./INSTALLATION_DETAILS.md).

### Quick start (macOS / Linux)

```bash
cd DesktopApp
python3 -m venv venv
source venv/bin/activate
pip install numpy scipy matplotlib pyserial PySide6 qasync websockets furhat-realtime-api
python3 main.py
```

## 📚 References
1. [Realtime API Python client for Furhat](https://docs.furhat.io/realtime-api/python_client) 