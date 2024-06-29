import os

import sys
# sys.path.append("./")
# print("-------------------")
# print(os.listdir("./"))
import pyagora_receive_callback as pyagora
import time
import model_vad
import numpy as np
import chat_utils
import sample_chat_adoption
import asyncio
# from langchain.prompts import PromptTemplate


def main():
    options = pyagora.SampleOptions()
    options.appId = "007eJxTYHD9y/ds9m25gvRNKax5S63apyiaOzcKFxjcureRcWK0+FIFBotUs2QLk8TUFMtEAxODxDTLtMSUlGQDC0tzU1Nzk5RU/qt1aQ2BjAy6kr2MjAwQCOLzMKSk5ubHJ2ck5uWl5jAwAADfsSDV"
    options.channelId = "demo_channel"
    options.userId = "12345"
    vad_processor = model_vad.SileroVAD()
    options.audioFile = "output_audio.pcm"

    agora = pyagora.PyAgora(options)
    frames_queue=[]
    silent_count=0
    compiled_audio =[]
    chat = sample_chat_adoption.Chat("1")
    session_id = chat.start_new_chat()
    print(f"Chat session started with ID: {session_id}")    
    
    if agora.connect():
        print("Connected successfully.")
        try:
            with open('output_audio_from_python.pcm', 'wb') as f:
                start_time = time.time()
                while (time.time() - start_time) < 200:  # run for 10 seconds
                    if not agora.pcm_frame_observer.is_queue_empty():
                        audio_data = agora.pcm_frame_observer.pop_audio_data()
                        # print(len(frames_queue))
                        # print(len(audio_data))
                        if len(frames_queue)<10:
                            frames_queue.append(bytes(audio_data))
                        else:
                            # print(frames_queue[0])
                            merged_bytes= b''.join(frames_queue)
                            frames_queue=[]
                            vad_out=vad_processor.process_pcm_buffers([merged_bytes])
                            # print(vad_out)
                            if np.array(max(vad_out)) > 0.1:
                                # print("--------------")
                                # print(vad_out)
                                compiled_audio.append(merged_bytes)  
                                silent_count=0 
                            else:
                                silent_count+=1
                                if silent_count>30 and len(compiled_audio)>0:
                                    prev_time=time.time()
                                    compiled_audio_merged = b"".join(compiled_audio)
                                    transcription = chat_utils.convert_bytes2text(bytes(compiled_audio_merged))
                                    now_time= time.time()
                                    print(transcription)
                                    response =asyncio.run(chat.send_message(transcription))
                                    print(response)
                                    print("Trasncription time:",now_time-prev_time)
                                    silent_count=0
                                    compiled_audio=[]
                                    compiled_audio_merged=""

                        # print(f"Received audio data of length: {len(audio_data)}")
                        # Write audio data to the file
                        f.write(bytes(audio_data))
                    # time.sleep(0.01)  # Sleep to reduce CPU usage
        except KeyboardInterrupt:
            print("Loop has been stopped by Ctrl+C.")
        finally:
            agora.disconnect()
            print("Disconnected.")
    else:
        print("Connection failed.")

if __name__ == "__main__":
    main()
