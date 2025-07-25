import asyncio
import disnake
import os
from dotenv import load_dotenv
import gpt
import flashcards
import settings
import database
from disnake.ext import commands

############# global settings #############
autotranslate = False
romanize = False
targetLang = "English"

languages = [
    disnake.SelectOption(label="English", emoji="🇬🇧"), 
    disnake.SelectOption(label="Spanish", emoji="🇪🇸"),
    disnake.SelectOption(label="French", emoji="🇫🇷"),
    disnake.SelectOption(label="Italian", emoji="🇮🇹"),
    disnake.SelectOption(label="German", emoji="🇩🇪"),
    disnake.SelectOption(label="Korean", emoji="🇰🇷"),
    disnake.SelectOption(label="Japanese", emoji="🇯🇵"),
    disnake.SelectOption(label="Mandarin", emoji="🇨🇳"),
]               

# Database instance for persistent storage
db = database.db

def get_guild_id(inter):
    """Helper function to safely get guild ID, returns 0 for DMs"""
    return inter.guild.id if inter.guild else 0

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

    # Handle DM messages for flashcard creation
    if isinstance(message.channel, disnake.DMChannel):
        # Check if message contains flashcard format (question | answer)
        if " | " in message.content:
            parts = message.content.split(" | ", 1)
            if len(parts) == 2:
                question = parts[0].strip()
                answer = parts[1].strip()
                
                # Create flashcard in database
                db.add_flashcard(message.author.id, question, answer)
                card_count = db.get_flashcard_count(message.author.id)
                
                # Send confirmation with buttons
                embed = disnake.Embed(
                    title="Flashcard Created!",
                    description=f"You now have {card_count} flashcards",
                    color=0x00FF00
                )
                embed.add_field(name="Question", value=question, inline=False)
                embed.add_field(name="Answer", value=answer, inline=False)
                
                quiz_btn = disnake.ui.Button(style=disnake.ButtonStyle.primary, 
                                           label="Start Quiz", emoji="🎮", 
                                           custom_id="start_quiz")
                view_btn = disnake.ui.Button(style=disnake.ButtonStyle.secondary, 
                                           label="View All Cards", emoji="📚", 
                                           custom_id="view_all_dm")
                
                await message.reply(embed=embed, components=[quiz_btn, view_btn])
                return
        
        # If not flashcard format, provide help
        help_embed = disnake.Embed(
            title="Create Flashcards in DM",
            description="To create a flashcard, use this format:\n`Question | Answer`",
            color=0x00FFFF
        )
        help_embed.add_field(
            name="Example", 
            value="`What is the capital of France? | Paris`", 
            inline=False
        )
        help_embed.add_field(
            name="Tips", 
            value="• Use ` | ` (space-pipe-space) to separate question and answer\n• You can create multiple cards by sending multiple messages", 
            inline=False
        )
        
        await message.reply(embed=help_embed)
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
        setts = database.DatabaseSettings(message.guild.id, message.author.id, db)
        
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
            
            # Use both default and target languages for translation
            def_lang = setts.get_def_lang()
            tgt_lang = setts.get_tgt_lang()
            # Only translate if both languages are set and different
            if def_lang and tgt_lang and def_lang != tgt_lang:
                response = gpt.translate(message.content, tgt_lang)
                await message.reply("Translated: ||" + response + "||", components=[button])
            else:
                # Skip translation if languages are not properly set
                await message.reply("Translation skipped: Please set different source and target languages.", components=[button])

@bot.listen("on_dropdown")
async def help_dropdown(inter: disnake.MessageInteraction):
    if inter.component.custom_id not in ["dl", "tl"]:
        return

    user = inter.author 
    setts = database.DatabaseSettings(get_guild_id(inter), user.id, db)

    if inter.component.custom_id == "dl":
        setts.set_def_lang(inter.values[0])
        await inter.response.send_message(f"Default language set to {inter.values[0]}", ephemeral=True)
    if inter.component.custom_id == "tl":
        setts.set_tgt_lang(inter.values[0])
        await inter.response.send_message(f"Target language set to {inter.values[0]}", ephemeral=True)

