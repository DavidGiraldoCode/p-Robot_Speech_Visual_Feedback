# view.py
"""
View: owns Qt widgets and layout.
Exposes small convenience methods so Controller doesn't manipulate internals directly.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt, QSize

from plot_view import AudioIntensityCanvas

WINDOW_WIDTH = 400
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Robot Speech Visual Feedback"

# WebSocket connection UI constants
DEFAULT_WS_URL = "ws://127.0.0.1:8765"
BUTTON_CONNECT_LABEL = "Connect (WebSocket)"
BUTTON_DISCONNECT_LABEL = "Disconnect (WebSocket)"
BUTTON_START_LISTENING = "Start listening"
BUTTON_STOP_LISTENING = "Stop listening"

# System message copy
MSG_DEFAULT = "⏳ Waiting for you to connect to the virtual Furhat or the physical robot."
MSG_CONNECTED = "✨ Success! You are now connected to Furhat. Start listening to the speech."
MSG_FAILED = "😵 Failed to connect to the provided IP. Please try again."

# Listening status copy
STATUS_LISTENING = "Listening..."
STATUS_STOPPED = "Stopped listening."
STATUS_TALKING = "🗣️ Robot is talking"
STATUS_QUIET = "🤫 Robot is quiet"

class View(QMainWindow):
    def __init__(self, model):
        super().__init__()
        self.model = model

        self.setWindowTitle(WINDOW_TITLE)
        self.setFixedSize(QSize(WINDOW_WIDTH, WINDOW_HEIGHT))

        central = QWidget()
        self.setCentralWidget(central)

        self.layout = QVBoxLayout(central)
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # Widgets
        self.description_label = QLabel("Furhat - Arduino controller")
        font = self.description_label.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 8)
        self.description_label.setFont(font)


        self.text_input_label = QLabel("Input the URL and press ENTER")
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("ws://127.0.0.1:8765")

        self.button_connect = QPushButton(BUTTON_CONNECT_LABEL)
        self.button_fetch = QPushButton(BUTTON_START_LISTENING)
        self.button_fetch.setEnabled(False)  # Disabled until connected
        self.combo_box = QComboBox()
        self.combo_result_label = QLabel("Select Arduino Port")
        self.combo_box.addItems([])  # Controller will populate

        self.async_status_label = QLabel("You are disconnected from the robot")

        # Arrange
        self.layout.addWidget(self.description_label)
        self.layout.addWidget(self.text_input_label)
        self.layout.addWidget(self.text_input)
        self.layout.addWidget(self.async_status_label)
        self.layout.addWidget(self.button_connect)
        self.layout.addWidget(self.button_fetch)
        self.layout.addWidget(self.combo_result_label)
        self.layout.addWidget(self.combo_box)

        # System Messages section
        self.system_msg_header = QLabel("System Messages")
        font = self.system_msg_header.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 4)
        self.system_msg_header.setFont(font)

        self.system_msg_label = QLabel(MSG_DEFAULT)
        self.system_msg_label.setWordWrap(True)

        self.layout.addWidget(self.system_msg_header)
        self.layout.addWidget(self.system_msg_label)
        self.layout.addStretch()

        # Plot area placeholder (view owns insertion)
        self._plot_widget = None

    # small API so Controller doesn't touch layout indices
    def set_plot_widget(self, widget):
        """Place or replace the plot widget at a known position near the top."""
        if self._plot_widget:
            self.layout.removeWidget(self._plot_widget)
            self._plot_widget.setParent(None)
            self._plot_widget = None

        self._plot_widget = widget
        # for inserting at the end use self.layout.count()
        self.layout.insertWidget(1, self._plot_widget)

    # convenience setters for labels
    def set_combo_result_text(self, text):
        self.combo_result_label.setText(text)

    def set_async_status(self, text):
        self.async_status_label.setText(text)

    # WebSocket connection state methods
    def set_ws_connected_state(self):
        """Update UI to reflect connected state."""
        self.button_connect.setText(BUTTON_DISCONNECT_LABEL)
        self.text_input.setEnabled(False)
        self.button_fetch.setEnabled(True)

    def set_ws_disconnected_state(self):
        """Update UI to reflect disconnected state."""
        self.button_connect.setText(BUTTON_CONNECT_LABEL)
        self.text_input.setEnabled(True)
        self.button_fetch.setEnabled(False)
        self.button_fetch.setText(BUTTON_START_LISTENING)

    def set_listening_state(self, is_listening: bool):
        """Update fetch button label based on listening state."""
        if is_listening:
            self.button_fetch.setText(BUTTON_STOP_LISTENING)
        else:
            self.button_fetch.setText(BUTTON_START_LISTENING)

    def reset_url_input_to_default(self):
        """Reset the URL input field to default value."""
        self.text_input.setText("")
        self.text_input.setPlaceholderText(DEFAULT_WS_URL)

    def get_url_or_default(self) -> str:
        """Get user-entered URL or return default."""
        url = self.text_input.text().strip()
        return url if url else DEFAULT_WS_URL

    def set_system_message(self, text: str):
        """Update the system message label."""
        self.system_msg_label.setText(text)
