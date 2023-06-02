import disnake
import discord

from disnake.ext import commands

bot = commands.Bot(
    command_prefix="!",
)
    
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')


@bot.slash_command(description="Responds with 'World'")
async def hello(inter):
    await inter.response.send_message("World")

bot.run('MTExNDI0OTY1NDc5MjYyNjI3Nw.GI0y-I.Fu1t-Z2Y7MJArKCsHKSHRqrsXpMuLZnOyiagac')
