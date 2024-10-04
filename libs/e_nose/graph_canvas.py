from PyQt5.QtCore import QTimer

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class GraphCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)

        # Initial plot
        self.x = np.linspace(0, 10, 100)
        self.y = np.sin(self.x)
        self.line, = self.ax.plot(self.x, self.y)

        # Timer to update the graph
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(100)

    def update_plot(self):
        self.y = np.sin(self.x + np.random.uniform(0, 0.5))  # Update y data
        self.line.set_ydata(self.y)
        self.ax.draw_artist(self.line)
        self.fig.canvas.draw()