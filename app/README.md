A Discord bot for language learning with translation and flashcard features.

## Features

- Auto-translation of messages
- Romanization of text
- Flashcard creation from translations and DMs
- Interactive quiz system
- User profile management
- Language settings

## Commands

- `/profile` - Display user profile
- `/change_settings` - Change bot settings
- `/view_cards` - View your flashcards
- `/toggle_at` - Toggle auto-translate
- `/toggle_ro` - Toggle romanization
- `/set_target_lang` - Set target language
- `/create_card` - Create a flashcard (DM only)
- `/generate_image` - Generate an image

## Creating Flashcards in DMs

### Method 1: Simple Text Format
Send a message in this format:
```
Question | Answer
```

**Example:**
```
What is the capital of France? | Paris
```

### Method 2: Slash Command
Use the `/create_card` command in DMs:
```
/create_card question:What is the capital of France? answer:Paris
```

## Usage

1. Set your default and target languages using `/change_settings`
2. Enable auto-translate to automatically translate messages
3. Save translations to create flashcards OR create flashcards directly in DMs
4. Use the quiz feature to test your knowledge

## Setup

- Need openai and discord api developer keys in `.env` to run

Run with:

``` python main.py ```

Installing external libraries:

``` pip install asyncio, disnake, openai, requests, python-dotenv ```
