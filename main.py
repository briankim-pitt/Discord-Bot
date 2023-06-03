import asyncio
import disnake
import discord
import credentials
import gpt


from disnake.ext import commands

users = {}

#settings
autotranslate = False
romanize = False
targetLang = "English"

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
            response = gpt.ask(guild, text)
            await message.channel.send(response)
    else:
        if romanize:
            response = gpt.romanize(message.content)
            await message.channel.send("Romanized: ||" + response + "||")

        if users.get(message.author, False):
            global targetLang
            response = gpt.translate(message.content, targetLang)
            await message.channel.send("Translated: ||" + response + "||")
        

@bot.slash_command(description="Responds with 'World'")
async def hello(inter):
    await inter.response.send_message("World")

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


@bot.command(description="Ask GPT")
async def ask(ctx, arg):
    await ctx.channel.send("hi")
    response = gpt.ask(arg)
    await ctx.channel.send(response)

@bot.command(description="Say Hi")
async def hi(ctx: commands.Context):
    print("hello")
    await ctx.send('hello')
bot.run(credentials.disc_token)
