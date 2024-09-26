import wave

import wave
import numpy as np

# Open the WAV file
with wave.open('Audio_fs_48000_Chans_2_1725816438.wav', 'rb') as wav_file:
    # Read parameters
    num_channels = wav_file.getnchannels()
    sample_width = wav_file.getsampwidth()
    frame_rate = wav_file.getframerate()
    num_frames = wav_file.getnframes()

    # Read audio data
    audio_data = wav_file.readframes(num_frames)

    # Convert byte data to numpy array
    audio_array = np.frombuffer(audio_data, dtype=np.int16)

# Reshape if stereo
if num_channels == 2:
    audio_array = audio_array.reshape(-1, 2)

print(audio_array)
