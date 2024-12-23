from flask import Flask, render_template, Response, stream_with_context
import json
import numpy as np
import time
import random
import sounddevice as sd
import cv2
import librosa
import librosa.display
import io
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

camera = cv2.VideoCapture(0)

sample_rate = 44100
chunk_size = 1024  # Number of samples per chunk (frame)
buffer_duration = 5  # Buffer duration in seconds
total_samples = int(sample_rate * buffer_duration)  # Total samples to collect

# Initialize buffer to store audio data
audio_buffer = np.zeros(total_samples)

audio_buffer_ready = False

def audio_callback(indata, frames, time, status):
    global audio_buffer, audio_buffer_ready
    """Collect audio data into the buffer."""
    new_data = indata[:, 0]  # New audio data from the first channel (mono)

    # Roll the buffer and append new data
    shift_len = len(new_data)  # Number of new samples
    audio_buffer = np.roll(audio_buffer, -shift_len)
    audio_buffer[-shift_len:] = new_data  # Append new data to the end of the buffer

    # notify
    audio_buffer_ready = True

# Sound device stream
stream = sd.InputStream(samplerate=sample_rate, channels=1, blocksize=chunk_size, callback=audio_callback)
stream.start()


@app.route('/')
def index():
    return render_template('index.html')

def gen_video(camera : cv2.VideoCapture):
    while True:
        ret, frame = camera.read()
        success, jpeg_data = cv2.imencode('.jpeg', frame)
        jpeg_bytes = jpeg_data.tobytes()  # Convert to bytes if needed

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
        
def gen_audio():
    global audio_buffer_ready, audio_buffer
    while True:
        if(audio_buffer_ready):
            # Compute Short-Time Fourier Transform (STFT)
            stft = librosa.stft(audio_buffer, n_fft=1024, hop_length=512)
            spectrogram = librosa.amplitude_to_db(np.abs(stft), ref=np.max)

            # Convert the spectrogram to a grayscale image
            normalized_spectrogram = cv2.normalize(spectrogram, None, 0, 255, cv2.NORM_MINMAX)
            spectrogram_image = np.uint8(normalized_spectrogram)

            # Flip the spectrogram vertically
            spectrogram_image = cv2.flip(spectrogram_image, 0)

            # Apply a colormap to create a colored spectrogram
            spectrogram_image = cv2.applyColorMap(spectrogram_image, cv2.COLORMAP_JET)

            spectrogram_image = cv2.resize(spectrogram_image, (500, 500), interpolation=cv2.INTER_CUBIC)


            success, jpeg_data = cv2.imencode('.jpeg', spectrogram_image)
            jpeg_bytes = jpeg_data.tobytes()  # Convert to bytes if needed

            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')

            audio_buffer_ready = False

data = np.zeros(30)

def gen_sensor():
    global data    

    while True:
        # Simulate a server-sent event
        data = np.roll(data, -1)
        data[len(data) - 1] = random.randint(0, 100)

        payload = {}
        payload['data'] = data.tolist()
        print(payload)
        time.sleep(1)  # Send updates every second
        yield f"id: message\ndata: {json.dumps(payload)}\n\n"

@app.route('/video_feed')
def video_feed():
    return Response(gen_video(camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/audio_feed')
def audio_feed():
    return Response(gen_audio(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Define a route for SSE
@app.route('/sensor_feed')
def sensor_feed():
    return Response(stream_with_context(gen_sensor()), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

    # camera.release()