from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import requests

load_dotenv()
client = OpenAI(api_key=os.getenv("openai_key"))

chat=[]

def romanize(text):
    response = client.responses.create(
        model="gpt-4.1",
        instructions=f"Romanize this. Do not include any other text.",
        input=text,
    )    
    return response['choices'][0]['text'].lstrip("\n")

def translate(text, targetLang):
    response = client.responses.create(
        model="gpt-4.1",
        instructions=f"Translate this into {targetLang}. Do not include any other text.",
        input=text,
    )
    print(response.output_text)
    return response.output_text

def ask(question):
    # saveQuestion(guild, answer)
    # chat = getChat(guild)
    chat.append({"role": "user", "content": question})
    response = openai.ChatCompletion.create(
        model="o4-mini",
        messages=chat
    )
    answer = response['choices'][0]['message']
    chat.append(answer)
    # saveAnswer(guild, answer)
    return response['choices'][0]['message']['content']

def draw(prompt):
    
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    img_url = response['data'][0]['url']
    print(img_url)
    return img_url