@bot.listen("on_button_click")
async def help_listener(inter: disnake.MessageInteraction):
    if inter.component.custom_id not in ["save", "make_card", "ask", "at_on", "at_off", "tl_on", "tl_off", "start_quiz", "next_card", "show_answer", "view_all_dm"]:
        return
    
    user = inter.author 
    setts = database.DatabaseSettings(get_guild_id(inter), user.id, db)
    
    if inter.component.custom_id in ["at_on", "at_off", "tl_on", "tl_off"]:
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
        # Get the message content from the embed
        embed = inter.message.embeds[0]
        original = embed.fields[0].value
        translation = embed.fields[1].value
        
        # Create a new card in database
        db.add_flashcard(user.id, original, translation)
        card_count = db.get_flashcard_count(user.id)
        
        # Confirm card creation
        await inter.response.send_message("Flashcard created successfully!", ephemeral=True)
        
        # Offer to start a quiz
        quiz_btn = disnake.ui.Button(style=disnake.ButtonStyle.primary, label="Start Quiz", 
                                    emoji="🎮", custom_id="start_quiz")
        await user.send(f"You now have {card_count} flashcards. Would you like to test your knowledge?", 
                        components=[quiz_btn])
        
    if inter.component.custom_id == "start_quiz":
        # Check if user has cards
        user_cards_data = db.get_user_flashcards(user.id)
        if not user_cards_data:
            await inter.response.send_message("You don't have any flashcards yet. Save some translations first!", ephemeral=True)
            return
        
        # Initialize quiz state
        setts.current_card_index = 0
        setts.quiz_mode = True
        
        # Show first card
        current_card = user_cards_data[0]
        
        show_answer_btn = disnake.ui.Button(style=disnake.ButtonStyle.secondary, 
                                           label="Show Answer", emoji="👀", 
                                           custom_id="show_answer")
        
        await inter.response.send_message("Quiz started! Here's your first card:", ephemeral=True)
        await user.send(f"**Question:** {current_card['question']}", components=[show_answer_btn])
    
    if inter.component.custom_id == "show_answer":
        if not setts.quiz_mode:
            await inter.response.send_message("No active quiz session. Start a quiz first!", ephemeral=True)
            return
        
        user_cards_data = db.get_user_flashcards(user.id)
        current_card = user_cards_data[setts.current_card_index]
        next_btn = disnake.ui.Button(style=disnake.ButtonStyle.primary, 
                                    label="Next Card", emoji="➡️", 
                                    custom_id="next_card")
        
        await inter.response.send_message(f"**Answer:** {current_card['answer']}", ephemeral=True)
        
        # If there are more cards, show next button
        if setts.current_card_index < len(user_cards_data) - 1:
            await user.send("Ready for the next card?", components=[next_btn])
        else:
            setts.quiz_mode = False
            quiz_btn = disnake.ui.Button(style=disnake.ButtonStyle.primary, 
                                        label="Restart Quiz", emoji="🔄", 
                                        custom_id="start_quiz")
            await user.send("Quiz completed! You've reviewed all your flashcards.", components=[quiz_btn])
    
    if inter.component.custom_id == "next_card":
        if not setts.quiz_mode:
            await inter.response.send_message("No active quiz session. Start a quiz first!", ephemeral=True)
            return
        
        # Move to next card
        setts.current_card_index += 1
        
        user_cards_data = db.get_user_flashcards(user.id)
        
        # Check if we've reached the end
        if setts.current_card_index >= len(user_cards_data):
            setts.quiz_mode = False
            quiz_btn = disnake.ui.Button(style=disnake.ButtonStyle.primary, 
                                        label="Restart Quiz", emoji="🔄", 
                                        custom_id="start_quiz")
            await inter.response.send_message("Quiz completed! You've reviewed all your flashcards.", ephemeral=True)
            await user.send("Quiz completed! You've reviewed all your flashcards.", components=[quiz_btn])
            return
        
        # Show next card
        current_card = user_cards_data[setts.current_card_index]
        show_answer_btn = disnake.ui.Button(style=disnake.ButtonStyle.secondary, 
                                           label="Show Answer", emoji="👀", 
                                           custom_id="show_answer")
        
        await inter.response.send_message("Here's your next card:", ephemeral=True)
        await user.send(f"**Question:** {current_card['question']}", components=[show_answer_btn])
        
    if inter.component.custom_id == "view_all_dm":
        # Check if user has cards
        user_cards_data = db.get_user_flashcards(user.id)
        if not user_cards_data:
            await inter.response.send_message("You don't have any flashcards yet. Create some first!", ephemeral=True)
            return
        
        # Create embed showing all cards
        embed = disnake.Embed(
            title="Your Flashcards",
            description=f"You have {len(user_cards_data)} flashcards",
            color=0x00FFFF
        )
        
        for i, card in enumerate(user_cards_data, 1):
            embed.add_field(
                name=f"Card {i}",
                value=f"**Q:** {card['question']}\n**A:** {card['answer']}",
                inline=False
            )
        
        quiz_btn = disnake.ui.Button(style=disnake.ButtonStyle.primary, 
                                    label="Start Quiz", emoji="🎮", 
                                    custom_id="start_quiz")
        
        await inter.response.send_message(embed=embed, components=[quiz_btn], ephemeral=True)
    
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
        await user.send(text, embed=embed, components=[card_btn, ask_btn]) 

def extract_text(input_string):
    start_marker = "Translated: ||"
    end_marker = "||"
    start_index = input_string.find(start_marker)
    end_index = input_string.find(end_marker, start_index + len(start_marker))

    if start_index != -1 and end_index != -1:
        extracted_text = input_string[start_index + len(start_marker):end_index]
        return extracted_text.strip()
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
        setts = database.DatabaseSettings(get_guild_id(inter), user.id, db)
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
        setts = database.DatabaseSettings(get_guild_id(inter), user.id, db)
        setts.set_tgt_lang(self.values[0])
        await inter.response.send_message("Target language set to " + self.values[0], ephemeral=True)

