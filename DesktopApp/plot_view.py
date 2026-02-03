# plot_view.py
"""
PlotView (AudioIntensityCanvas):
 - Dedicated file for plotting so view.py stays small.
 - Keeps the exact plotting details isolated; Controller just calls plot_frame_intensity_normal(value).
"""
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import QWidget, QVBoxLayout

PLOT_BG_COLOR = "#323232"

class AudioIntensityCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(4,3), facecolor=PLOT_BG_COLOR)
        self.canvas = FigureCanvas(self.figure)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.canvas)
        self.layout.setContentsMargins(0,0,0,0)
        self.ax = self.figure.add_subplot(111)
        self.bar_norm = None
        self.init_plot_style_only_normal()

    def init_plot_style_only_normal(self):
        self.ax.clear()
        self.ax.set_facecolor(PLOT_BG_COLOR)
        self.ax.set_title("Real-Time normalized audio intensity", color='white')
        self.ax.set_xticks([0.5])
        self.ax.set_xticklabels(['Normalized'], color='white')
        self.ax.set_ylim(0, 1.1)
        self.ax.grid(axis='y', alpha=0.3, color='gray')
        self.bar_norm = self.ax.bar(0.5, 0, width=0.35)
        self.figure.tight_layout(pad=1.5)

    def plot_frame_intensity_normal(self, normalized_value: float):
        if not self.bar_norm:
            return
        clamped = max(0.0, min(1.0, float(normalized_value)))
        self.bar_norm[0].set_height(clamped)
        self.canvas.draw()
