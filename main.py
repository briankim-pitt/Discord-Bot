import asyncio
import disnake
import discord
import credentials
import gpt
import flashcards
import settings
import mysql.connector
from mysql.connector import Error


from disnake.ext import commands


############# global settings #############
autotranslate = False
romanize = False
targetLang = "English"

languages = [
            disnake.SelectOption(
                label="English", emoji="🇬🇧"), 
            disnake.SelectOption(
                label="Spanish", emoji="🇪🇸"),
            disnake.SelectOption(
                label="French", emoji="🇫🇷"),
            disnake.SelectOption(
                label="Italian", emoji="🇮🇹"),
            disnake.SelectOption(
                label="German", emoji="🇩🇪"),
            disnake.SelectOption(
                label="Korean", emoji="🇰🇷"),
            disnake.SelectOption(
                label="Japanese", emoji="🇯🇵"),
            disnake.SelectOption(
                label="Mandarin", emoji="🇨🇳"),
        ]               

users = {}

###########################################


bot = commands.Bot(
    command_prefix="!",
    intents=disnake.Intents.all()
)
    
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return    

    if bot.user.mentioned_in(message):
        guild = message.guild.id
        print(f"guild: {guild}")
        text = message.content.split(' ', 1)[1]
        print(text)
        async with message.channel.typing():
            await asyncio.sleep(0.1)
            response = gpt.ask(text)
            await message.channel.send(response)
    
    #all non-bot and non-bot-mentioned messages
    else:
        setts = users.get(message.author.id)
        if setts.get_translit():
            response = gpt.romanize(message.content)
            await message.channel.send("Romanized: ||" + response + "||")

        if setts.get_auto_t():
            # Define the button's style and label
            button_style = disnake.ButtonStyle.secondary
            button_label = 'Save'
            button_emoji = '📥'
            # Create the button
            button = disnake.ui.Button(style=button_style, label=button_label, 
                                       emoji=button_emoji, custom_id="save")
            
            response = gpt.translate(message.content, setts.get_tgt_lang())
            await message.reply("Translated: ||" + response + "||", components=[button])
            # await bot.wait_for('button_click', check=lambda i: i.component == button)
            

                    
# @bot.listen("on_dropdown")
# async def help_dropdown(inter: disnake.MessageInteraction):
#     if inter.component.custom_id not in ["dl", "tl"]:
#         return
#     user = inter.author 
#     setts = users.get(user.id)

#     if inter.component.custom_id == "dl":
#         setts.set_def_lang(inter.component.value)
#         await inter.response.send_message("Default language set to " + inter.component.value, ephemeral=True)
#     if inter.component.custom_id == "tl":
#         setts.set_tgt_lang(inter.component.value)
#         await inter.response.send_message("Target language set to " + inter.component.value, ephemeral=True)
     
    
@bot.listen("on_button_click")
async def help_listener(inter: disnake.MessageInteraction):
    if inter.component.custom_id not in ["save", "make_card", "ask", "at_on", "at_off", "tl_on", "tl_off"]:
        return
    
    user = inter.author 
    
    if inter.component.custom_id in ["at_on", "at_off", "tl_on", "tl_off"]:
        setts = users.get(user.id)
        if inter.component.custom_id == "at_on":
            setts.set_auto_t(True)
            await inter.response.send_message("Auto-Translate is now on", ephemeral=True)
        if inter.component.custom_id == "at_off":
            setts.set_auto_t(False)
            await inter.response.send_message("Auto-Translate is now off", ephemeral=True)
        if inter.component.custom_id == "tl_on":
            setts.set_translit(True)
            await inter.response.send_message("Transliterate is now on", ephemeral=True)
        if inter.component.custom_id == "tl_off":
            setts.set_translit(False)
            await inter.response.send_message("Transliterate is now off", ephemeral=True)

    #DM interactions
    if inter.component.custom_id == "make_card":
        await user.send("Making flashcards")
        
    if inter.component.custom_id == "ask":
        await user.send("What would you like to know?")
    
    #server interactions
    if inter.component.custom_id == "save":
        message = extract_text(inter.message.content)
        #send success message
        await inter.response.send_message("✅ Translated message saved in DMs", ephemeral=True)
        repliedfrom = await inter.channel.fetch_message(inter.message.reference.message_id)
        og_msg = repliedfrom.content
        #send embed to user DM
        embed = disnake.Embed(
            title="",
            description="",
            color=0x00FFFF,
            type="rich"            
        )
        # embed.set_author(
        #     name=''
        # )
        embed.add_field(
            name="Original",
            value=og_msg,
            inline=True
        )
        embed.add_field(
            name="Translation",
            value=message,
            inline=True
        )
        
        card_btn = disnake.ui.Button(style=disnake.ButtonStyle.secondary, label="Make flashcards", 
                                       emoji="📝", custom_id="make_card")
        ask_btn = disnake.ui.Button(style=disnake.ButtonStyle.secondary, label="Ask me a question", 
                                       emoji="🤔", custom_id="ask")
        
        text = "I saved part of your conversation from " + "**" + inter.guild.name + "** " + "#" + inter.channel.name + " !"
        await user.send(text, embed=embed, components=[card_btn,ask_btn]) 

