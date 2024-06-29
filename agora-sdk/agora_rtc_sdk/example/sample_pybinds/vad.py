import numpy as np
import torch

# Load your model here instead of the dummy model
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=True)


# Helper function to convert int16 audio data to float32
def int2float(sound):
    abs_max = np.abs(sound).max()
    sound = sound.astype('float32')
    if abs_max > 0:
        sound *= 1 / 32768
    sound = sound.squeeze()  # Adjust based on the specific use case
    return sound

# Function to process PCM buffers
def process_pcm_buffers(pcm_buffers):
    voiced_confidences = []
    for buffer in pcm_buffers:
        audio_int16 = np.frombuffer(buffer, np.int16)
        audio_float32 = int2float(audio_int16)
        vad_output = model(torch.from_numpy(audio_float32), 16000).item()
        voiced_confidences.append(vad_output)
    return voiced_confidences

# Reading the PCM file and processing it
def read_and_process_pcm_file(file_path):
    fs = 16000  # Sampling frequency
    frame_duration = 0.1  # 10 ms
    frame_samples = int(fs * frame_duration)  # Number of samples in one frame

    # Read the raw PCM file
    with open(file_path, 'rb') as file:
        audio_data = file.read()
    print(frame_samples)
    # Split the audio data into 10 ms frames
    num_frames = len(audio_data) // (frame_samples * 2)  # 2 bytes per sample (int16)
    frames = [audio_data[i * frame_samples * 2:(i + 1) * frame_samples * 2] for i in range(num_frames)]
    print(len(frames))
    # Process each frame
    confidences = process_pcm_buffers(frames)
    return confidences

# Example of using the function
# Replace 'path_to_pcm_file.pcm' with the actual path to your PCM file
vad_outputs = read_and_process_pcm_file('output_audio_from_python.pcm')
print("VAD Outputs:", vad_outputs)
