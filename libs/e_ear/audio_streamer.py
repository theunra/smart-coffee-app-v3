import numpy as np
import sounddevice as sd

class AudioStreamer:
    def __init__(self, sample_rate = 44100, chunk_size = 512 , buffer_duration = 5, onNewSample = None):
        # Initialize buffer to store audio data
        total_samples = int(sample_rate * buffer_duration)  # Total samples to collect
        self.audio_buffer = np.zeros(total_samples)

        self.total_sampling_count = int(sample_rate * buffer_duration / chunk_size)
        self.sampling_count = 0

        self.audio_buffer_ready = False

        self.__onNewSample = onNewSample

        # Sound device stream
        self.stream = sd.InputStream(samplerate=sample_rate, channels=1, blocksize=chunk_size, callback=self.audio_callback)
        self.stream.start()

    def audio_callback(self, indata, frames, time, status):
        """Collect audio data into the buffer."""
        new_data = indata[:, 0]  # New audio data from the first channel (mono)

        # Roll the buffer and append new data
        shift_len = len(new_data)  # Number of new samples
        self.audio_buffer = np.roll(self.audio_buffer, -shift_len)
        self.audio_buffer[-shift_len:] = new_data  # Append new data to the end of the buffer

        if(self.__onNewSample != None):
            self.__onNewSample(new_data)
        else:
            print("no callback")

        # self.audio_buffer_ready = True

        # if(self.sampling_count >= self.total_sampling_count):
        #     self.audio_buffer_ready = True
        #     self.sampling_count = 0

        # else:
        #     self.audio_buffer_ready = False
        #     self.sampling_count = self.sampling_count + 1