def extract_text(input_string):
    # Find the index of the start and end markers
    start_marker = "Translated: ||"
    end_marker = "||"
    start_index = input_string.find(start_marker)
    end_index = input_string.find(end_marker, start_index + len(start_marker))

    if start_index != -1 and end_index != -1:
        # Extract the text between the markers
        extracted_text = input_string[start_index + len(start_marker):end_index]
        return extracted_text.strip()  # Remove leading/trailing whitespace
    else:
        return None

class Dropdown_def_lang(disnake.ui.StringSelect):
    def __init__(self):
        global languages
        super().__init__(
            placeholder="Auto-Translate from", 
            options=languages,
            custom_id="dl"
        )
        
    async def callback(self, inter: disnake.MessageInteraction):
        user = inter.user
        setts = users.get(user.id)
        setts.set_def_lang(self.values[0])
        await inter.response.send_message("Default language set to " + self.values[0], ephemeral=True)
        
class Dropdown_tgt_lang(disnake.ui.StringSelect):
    def __init__(self):
        global languages
        super().__init__(
            placeholder="Auto-Translate to", 
            options=languages,
            custom_id="tl"
        )
        
    async def callback(self, inter: disnake.MessageInteraction):
        user = inter.user
        setts = users.get(user.id)
        setts.set_tgt_lang(self.values[0])
        await inter.response.send_message("Target language set to " + self.values[0], ephemeral=True)

########## SLASH COMMANDS #############

@bot.slash_command(description="Display user profile")
async def profile(inter):
    if users.get(inter.user.id) == None:   
        setts = settings.Settings(inter.guild.id, inter.user.id)
        users.update({inter.user.id: setts})
    else:    
        setts = users.get(inter.user.id)
    at = setts.get_auto_t()
    tr = setts.get_translit()
    dl = setts.get_def_lang()
    tl = setts.get_tgt_lang()
    
    embed = disnake.Embed(
        title= "",
        description="",
        color=0x00FFFF,
        type="rich"            
    )
    
    embed.set_author(
        name=inter.author.name + "'s profile",
        icon_url=inter.author.avatar.url
    )
    
    value = ""
    if(at): value="On" 
    else: value="Off"
    
    embed.add_field(
        name="Auto-Translate",
        value=value,
        inline=True
    )
    
    if(tr): value="On" 
    else: value="Off"
    
    embed.add_field(
        name="Transliterate",
        value=value,
        inline=True
    )
    
    embed.add_field(
        name="Default Language",
        value=dl,
        inline=True
    )
    
    embed.add_field(
        name="Target Language",
        value=tl,
        inline=True
    )
    
    await inter.response.send_message(embed=embed) 
     
