from flask import Flask, render_template, Response, stream_with_context, request
import json
from queue import Queue
import numpy as np
import time
import random
import pandas as pd
import cv2
import librosa
import librosa.display
from flask_cors import CORS
from libs.database.database import Database
from libs.e_ear.audio_streamer import AudioStreamer

from libs.e_nose.SerialHandler import SerialHandler
import threading
from datetime import datetime
import json
import struct

class Command:
  STOP_SESSION = 0
  START_SESSION = 1
  PAUSE_SESSION = 2
  SET_ROAST_LEVEL = 3

class Message:
    START_SAMPLING = 0
    STOP_SAMPLING = 1
    CYCLE_START = 2
    SENSOR_DATA = 3

PORT = "/dev/ttyUSB0"
# PORT = "COM18"
BAUDRATE = 115200

serial_handler = SerialHandler(PORT, BAUDRATE)
status = "preheat"
filetime = datetime.now().isoweekday()
filename = "output.txt"
is_run = True

app = Flask(__name__)

CORS(app)

import cv2, glob

"""
camera = None

for camera_id in glob.glob("/dev/video?"):
    try:
        camera = cv2.VideoCapture(camera_id)
    except Exception as e:
        print(e)
        
if(camera == None):
    exit();
else:
    print(camera)
"""
camera = cv2.VideoCapture(0)

audio_buffer = np.array([])
audio_buffer_max_len = 44100 # 44100 sample rate, 1 seconds

def onNewSampleAudio(samples):
    global audio_buffer, audio_buffer_max_len

    if(len(audio_buffer) >= audio_buffer_max_len):
        # print("process audio data")
        audio_buffer = np.array([])
    else:
        audio_buffer = np.concatenate((audio_buffer,samples), axis=0)

audio_streamer = AudioStreamer(onNewSample=onNewSampleAudio)

gas_datas :  pd.DataFrame = pd.DataFrame()
gas_datas["MQ135"] = np.zeros(30).tolist()
gas_datas["MQ136"] = np.zeros(30).tolist()
gas_datas["MQ137"] = np.zeros(30).tolist()
gas_datas["MQ138"] = np.zeros(30).tolist()
gas_datas["MQ2"] = np.zeros(30).tolist()
gas_datas["MQ3"] = np.zeros(30).tolist()
gas_datas["TGS822"] = np.zeros(30).tolist()
gas_datas["TGS2620"] = np.zeros(30).tolist()

def gasDFtoJson(datas : pd.DataFrame):
    mq136 = datas.iloc[:,0].to_list()
    mq135 = datas.iloc[:,1].to_list()
    mq137 = datas.iloc[:,2].to_list()
    mq138 = datas.iloc[:,3].to_list()
    mq2 = datas.iloc[:,4].to_list()
    mq3 = datas.iloc[:,5].to_list()
    tgs822 = datas.iloc[:,6].to_list()
    tgs2620 = datas.iloc[:,7].to_list()

    return json.dumps({
        "mq135" : mq135,
        "mq136" : mq136,        
        "mq137" : mq137,
        "mq138" : mq138,
        "mq2" : mq2,
        "mq3" : mq3,
        "tgs822" : tgs822,
        "tgs2620" : tgs2620
    })


@app.route('/')
def index():
    return render_template('index.html')

def gen_video():
    global image_jpeg_bytes, camera

    while True:
        ret, frame = camera.read()

        success, jpeg_data = cv2.imencode('.jpeg', frame)
        jpeg_bytes = jpeg_data.tobytes()  # Convert to bytes if needed

        image_jpeg_bytes = jpeg_bytes

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
        
def gen_audio():
    global audio_streamer

    while True:
        # Compute Short-Time Fourier Transform (STFT)
        stft = librosa.stft(audio_streamer.audio_buffer, n_fft=1024, hop_length=512)
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

        audio_jpeg_bytes = jpeg_bytes

        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')

        audio_streamer.audio_buffer_ready = False

temp_mq135  = 0
temp_mq136  = 0
temp_mq137  = 0
temp_mq138  = 0
temp_mq2    = 0
temp_mq3    = 0
temp_tgs822 = 0
temp_2620   = 0

gas_data_counter = 0
gas_data_max = 20

