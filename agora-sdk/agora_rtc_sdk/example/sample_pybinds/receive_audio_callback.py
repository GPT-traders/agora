import os
import sys
import pyagora_receive_callback as pyagora
import time
import model_vad
import numpy as np
import chat_utils
import sample_chat_adoption
import asyncio
import pyagora as pyagora_send
import threading
import queue
# from langchain.prompts import PromptTemplate

import signal



def handle_sigint(signum, frame):
    print("SIGINT received, exiting...")
    exit(0)



# Thread function to process data
def process_thread(queue,agora_send):
    prev_time=0
    sample_rate=24000 
    num_channels=1
    bytes_per_sample=2
    chunk_size = sample_rate // 100 * num_channels * bytes_per_sample
    num_samples = chunk_size// (num_channels * 2)  # 2 bytes per sample (16-bit audio)
    log_time=time.time()
    while True:
        
        if queue.empty():
            time.sleep(0.050)
        data = queue.get()  # Get data from the queue
        next_call = time.time()
        for chunk in data.iter_bytes(chunk_size=chunk_size):
            
            if len(chunk)<chunk_size:
                continue
            # print(time.time()-log_time)
            # log_time=time.time()
            # print("Starting to send the data")
            agora_send.send_audio_pcm_data(chunk, num_samples, 2, num_channels, 24000)
            next_call+=0.01
            sleep_time = max(0, next_call - time.time())
            # print(sleep_time)
            time.sleep(sleep_time)

def main():

    ### Signal kill

    signal.signal(signal.SIGINT, handle_sigint)

    ### Meeting Vars
    options = pyagora.SampleOptions()
    options.appId = "007eJxTYJATOOLx9oiNdJCQiT1v2MemO/zcVQ/d7sVwHJnSK3xfs0+BwSLVLNnCJDE1xTLRwMQgMc0yLTElJdnAwtLc1NTcJCX11P2GtIZARgYrUVtGRgYIBPF5GFJSc/PjkzMS8/JScxgYAKE3IKY="
    options.channelId = "demo_channel"
    options.userId = "12345"

    ### VAD setup
    vad_processor = model_vad.SileroVAD()
    options.audioFile = "output_audio.pcm"

    ### receive audio connection
    agora = pyagora.PyAgora(options)

    ### send audio connections
    send_data_queue = queue.Queue()
    agora_send = pyagora_send.AgoraAPI()
    send_connect=agora_send.connect(options.appId, options.channelId, options.userId)
    agora_send.create_audio_track()


    ### Thread connection-to send 
    processing_thread = threading.Thread(target=process_thread, args=(send_data_queue,agora_send,))
    processing_thread.start()

    ### init vars
    frames_queue=[] #vad
    silent_count=0 # interms of 100ms
    compiled_audio =[] #whisper
    output_file=0

    ### init chat session
    chat = sample_chat_adoption.Chat("1")
    session_id = chat.start_new_chat()
    print(f"Chat session started with ID: {session_id}")    
    
    if not agora.connect():
        print("Connection failed.")
    try:
        start_time = time.time()
        while True:  # run for 10 seconds
            if agora.pcm_frame_observer.is_queue_empty():
                time.sleep(0.01)
                continue
            audio_data = agora.pcm_frame_observer.pop_audio_data()
            if len(frames_queue)<10:
                frames_queue.append(bytes(audio_data))
                continue
            merged_bytes= b''.join(frames_queue)
            frames_queue=[]
            vad_out=vad_processor.process_pcm_buffers([merged_bytes])
            # vad_out = [round(num, 3) for num in vad_out]
            # print(f"{vad_out}")
            if np.array(max(vad_out)) > 0.5: # To be changed later 
                compiled_audio.append(merged_bytes)  
                silent_count=0 
                continue
            silent_count+=1
            if silent_count>20 and len(compiled_audio)>0:
                # prev_time=time.time()
                compiled_audio_merged = b"".join(compiled_audio)
                transcription = chat_utils.convert_bytes2text(bytes(compiled_audio_merged))
                # now_time= time.time()
                # print(transcription)
                if len(transcription.text) <2:
                    continue
                response =asyncio.run(chat.send_message(transcription.text))
                print(response)
                pcm_response=chat_utils.convert_txt2wav(response)
                # print("Trasncription time:",now_time-prev_time)
                send_data_queue.put(pcm_response)
                silent_count=0
                compiled_audio=[]
                compiled_audio_merged=""
                
            if (time.time()-start_time)>300:
                break
                    # print("single pass time: ",prev_time-now_time)
    except KeyboardInterrupt:
        print("Loop has been stopped by Ctrl+C.")
    finally:
        agora.disconnect()
        print("Disconnected.")
        

if __name__ == "__main__":
    main()
