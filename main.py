import disnake
import discord

from disnake.ext import commands

bot = commands.Bot(

)

@bot.slash_command(description="Responds with 'World'")
async def hello(inter):
    await inter.response.send_message("World")