def gen_sensor():
    global gas_datas, gas_data_counter, gas_data_max
    global temp_mq135, temp_mq136, temp_mq137, temp_mq138, temp_mq2, temp_mq3, temp_tgs822, temp_2620  

    while True:
        try:
            data = serial_handler.read()

            message_id = data[0]
            
            if(message_id == Message.SENSOR_DATA):
                sensor_datas = struct.unpack("HHHHHHHHff", data[1:len(data) - 3])
                temp_mq135  += sensor_datas[0] / gas_data_max
                temp_mq136  += sensor_datas[1] / gas_data_max
                temp_mq137  += sensor_datas[2] / gas_data_max
                temp_mq138  += sensor_datas[3] / gas_data_max
                temp_mq2    += sensor_datas[4] / gas_data_max
                temp_mq3    += sensor_datas[5] / gas_data_max
                temp_tgs822 += sensor_datas[6] / gas_data_max
                temp_2620   += sensor_datas[7] / gas_data_max

                gas_data_counter += 1

            elif(message_id == Message.CYCLE_START):
                print("cyclestart")
            
            if(gas_data_counter >= gas_data_max):
                gas_data_counter = 0

                gas_datas["MQ135"]      = gas_datas["MQ135"].shift(-1,      fill_value=temp_mq135)
                gas_datas["MQ136"]      = gas_datas["MQ136"].shift(-1,      fill_value=temp_mq136)
                gas_datas["MQ137"]      = gas_datas["MQ137"].shift(-1,      fill_value=temp_mq137)
                gas_datas["MQ138"]      = gas_datas["MQ138"].shift(-1,      fill_value=temp_mq138)
                gas_datas["MQ2"]        = gas_datas["MQ2"].shift(-1,        fill_value=temp_mq2)
                gas_datas["MQ3"]        = gas_datas["MQ3"].shift(-1,        fill_value=temp_mq3)
                gas_datas["TGS822"]     = gas_datas["TGS822"].shift(-1,     fill_value=temp_tgs822)
                gas_datas["TGS2620"]    = gas_datas["TGS2620"].shift(-1,    fill_value=temp_2620)

                temp_mq135  = 0
                temp_mq136  = 0
                temp_mq137  = 0
                temp_mq138  = 0
                temp_mq2    = 0
                temp_mq3    = 0
                temp_tgs822 = 0
                temp_2620   = 0

                yield f"id: message\ndata: {gasDFtoJson(gas_datas)}\n\n"

        except Exception as e:
            print(e)

# events = Queue()
is_starting = False
progress = 0 #%
start_time = 0 #sec 
roast_level = 'unclass'
duration = 5 * 60 #sec

def gen_events():
    # global events
    global is_starting, progress, start_time, duration
    while True:
        if(is_starting):
            time.sleep(1)

            end_time = start_time + duration

            start_time += 1

            # if(start_time >= 3 * 60):
            #     roast_level = 'light'
            # elif(start_time >= 4 * 60):
            #     roast_level = 'medium'
            # elif(start_time >= 4.3 * 60):
            #     roast_level = 'dark'

            if(start_time >= end_time):
                progress = 100
            else:
                progress = 100 * (start_time / end_time)

            data = {"event" : "roast", "progress" : progress, "level" : roast_level}

            yield f"id: message\ndata: {json.dumps(data)}\n\n"
        else:
            time.sleep(1)

            data = {"event" : "roast", "progress" : 0, "level" : roast_level}

            yield f"id: message\ndata: {json.dumps(data)}\n\n"
        
        # if(events.empty() != True):
            # print("processing events")
            # event = events.get()

@app.route('/video_feed')
def video_feed():
    return Response(gen_video(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/audio_feed')
def audio_feed():
    return Response(gen_audio(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/sensor_feed')
def sensor_feed():
    return Response(stream_with_context(gen_sensor()), 
                    content_type='text/event-stream')

@app.route('/events_feed')
def events_feed():
    return Response(stream_with_context(gen_events()), 
                    content_type='text/event-stream')

@app.route('/session', methods = ['POST'])
def session():
    global is_starting, progress, start_time, duration, roast_level

    if request.method == 'POST':
        data = request.json

        print(f"received post at /session : {data}")

        command = data["command"]

        if(command == Command.START_SESSION):
            print("starting session")
            is_starting = True
            progress = 0 #%
            start_time = 0 #sec 

        elif(command == Command.STOP_SESSION):
            print("stopping session")
            is_starting = False

        elif(command == Command.PAUSE_SESSION):
            print("pausing session")
        
        elif(command == Command.SET_ROAST_LEVEL):
            print("set roast level")
            roast_level = data["level"]

        return Response("ok")

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

    # camera.release()
