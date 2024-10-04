import sys
import numpy as np
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QOpenGLWidget
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import cv2 as cv

import pyqtgraph as pg
import OpenGL.GL as gl

import sounddevice as sd
import scipy.io.wavfile as wav


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

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Load the .ui file dynamically
        uic.loadUi('main_window.ui', self)

        # # Connect the button for switching pages
        # self.acquireButton.clicked.connect(self.show_monitoring_page)

        # Create custom widgets (Graph and Spectrum) and insert them into layouts
        self.graph_canvas = GraphCanvas(self)
        # self.audio_canvas = AudioPlotCanvas(self)
        # self.audio_widget = AudioPlotWidget()  # No need to pass 'self' here
        # self.spectrum_canvas = SpectrumCanvas(self)
        self.audio_widget = AudioPlotOpenGL()

        # # Insert the canvases into the respective layouts in the UI
        graph_layout = QVBoxLayout(self.graphWidget)  # Assuming graphWidget is the placeholder in Qt Designer
        graph_layout.addWidget(self.graph_canvas)

        spectrum_layout = QVBoxLayout(self.spectrumWidget)  # Assuming spectrumWidget is the placeholder in Qt Designer
        spectrum_layout.addWidget(self.audio_widget)

        # Set an initial image in the QLabel (image frame)
        pixmap = QPixmap(500, 500)
        pixmap.fill()
        self.imageLabel.setPixmap(pixmap)

        self.cap = cv.VideoCapture(0)  # Use camera index 0 (default camera)

        # Timer to update the image
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_image)
        self.timer.start(30)


    def update_audio(self):
        self.spectrum_canvas.update_spectrum()

    def update_image(self):
        # Read frame from the camera
        ret, frame = self.cap.read()

        if ret:
            target = 400
            h = frame.shape[0]
            w = frame.shape[1]

            sh = int(abs(h - target) / 2)
            sw = int(abs(w - target) / 2)
            
            frame = frame[sh:target + sh, sw:target + sw]
            # Convert the frame from BGR to RGB
            rgb_image = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

            # Get image dimensions
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w

            # Create QImage from RGB data
            q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

            # Convert QImage to QPixmap and set it in the QLabel
            pixmap = QPixmap.fromImage(q_image)
            self.imageLabel.setPixmap(pixmap)
            self.imageLabel.setAlignment(Qt.AlignCenter)

    # def show_monitoring_page(self):
    #     self.stackedWidget.setCurrentWidget(self.monitoringPage)

# Main execution
if __name__ == '__main__':
    app = QApplication(sys.argv)    
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
