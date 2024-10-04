from PyQt5.QtCore import QTimer

import numpy as np
import sounddevice as sd

class AudioPlotWidget(pg.PlotWidget):
    def __init__(self, sample_rate=44100, buffer_duration=60):
        super().__init__()
        self.sample_rate = sample_rate
        self.chunk_size = 1024  # Number of samples per chunk (frame)
        self.buffer_duration = buffer_duration  # Buffer duration in seconds
        self.total_samples = int(self.sample_rate * self.buffer_duration)  # Total samples to collect for 2 seconds
        
        # Time axis for the buffer
        self.time_axis = np.linspace(0, self.buffer_duration, self.total_samples)
        
        # Initialize buffer to store audio data for 2 seconds
        self.audio_buffer = np.zeros(self.total_samples)
        
        # PyQtGraph plot setup
        self.plot = self.plotItem
        self.plot.setTitle("Real-Time Audio Signal")
        self.plot.setLabel('left', 'Amplitude')
        self.plot.setLabel('bottom', 'Time', units='s')
        self.curve = self.plot.plot(self.time_axis, self.audio_buffer, pen='g')

        # Sound device stream
        self.stream = sd.InputStream(samplerate=self.sample_rate, channels=1, blocksize=self.chunk_size, callback=self.audio_callback)
        self.stream.start()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(2000)

    def audio_callback(self, indata, frames, time, status):
        """Collect audio data into the buffer."""
        new_data = indata[:, 0]  # New audio data from the first channel (mono)

        # Roll the buffer and append new data
        shift_len = len(new_data)  # Number of new samples
        self.audio_buffer = np.roll(self.audio_buffer, -shift_len)
        self.audio_buffer[-shift_len:] = new_data  # Append new data to the end of the buffer

        # self.update_plot()

    def update_plot(self):
        """Update the plot with the latest buffer data."""
        self.curve.setData(self.time_axis, self.audio_buffer)