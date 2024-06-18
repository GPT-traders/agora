import numpy as np
import pyagora
import time

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
    token = "007eJxTYKitW3XbOPLHPElf/smhNo2Tmf4vS1bba51hKPy6VOyDq7sCg0WqWbKFSWJqimWigYlBYpplWmJKSrKBhaW5qam5SUqqyc7ctIZARoZ76pKsjAwQCOLzMaSk5ubHJ2ck5uWl5sQbMjAAADPrIb4="
    channel_id = "demo_channel_1"
    user_id = "3"
    out_connect=agora.connect(token, channel_id, user_id)
    print(out_connect)
    agora.create_audio_track()

    try:
        prev_time=0
        max_process_time=0
        for frame in read_pcm_file(file_name, sample_rate, num_channels):
            # print(frame)
            num_samples = len(frame) // (num_channels * 2)  # 2 bytes per sample (16-bit audio)
            # print(num_samples,num_channels,sample_rate)
            agora.send_audio_pcm_data(frame, num_samples, 2, num_channels, sample_rate)
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
