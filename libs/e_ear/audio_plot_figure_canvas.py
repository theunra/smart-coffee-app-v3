import numpy as np
import sounddevice as sd

from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class AudioPlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100, sample_rate=44100, buffer_duration=2):
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)

        self.sample_rate = sample_rate
        self.chunk_size = 1024  # Number of samples per chunk (frame)
        self.buffer_duration = buffer_duration  # Buffer duration in seconds
        self.total_samples = int(self.sample_rate * self.buffer_duration)  # Total samples to collect for 2 seconds

        # Time axis for the buffer
        self.time_axis = np.linspace(0, self.buffer_duration, self.total_samples)

        # Initialize buffer to store audio data for 2 seconds
        self.audio_buffer = np.zeros(self.total_samples)

        # Plot initial empty buffer
        self.line, = self.ax.plot(self.time_axis, self.audio_buffer, color='b')
        self.ax.set_title("Real-Time Audio Signal")
        self.ax.set_xlabel("Time [s]")
        self.ax.set_ylabel("Amplitude")

        self.y_min_lim = -0.1
        self.y_max_lim = 0.1

        # Sound device stream
        self.stream = sd.InputStream(samplerate=self.sample_rate, channels=1, blocksize=self.chunk_size, callback=self.audio_callback)
        self.stream.start()

        # Timer to update the plot every 50 ms after buffer is filled
        self.plot_initialized = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(1000)

    def audio_callback(self, indata, frames, time, status):
        """Collect audio data into the buffer."""
        if True:
            # Shift the buffer to the left and append new data at the end
            self.audio_buffer = np.roll(self.audio_buffer, -len(indata))
            self.audio_buffer[-len(indata):] = indata[:, 0]

            # Check if we've filled the buffer for 2 seconds
            if np.count_nonzero(self.audio_buffer) > 0:
                self.plot_initialized = True

    def update_plot(self):
        """Update the plot only after 2 seconds of data is collected."""
        self.line.set_ydata(self.audio_buffer)  # Update the plot with the buffer data

        self.y_max_lim = np.max([self.y_max_lim, np.max(self.audio_buffer)])
        self.y_min_lim = np.min([self.y_min_lim, np.min(self.audio_buffer)])
        self.ax.set_ylim(self.y_min_lim, self.y_max_lim)
        self.ax.draw_artist(self.line)
        self.fig.canvas.draw()