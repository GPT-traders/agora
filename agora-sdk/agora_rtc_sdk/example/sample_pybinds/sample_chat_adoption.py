import uuid
from datetime import datetime
from typing import List, Dict
import chat_utils
import PROMPT_TEMPLATES


def Message( text, created_by, created_at):
    return{
        "text" : text,
        "created_by" : created_by,
        "created_at" : created_at
    }

class Chat:
    def __init__(self, job_id):
        self.session_id = str(uuid.uuid4())
        self.job_id = job_id
        self.messages = []
        self.started_by = None

    def start_new_chat(self):
        jd_context = PROMPT_TEMPLATES.JD
        message_text = PROMPT_TEMPLATES.context_prompt.format(jd_context=jd_context)
        system_message = Message(text=message_text, 
                                 created_by="system", 
                                 created_at=datetime.now())
        print(system_message)
        self.messages.append(system_message)
        # self.started_by = user_email
        return self.session_id

    async def send_message(self, message):
        msg = Message(text=message, created_by="candidate", created_at=datetime.now())
        self.messages.append(msg)
        langchain_msg = chat_utils.convert_msg2dict(self.messages)
        langchain_response = await chat_utils.invoke_langchain(langchain_msg)
        # print()
        ai_message = Message(text=langchain_response.content, 
                             created_by="ai", 
                             created_at=datetime.now())
        self.messages.append(ai_message)
        return langchain_response.content

    # @staticmethod
    # def invoke_langchain(messages):
    #     response = "AI Response: " + " ".join(msg.text for msg in messages if msg.created_by != 'ai')
    #     return response

# chat = Chat("1")
# session_id = chat.start_new_chat()
# print(f"Chat session started with ID: {session_id}")

# import asyncio
# response =asyncio.run(chat.send_message("Hi how are you"))
# print("Langchain response:", response)
