from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import QTimer

import OpenGL.GL as gl
import sounddevice as sd
import numpy as np

import scipy.io.wavfile as wav

class AudioPlotOpenGL(QOpenGLWidget):
    def __init__(self, sample_rate=44100, buffer_duration=900, downsample_rate=44 * 2):
        super().__init__()
        self.sample_rate = sample_rate
        self.downsample_rate = downsample_rate  # Downsample from 44,100 Hz to 1,000 Hz
        self.buffer_duration = buffer_duration  # Buffer duration in seconds (15 minutes = 900 seconds)
        self.total_samples = int((self.sample_rate / self.downsample_rate) * self.buffer_duration)  # 900,000 samples for 15 min

        self.audio_buffer = np.zeros(self.total_samples)
        self.current_index = 0  # Index to track where to place new audio samples


        self.stream = sd.InputStream(samplerate=self.sample_rate, channels=1, blocksize=1024, callback=self.audio_callback)
        self.stream.start()

        # OpenGL update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(5000)  # Approx 60 FPS

    def initializeGL(self):
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)  # Set the background color (black)
        gl.glLineWidth(2)  # Set the line width for the audio plot

    def resizeGL(self, w, h):
        gl.glViewport(0, 0, w, h)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0, self.total_samples, -1, 1, -1, 1)  # Adjust the orthographic view for the total sample size
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glLoadIdentity()

        # Draw audio signal as a line strip
        gl.glColor3f(0.0, 1.0, 0.0)  # Green color for the line
        gl.glBegin(gl.GL_LINE_STRIP)
        for i in range(self.total_samples):
            gl.glVertex2f(i, self.audio_buffer[i])
        gl.glEnd()

    # def audio_callback(self, indata, frames, time, status):
    #     """Callback for audio input. Receives audio samples."""
    #     new_data = indata[:, 0]  # Mono audio data
    #     downsampled_data = new_data[::self.downsample_rate]  # Downsample the audio data
    #     shift_len = len(downsampled_data)

    #     self.audio_buffer = np.roll(self.audio_buffer, -shift_len)
    #     self.audio_buffer[-shift_len:] = downsampled_data
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio input. Receives audio samples."""
        new_data = indata[:, 0]  # Mono audio data
        downsampled_data = new_data[::self.downsample_rate]  # Downsample the audio data
        shift_len = len(downsampled_data)

        # Ensure we don't exceed buffer length
        if self.current_index + shift_len < self.total_samples:
            # Update the buffer with new downsampled data
            self.audio_buffer[self.current_index:self.current_index + shift_len] = downsampled_data
            self.current_index += shift_len  # Move the index forward
        else:
            # If buffer is full, roll the buffer left and add new samples at the end
            remaining = self.total_samples - self.current_index
            self.audio_buffer[:remaining] = self.audio_buffer[self.current_index:]
            self.audio_buffer[remaining:] = downsampled_data[:shift_len - remaining]
            self.current_index = self.total_samples  # Buffer is now full

        # If there's no audio, keep the rest of the buffer filled with zeros
        if np.max(np.abs(new_data)) == 0:
            self.audio_buffer[-shift_len:] = 0
