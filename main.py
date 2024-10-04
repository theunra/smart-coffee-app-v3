import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout

from libs.e_ear.audio_plot_opengl import AudioPlotOpenGL
from libs.e_nose.graph_canvas import GraphCanvas
from libs.e_eye.camera_display import CameraDisplay



class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Load the .ui file dynamically
        uic.loadUi('main_window.ui', self)

        self.graph_canvas = GraphCanvas(self)
        self.audio_widget = AudioPlotOpenGL()
        self.camera_display = CameraDisplay()

        # # Insert the canvases into the respective layouts in the UI
        graph_layout = QVBoxLayout(self.graphWidget)  # Assuming graphWidget is the placeholder in Qt Designer
        graph_layout.addWidget(self.graph_canvas)

        spectrum_layout = QVBoxLayout(self.spectrumWidget)  # Assuming spectrumWidget is the placeholder in Qt Designer
        spectrum_layout.addWidget(self.audio_widget)

        image_layout = QVBoxLayout(self.imageWidget)
        image_layout.addWidget(self.camera_display)

# Main execution
if __name__ == '__main__':
    app = QApplication(sys.argv)    
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
