import openai
import credentials 
import json
import requests
import mysql.connector
from mysql.connector import Error


openai.api_key = credentials.openai_key


# def getChat(guild):
#     chat = []
#     try:
#         connection = mysql.connector.connect(host="localhost",
#                                              database="gpt_bot",
#                                              user="root",
#                                              password="root")
#         cursor = connection.cursor()
        
#     except mysql.connector.Error as error: 
#         print("Failed to create table: {}".format(error))


#     return chat


# def saveQuestion(guild, question):
#     try:
#         connection = mysql.connector.connect(host="localhost",
#                                              database="gpt_bot",
#                                              user="root",
#                                              password="root")
#         mySql_Create_Table_Query = """CREATE TABLE DB_""" + str(guild) + """ (
#         Id int(11) NOT NULL AUTO_INCREMENT,
#         User varchar(250) NOT NULL,
#         Message varchar(5000) NOT NULL,
#         PRIMARY KEY (Id)) """

#         cursor = connection.cursor()
#         result = cursor.execute(mySql_Create_Table_Query)
#         print("Table created")

#     except mysql.connector.Error as error:
#         print("Failed to create table: {}".format(error))

#     finally:
#         if connection.is_connected():
#             table = "DB_" + str(guild)
#             mySql_Insert_Row_Query = "INSERT INTO " + table + " (question) VALUES (%s)"
#             message = {"role": "user", "content": question}
#             mySql_Insert_Row_values = (message)
#             cursor.execute(mySql_Insert_Row_Query, mySql_Insert_Row_values)

            

#             print("question stored in db")

#             cursor.close()

#             connection.close()

# def saveAnswer(guild, answer):
#     try:
#         connection = mysql.connector.connect(host="localhost",
#                                              database="gpt_bot",
#                                              user="root",
#                                              password="root")
#         cursor = connection.cursor()

#     except mysql.connector.Error as error:
#         print("Failed to create table: {}".format(error))
#     finally:
#         if connection.is_connected():
#             table = "DB_" + str(guild)
#             mySql_Insert_Row_Query = "INSERT INTO " + table + " (answer) VALUES (%s)"
#             mySql_Insert_Row_values = (answer)
#             cursor.execute(mySql_Insert_Row_Query, mySql_Insert_Row_values)
    
#     print("question stored in db")

#     cursor.close()
#     connection.close()

chat=[]

def romanize(text):
    response = openai.Completion.create(
        model="text-curie-001",
        prompt=f"Romanize this: {text}",
        temperature=0.3,
        max_tokens=200,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
    print(response['choices'][0]['text'].lstrip("\n"))
    return response['choices'][0]['text'].lstrip("\n")

def translate(text, targetLang):
    response = openai.Completion.create(
        model="text-curie-001",
        prompt=f"Translate this into {targetLang}: {text}",
        temperature=0.3,
        max_tokens=200,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
    print(response['choices'][0]['text'].lstrip("\n"))
    return response['choices'][0]['text'].lstrip("\n")

def ask(guild, question):
    # saveQuestion(guild, answer)
    # chat = getChat(guild)
    chat.append({"role": "user", "content": question})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
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

