import cv2 as cv

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QImage


class VisionStreamer():
    def __init__(self):
        self.cap = cv.VideoCapture(0)  # Use camera index 0 (default camera)

        self.timer = QTimer()
        # self.timer.timeout.connect(self.update_image)
        self.timer.start(30)

class CameraDisplay(QLabel):
    def __init__(self, vision_streamer : VisionStreamer):
        super(CameraDisplay, self).__init__()

        self.vision_streamer = vision_streamer
        self.vision_streamer.timer.timeout.connect(self.update_image)

        pixmap = QPixmap(500, 500)
        pixmap.fill()
        self.setPixmap(pixmap)


    def update_image(self):
        # Read frame from the camera
        ret, frame = self.vision_streamer.cap.read()

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
            self.setPixmap(pixmap)
            self.setAlignment(Qt.AlignCenter)