class DropDownView(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(Dropdown_def_lang())

########## SLASH COMMANDS #############

@bot.slash_command(description="View your flashcards")
async def view_cards(inter):
    user_id = inter.user.id
    
    user_cards_data = db.get_user_flashcards(user_id)
    if not user_cards_data:
        await inter.response.send_message("You don't have any flashcards yet. Save some translations first!")
        return
    
    embed = disnake.Embed(
        title="Your Flashcards",
        description=f"You have {len(user_cards_data)} flashcards",
        color=0x00FFFF
    )
    
    for i, card in enumerate(user_cards_data, 1):
        embed.add_field(
            name=f"Card {i}",
            value=f"**Q:** {card['question']}\n**A:** {card['answer']}",
            inline=False
        )
    
    quiz_btn = disnake.ui.Button(style=disnake.ButtonStyle.primary, label="Start Quiz", 
                                emoji="🎮", custom_id="start_quiz")
    
    await inter.response.send_message(embed=embed, components=[quiz_btn])

@bot.slash_command(description="Display user profile")
async def profile(inter):
    setts = database.DatabaseSettings(get_guild_id(inter), inter.user.id, db)
    at = setts.get_auto_t()
    tr = setts.get_translit()
    dl = setts.get_def_lang()
    tl = setts.get_tgt_lang()
    
    embed = disnake.Embed(
        title="",
        description="",
        color=0x00FFFF,
        type="rich"            
    )
    
    embed.set_author(
        name=inter.author.name + "'s profile",
        icon_url=inter.author.avatar.url
    )
    
    value = "On" if at else "Off"
    embed.add_field(name="Auto-Translate", value=value, inline=True)
    
    value = "On" if tr else "Off"
    embed.add_field(name="Transliterate", value=value, inline=True)
    
    embed.add_field(name="Default Language", value=dl or "Not set", inline=True)
    embed.add_field(name="Target Language", value=tl or "Not set", inline=True)
    
    await inter.response.send_message(embed=embed)
     
@bot.slash_command(description="Change settings")
async def change_settings(inter):  
    dl_menu = Dropdown_def_lang()
    tl_menu = Dropdown_tgt_lang()
    
    await inter.response.send_message("**Settings: **", ephemeral=True, components=[
        disnake.ui.Button(label="AT On", style=disnake.ButtonStyle.success, custom_id="at_on"),
        disnake.ui.Button(label="AT Off", style=disnake.ButtonStyle.danger, custom_id="at_off"),
        disnake.ui.Button(label="TL On", style=disnake.ButtonStyle.success, custom_id="tl_on"),
        disnake.ui.Button(label="TL Off", style=disnake.ButtonStyle.danger, custom_id="tl_off"),
        dl_menu, tl_menu
    ])

@bot.slash_command(description="Toggle Auto-Translate Globally")
async def toggle_at_global(inter):
    global autotranslate
    autotranslate = not autotranslate
    await inter.response.send_message("Auto-translate is now on" if autotranslate else "Auto-translate is now off")

@bot.slash_command(description="Toggle Auto-Translate")
async def toggle_at(inter):
    setts = database.DatabaseSettings(get_guild_id(inter), inter.user.id, db)
    setts.set_auto_t(not setts.get_auto_t())
    await inter.response.send_message("Auto-translate is now on" if setts.get_auto_t() else "Auto-translate is now off")

@bot.slash_command(description="Toggle Romanize")
async def toggle_ro(inter):
    global romanize
    romanize = not romanize
    await inter.response.send_message("Auto-romanization is now on" if romanize else "Auto-romanization is now off")

@bot.slash_command(description="Set target language")
async def set_target_lang(inter, language):
    global targetLang
    targetLang = language
    await inter.response.send_message("Target language has been set to " + language)     

@bot.slash_command(description="Create a flashcard (use in DM)")
async def create_card(inter, question: str, answer: str):
    # Check if this is being used in DM
    if not isinstance(inter.channel, disnake.DMChannel):
        await inter.response.send_message("This command can only be used in DMs with the bot!", ephemeral=True)
        return
    
    user_id = inter.user.id
    
    # Create flashcard in database
    db.add_flashcard(user_id, question, answer)
    card_count = db.get_flashcard_count(user_id)
    
    # Send confirmation with buttons
    embed = disnake.Embed(
        title="Flashcard Created!",
        description=f"You now have {card_count} flashcards",
        color=0x00FF00
    )
    embed.add_field(name="Question", value=question, inline=False)
    embed.add_field(name="Answer", value=answer, inline=False)
    
    quiz_btn = disnake.ui.Button(style=disnake.ButtonStyle.primary, 
                               label="Start Quiz", emoji="🎮", 
                               custom_id="start_quiz")
    view_btn = disnake.ui.Button(style=disnake.ButtonStyle.secondary, 
                               label="View All Cards", emoji="📚", 
                               custom_id="view_all_dm")
    
    await inter.response.send_message(embed=embed, components=[quiz_btn, view_btn])

@bot.slash_command(description="Generate Image")
async def generate_image(inter, prompt):
    await inter.response.defer()
    result = gpt.draw(prompt)
    await inter.followup.send(result)
        

load_dotenv()
disc_token = os.getenv("disc_token")

bot.run(disc_token)
bot.run(disc_token)
