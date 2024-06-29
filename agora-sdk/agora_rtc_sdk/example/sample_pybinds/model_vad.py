import numpy as np
import torch

class SileroVAD:
    def __init__(self, repo_or_dir='snakers4/silero-vad', model_name='silero_vad', force_reload=True):
        # Load the model using torch.hub
        self.model, self.utils = torch.hub.load(repo_or_dir=repo_or_dir,
                                                model=model_name,
                                                force_reload=force_reload)

    def int2float(self, sound):
        """Converts int16 audio data to float32."""
        abs_max = np.abs(sound).max()
        sound = sound.astype('float32')
        if abs_max > 0:
            sound *= 1 / 32768
        sound = sound.squeeze()  # Adjust based on the specific use case
        return sound

    def process_pcm_buffers(self, pcm_buffers,SAMPLING_RATE=16000):
        """Process PCM buffers to get voice activity detection confidence levels."""
        voiced_confidences = []
        for buffer in pcm_buffers:
            audio_int16 = np.frombuffer(buffer, np.int16)
            audio_float32 = self.int2float(audio_int16)
            window_size_samples = 512 if SAMPLING_RATE == 16000 else 256
            for i in range(0, len(audio_float32), window_size_samples):
                chunk = audio_float32[i: i+ window_size_samples]
                if len(chunk) < window_size_samples:
                    chunk=audio_float32[-window_size_samples:]
                # speech_prob = model(chunk, SAMPLING_RATE).item()
                # speech_probs.append(speech_prob)
                vad_output = self.model(torch.from_numpy(chunk), SAMPLING_RATE).item()
                voiced_confidences.append(vad_output)
        return voiced_confidences

    def read_and_process_pcm_file(self, file_path):
        """Reads PCM file, splits it into frames and processes each frame."""
        fs = 16000  # Sampling frequency
        frame_duration = 0.1  # Frame duration in seconds (10 ms)
        frame_samples = int(fs * frame_duration)  # Number of samples per frame

        # Read the raw PCM file
        with open(file_path, 'rb') as file:
            audio_data = file.read()

        # Split the audio data into frames
        num_frames = len(audio_data) // (frame_samples * 2)  # 2 bytes per sample (int16)
        frames = [audio_data[i * frame_samples * 2:(i + 1) * frame_samples * 2] for i in range(num_frames)]
        print(len(frames))

        # Process each frame
        confidences = self.process_pcm_buffers(frames)
        return confidences

# # Usage
# # Initialize the SileroVAD class
# vad_processor = SileroVAD()

# # Example of processing a file (replace 'path_to_pcm_file.pcm' with your file path)
# vad_outputs = vad_processor.read_and_process_pcm_file('output_audio_from_python.pcm')
# print("VAD Outputs:", vad_outputs)
