# serial_com.py
"""
Serial communication helper.
Responsibility:
 - List available ports
 - Connect/disconnect
 - Provide a simple send(data) method
Design rationale:
 - Keeps serial concerns in one place and shields Model / Controller from pyserial details.
"""
import serial
import serial.tools.list_ports

class SerialCom:
    def __init__(self, baudrate=9600):
        self._baudrate = baudrate
        self._conn = None

    def list_ports(self):
        try:
            ports = serial.tools.list_ports.comports()
            return [p.device for p in ports]
        except Exception as e:
            print("SerialCom: error listing ports:", e)
            return []

    def connect(self, port_name: str):
        # close existing connection
        self.disconnect()
        try:
            self._conn = serial.Serial(port=port_name, baudrate=self._baudrate, timeout=1)
            print(f"SerialCom: connected to {port_name}")
            return True
        except Exception as e:
            print("SerialCom: connect failed:", e)
            self._conn = None
            return False

    def disconnect(self):
        if self._conn:
            try:
                if self._conn.is_open:
                    self._conn.close()
                self._conn = None
            except Exception:
                self._conn = None

    def is_connected(self):
        return self._conn is not None and getattr(self._conn, "is_open", False)

    def send(self, payload):
        if not self.is_connected():
            print("SerialCom: cannot send, not connected")
            return False
        try:
            data = f"{payload}\n".encode("utf-8")
            self._conn.write(data)
            return True
        except Exception as e:
            print("SerialCom: send error", e)
            self.disconnect()
            return False
