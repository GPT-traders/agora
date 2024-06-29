import numpy as np
import pyagora
import time
import chat_utils
def read_pcm_file(file_name, sample_rate=16000, num_channels=1, bytes_per_sample=2):
    """Read PCM file and yield chunks of audio data."""
    chunk_size = sample_rate // 100 * num_channels * bytes_per_sample  # 10ms of audio
    print(chunk_size)
    with open(file_name, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data

def wait_before_next_send(interval):
    """Wait for a specified interval in milliseconds."""
    time.sleep(interval)  # Convert ms to seconds

def send_audio(file_name, sample_rate=16000, num_channels=1):
    """Initialize Agora, create audio track, and send PCM data from file."""
    agora = pyagora.AgoraAPI()
    token = "007eJxTYPh6yXH7/RmFZ05eFFr74dzdyN8l67WK/vrc3VSysrretSFLgcEi1SzZwiQxNcUy0cDEIDHNMi0xJSXZwMLS3NTU3CQl1aevPq0hkJFhp+B1VkYGCATxeRhSUnPz45MzEvPyUnMYGAD9FScx"
    channel_id = "demo_channel"
    user_id = "12345"
    out_connect=agora.connect(token, channel_id, user_id)
    print(out_connect)
    agora.create_audio_track()

    try:
        prev_time=0
        max_process_time=0
        # for frame in read_pcm_file(file_name, sample_rate, num_channels):
        #     # print(frame)
        #     num_samples = len(frame) // (num_channels * 2)  # 2 bytes per sample (16-bit audio)
        #     # print(num_samples,num_channels,sample_rate)
        #     agora.send_audio_pcm_data(frame, num_samples, 2, num_channels, sample_rate)
        #     if prev_time==0:
        #         wait_before_next_send(10/1000)
        #     else:
        #         # max_process_time = max(max_process_time,(time.time()-prev_time))
        #         # print(max_process_time)
        #         wait_time=(10/1000)-(time.time()-prev_time)
        #         time.sleep(wait_time)

        #         # wait_before_next_send(wait_time)
        #     prev_time = time.time()
        wav_response=chat_utils.convert_txt2wav("This is a sample response to test!!!")
        # for chunk in wav_response.iter_bytes(chunk_size=320):
        #     print(len(chunk))
        # for bytes in wav_response.aiter_bytes(320):
        #     print(bytes)
        wav_response.stream_to_file("output.pcm")
        sample_rate=24000 
        num_channels=1
        bytes_per_sample=2
        chunk_size = sample_rate // 100 * num_channels * bytes_per_sample
        for chunk in wav_response.iter_bytes(chunk_size=chunk_size):#frame in read_pcm_file(file_name, sample_rate, num_channels):
            # print(chunk)
            num_samples = len(chunk) // (num_channels * 2)  # 2 bytes per sample (16-bit audio)
            # print(num_samples,num_channels,sample_rate)
            agora.send_audio_pcm_data(chunk, num_samples, 2, num_channels, 24000)
            if prev_time==0:
                wait_before_next_send(10/1000)
            else:
                # max_process_time = max(max_process_time,(time.time()-prev_time))
                # print(max_process_time)
                wait_time=(10/1000)-(time.time()-prev_time)
                time.sleep(wait_time)

                # wait_before_next_send(wait_time)
            prev_time = time.time()
    finally:
        agora.disconnect()

# Usage
send_audio("../out/test_data/send_audio_16k_1ch.pcm")
