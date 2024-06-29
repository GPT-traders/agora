from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
import openai
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import os
from io import BytesIO
from pydub import AudioSegment
# Load environment variables
load_dotenv(Path(".env_openai"))

# Initialize OpenAI with your API key
openai.api_key = os.getenv("OPENAI_API_KEY")
chat = ChatOpenAI(temperature=0, model_name="gpt-4")
client = OpenAI()

async def invoke_langchain(messages):
    """
    Invokes Langchain with a list of messages and returns the response.
    """
    output = chat.invoke(messages)
    return output


def convert_msg2dict(message_db):
    messages_list = []
    for item in message_db:
        # print(item["text"])
        if "ai" in item["created_by"]:
            msg_model = AIMessage(item["text"])
        elif "system" in item["created_by"]:
            msg_model = SystemMessage(item["text"])
        else:
            msg_model = HumanMessage(item["text"])
        messages_list.append(msg_model)
    print(messages_list)
    return messages_list


def convert_bytes2text(bytes):
    pcm_data = bytes  # This should be the bytes of PCM data
    sample_width = 2  # 2 bytes (16 bits)
    frame_rate = 16000  # 44.1 kHz
    channels = 1  # Stereo

    # Create an audio segment
    audio = AudioSegment(
        data=pcm_data,
        sample_width=sample_width,
        frame_rate=frame_rate,
        channels=channels
    )

    # mp3_io = BytesIO()
    audio_file_name="output.mp3"

    # Export to MP3 format into the BytesIO object
    audio.export(audio_file_name, format='mp3' )
    
    # mp3_io.seek(0)  # Rewind the buffer to the beginning

    # # Now mp3_io contains the MP3 bytes, you can use mp3_io.read() to access them
    # mp3_bytes = mp3_io.read()
    audio_file= open(audio_file_name, "rb")
    transcription = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    language = "en", 
                    response_format="text"#"verbose_json"
                    )

    # print(transcription)
    return transcription