@bot.slash_command(description="Change settings")
async def change_settings(inter):  
    if users.get(inter.user.id) == None:   
        setts = settings.Settings(inter.guild.id, inter.user.id)
        users.update({inter.user.id: setts})
    
    dl_menu = Dropdown_def_lang()
    tl_menu = Dropdown_tgt_lang()
    
    await inter.response.send_message("**Settings: **", ephemeral=True, components=[
        disnake.ui.Button(label="AT On", style=disnake.ButtonStyle.success, custom_id="at_on"),
        disnake.ui.Button(label="AT Off", style=disnake.ButtonStyle.danger, custom_id="at_off"),
        disnake.ui.Button(label="TL On", style=disnake.ButtonStyle.success, custom_id="tl_on"),
        disnake.ui.Button(label="TL Off", style=disnake.ButtonStyle.danger, custom_id="tl_off"),
        dl_menu, tl_menu
        ])
    
    # await inter.response.send_message("**Transliterate: **", ephemeral=True, components=[
    #     disnake.ui.Button(label="On", style=disnake.ButtonStyle.success, custom_id="tl_on"),
    #     disnake.ui.Button(label="Off", style=disnake.ButtonStyle.danger, custom_id="tl_off")
    #     ])
    
    # languages = list("English", "Spanish", "French", "Italian", "German", "Korean", "Japanese", "Mandarin")
    
    # await inter.response.send_message("**Default Language: **", ephemeral=True, components=[
    #     disnake.ui.StringSelect(placeholder="What language do you want to translate?", options=languages, custom_id="dl")])
                                     
    # await inter.response.send_message("**Target Language: **", ephemeral=True, components=[
    #     disnake.ui.StringSelect(placeholder="What's your native language?", options=languages, custom_id="tl")])

@bot.slash_command(description="Toggle Auto-Translate Globally")
async def toggle_at_global(inter):
    global autotranslate
    autotranslate = not autotranslate
    if autotranslate:
        await inter.response.send_message("Auto-translate is now on")
    else:
        await inter.response.send_message("Auto-translate is now off")

@bot.slash_command(description="Toggle Auto-Translate")
async def toggle_at(inter):
    users[inter.user] = not users.get(inter.user, False)
    if users[inter.user]:
        await inter.response.send_message("Auto-translate is now on")
    else:
        await inter.response.send_message("Auto-translate is now off")

@bot.slash_command(description="Toggle Romanize")
async def toggle_ro(inter):
    global romanize
    romanize = not romanize
    if romanize:
        await inter.response.send_message("Auto-romanization is now on")
    else:
        await inter.response.send_message("Auto-romanization is now off")

@bot.slash_command(description="Set target language")
async def set_target_lang(inter, language):
    global targetLang
    targetLang = language
    await inter.response.send_message("Target language has been set to " + language)     

@bot.slash_command(description="Generate Image")
async def generate_image(inter, prompt):
    await inter.response.defer()
    result = gpt.draw(prompt)
    await inter.followup.send(result)

################### Database #################################

async def saveChat(guild, question):
    try:
        connection = mysql.connector.connect(host="localhost",
                                             database="gpt_bot",
                                             user="root",
                                             password="root")
        mySql_Create_Table_Query = """CREATE TABLE DB_""" + str(guild) + """ (
        Id int(11) NOT NULL AUTO_INCREMENT,
        User varchar(250) NOT NULL,
        Message varchar(5000) NOT NULL,
        PRIMARY KEY (Id)) """

        cursor = connection.cursor()
        result = cursor.execute(mySql_Create_Table_Query)
        print("Table created")

    except mysql.connector.Error as error:
        print("Failed to create table: {}".format(error))

    finally:
        if connection.is_connected():
            table = "DB_" + str(guild)
            mySql_Insert_Row_Query = "INSERT INTO " + table + " (question) VALUES (%s)"
            message = {"role": "user", "content": question}
            mySql_Insert_Row_values = (message)
            cursor.execute(mySql_Insert_Row_Query, mySql_Insert_Row_values)

            

            print("question stored in db")

            cursor.close()

            connection.close()

####################################################


bot.run(credentials.disc_token)
