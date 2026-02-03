# app_controller.py
"""
Controller: thin orchestration layer between Model and View.
 - Keeps event wiring compact.
 - Uses Model's synchronous scheduling functions to interact with async tasks.
 - Handles UI events and maps them to Model calls.
Design rationale:
 - Keep Controller free of low-level networking/serial code.
 - Controller should not create asyncio tasks directly except when scheduling model operations that return immediately.
"""
from PySide6.QtCore import QTimer
from view import View
from model import AppModel
from plot_view import AudioIntensityCanvas
import numpy as np

PLOT_UPDATE_INTERVAL_MS = 50  # UI polling interval

class AppController:
    def __init__(self):
        self.model = AppModel()
        self.view = View(self.model)

        # Create and set the plot widget in the view (view owns layout)
        self.plot_widget = AudioIntensityCanvas()
        self.view.set_plot_widget(self.plot_widget)

        # Populate combobox with serial ports
        ports = self.model.get_available_ports()
        self.view.combo_box.addItems([""] + ports)

        # Connect signals from view to controller handlers
        self._connect_signals()

        # QTimer to poll the model for the latest WS package and update the plot
        self._poll_timer = QTimer()
        self._poll_timer.setInterval(PLOT_UPDATE_INTERVAL_MS)
        self._poll_timer.timeout.connect(self._on_poll_timer_tick)
        # Start timer if you want autorefresh; start only when user wants visualization.
        # self._poll_timer.start()

    def _connect_signals(self):
        # Text input - pressing Enter commits URL text
        self.view.text_input.returnPressed.connect(self._on_text_commit)
        self.view.button_connect.clicked.connect(self._on_ws_connect_clicked)
        self.view.button_fetch.clicked.connect(self._on_ws_fetch_clicked)
        self.view.combo_box.currentIndexChanged.connect(self._on_combo_changed)

        # Model signals
        self.model.input_text_commited.connect(self._on_committed_signal)
        self.model.input_text_cleared.connect(self._on_cleared_signal)
        self.model.async_task_completed.connect(self._on_async_task_completed)

    # -----------------------
    # UI Event Handlers
    # -----------------------
    def _on_text_commit(self):
        url_text = self.view.text_input.text().strip()
        # Optionally store into model (live vs committed); here we keep committed
        self.model.set_committed_input_text(url_text)
        self.view.set_async_status(f"Committed URL: {url_text}")

    def _on_ws_connect_clicked(self):
        # Schedule connect/disconnect
        result = self.model.schedule_ws_connect_toggle()
        self.view.set_async_status(str(result))

    def _on_ws_fetch_clicked(self):
        # Start/stop fetching; ensure connected first
        ok = self.model.schedule_ws_data_toggle()
        if ok:
            self.view.set_async_status("WS fetch toggled.")
            # ensure the UI poll timer is active to refresh plot
            if not self._poll_timer.isActive():
                self._poll_timer.start()
        else:
            self.view.set_async_status("Start WS connect before fetching.")

    def _on_combo_changed(self, idx):
        selected = self.view.combo_box.currentText()
        self.view.set_combo_result_text(f"Select Arduino Port: {selected}")
        if selected == "":
            self.model.disconnect_serial()
        else:
            self.model.connect_serial(selected)

    # -----------------------
    # Model signal handlers
    # -----------------------
    def _on_committed_signal(self):
        self.view.set_async_status("Model emitted: input committed")

    def _on_cleared_signal(self):
        self.view.set_async_status("Model emitted: input cleared")

    def _on_async_task_completed(self, message):
        self.view.set_async_status(f"Async: {message}")

    # -----------------------
    # Polling / Rendering
    # -----------------------
    def _on_poll_timer_tick(self):
        frame = self.model.get_latest_ws_package_thread_safe()
        # frame is a tuple (left, right)
        if not frame:
            return
        left, right = frame
        # Convert to an absolute amplitude and normalize (example rule)
        value = (abs(left) + abs(right)) / 2.0
        normalized = min(value / 30000.0, 1.0)
        # update plot
        self.plot_widget.plot_frame_intensity_normal(normalized)
        # optionally send to serial as 0..255
        rgb = int(normalized * 255)
        self.model.send_serial_data(rgb)

    # -----------------------
    # Public
    # -----------------------
    def show(self):
        self.view.show()
