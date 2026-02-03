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
WINDOW_TITLE = "Modular PySide6 For Research Projects"

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
        self.title_label = QLabel("Real-time Audio controller")
        self.description_label = QLabel("Send real-time audio input stream through the serial port")

        self.text_input_label = QLabel("Input the URL and press ENTER")
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("ws://127.0.0.1:8765")

        self.button_connect = QPushButton("Connect (WebSocket)")
        self.button_fetch = QPushButton("Fetch real-time audio")
        self.combo_box = QComboBox()
        self.combo_result_label = QLabel("Select Arduino Port")
        self.combo_box.addItems([])  # Controller will populate

        self.async_status_label = QLabel("Waiting for async call...")

        # Arrange
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.description_label)
        self.layout.addWidget(self.text_input_label)
        self.layout.addWidget(self.text_input)
        self.layout.addWidget(self.button_connect)
        self.layout.addWidget(self.button_fetch)
        self.layout.addWidget(self.combo_result_label)
        self.layout.addWidget(self.combo_box)
        self.layout.addWidget(self.async_status_label)
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
        # insert near top after title and description -> index 2
        self.layout.insertWidget(2, self._plot_widget)

    # convenience setters for labels
    def set_combo_result_text(self, text):
        self.combo_result_label.setText(text)

    def set_async_status(self, text):
        self.async_status_label.setText(text)
