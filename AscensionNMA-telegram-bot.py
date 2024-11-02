import logging
import requests
import random
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler,
)
import asyncio

# Define API keys and base URLs
WEATHER_API_KEY = "a10a17233a99d6e36c3d99f9493fddf5"
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# List of quotes
QUOTES = [
    "The only limit to our realization of tomorrow is our doubts of today. - Franklin D. Roosevelt",
    "Do not wait to strike till the iron is hot; but make it hot by striking. - William Butler Yeats",
    "Whether you think you can, or you think you can't--you're right. - Henry Ford",
    "The best way to predict the future is to invent it. - Alan Kay",
    "If ifs and buts were candies and nuts, we'd all have a Merry Fucking Christmas! - Anonymous (aka Jimmy Crypto)",
    "You gotta read!!! - Tmeka",
    "Litigation is the ONLY way! - BJW and Mansa",
    "But but but muh 5 star Passport and much beneficiary signature! Murica! - EVERY sovereign citizen ever",
    "The most manly thing you can do is to fuck a tranny. - Freedom Olah",
    "Liberty, when it begins to take root, is a plant of rapid growth. - George Washington"
]

# Define states for the conversation handler
GET_ZIP_CODE = range(1)

# Start command with inline keyboard
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Help", callback_data='help'),
            InlineKeyboardButton("Quote", callback_data='quote'),
        ],
        [InlineKeyboardButton("Weather", callback_data='weather')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = await update.message.reply_text(
        "Greetings peasant! I'm your new bot overlord. Choose one of the options below:",
        reply_markup=reply_markup
    )
    asyncio.create_task(schedule_message_deletion(update.message, msg))

# Help command with inline keyboard
async def help_command(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Help", callback_data='help'),
            InlineKeyboardButton("Quote", callback_data='quote'),
        ],
        [InlineKeyboardButton("Weather", callback_data='weather')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Get help\n"
        "/quote - Get a random quote\n"
        "Click 'Weather' to get the current weather and time by entering your zip code."
    )
    msg = await update.callback_query.message.reply_text(help_text, reply_markup=reply_markup)
    asyncio.create_task(schedule_message_deletion(update.callback_query.message, msg))

# Quote command with inline keyboard
async def quote(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Help", callback_data='help'),
            InlineKeyboardButton("Quote", callback_data='quote'),
        ],
        [InlineKeyboardButton("Weather", callback_data='weather')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    random_quote = random.choice(QUOTES)
    
    # Send the quote
    msg = await update.callback_query.message.reply_text(random_quote, reply_markup=reply_markup)
    
    # Schedule deletion for both the old message (with the buttons) and the new quote message
    asyncio.create_task(schedule_message_deletion(update.callback_query.message, msg))

# Handle the weather button click and prompt for zip code
async def request_zip_code(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = [
        [
            InlineKeyboardButton("Help", callback_data='help'),
            InlineKeyboardButton("Quote", callback_data='quote'),
        ],
        [InlineKeyboardButton("Weather", callback_data='weather')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = await query.message.reply_text("Please enter your zip code to get the current weather:", reply_markup=reply_markup)
    asyncio.create_task(schedule_message_deletion(query.message, msg))
    return GET_ZIP_CODE

# Process the zip code and get the weather
async def get_weather_time(update: Update, context: CallbackContext):
    zip_code = update.message.text.strip()
    full_zip_code = f"{zip_code},US"

    weather_params = {'zip': full_zip_code, 'appid': WEATHER_API_KEY, 'units': 'imperial'}
    weather_response = requests.get(WEATHER_API_URL, params=weather_params)

    keyboard = [
        [
            InlineKeyboardButton("Help", callback_data='help'),
            InlineKeyboardButton("Quote", callback_data='quote'),
        ],
        [InlineKeyboardButton("Weather", callback_data='weather')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if weather_response.status_code == 200:
        weather_data = weather_response.json()
        city_name = weather_data.get('name')
        country = weather_data['sys'].get('country')
        lat = weather_data['coord'].get('lat')
        lon = weather_data['coord'].get('lon')
        temperature = weather_data['main'].get('temp')
        weather_description = weather_data['weather'][0].get('description')

        time_response = requests.get(f"http://worldtimeapi.org/api/timezone/Etc/GMT")
        if time_response.status_code == 200:
            time_data = time_response.json()
            current_time = time_data['datetime']

            msg = await update.message.reply_text(
                f"Weather in {city_name}, {country} (Lat: {lat}, Lon: {lon}):\n"
                f"Temperature: {temperature}°F\n"
                f"Description: {weather_description}\n\n"
                f"Current Time: {current_time}",
                reply_markup=reply_markup
            )
        else:
            msg = await update.message.reply_text("Sorry, I couldn't get the time for your location.", reply_markup=reply_markup)
    else:
        msg = await update.message.reply_text("Invalid zip code. Please try again.", reply_markup=reply_markup)

    # Schedule deletion of both the user input and the bot's response
    asyncio.create_task(schedule_message_deletion(update.message, msg))

    return ConversationHandler.END

# Schedule message deletion for both user and bot messages
async def schedule_message_deletion(*messages):
    await asyncio.sleep(15)  # Wait for 15 seconds before deleting
    for msg in messages:
        try:
            if msg:
                await msg.delete()
        except Exception as e:
            logger.warning(f"Failed to delete message: {e}")

# Handle button presses
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == 'help':
        await help_command(update, context)
    elif query.data == 'quote':
        await quote(update, context)
    elif query.data == 'weather':
        await request_zip_code(update, context)

    await query.answer()

# Handle regular messages, ignoring non-command posts
async def handle_regular_message(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if not text.startswith("/"):  # Ignore non-command posts
        return

    logger.info(f"Received a command: {update.message.text}")

    if text.startswith("/start"):
        await start(update, context)
    elif text.startswith("/help"):
        await help_command(update, context)
    elif text.startswith("/quote"):
        await quote(update, context)

def main():
    application = Application.builder().token('7823996299:AAHOsTyetmM50ZggjK2h_NWUR-Vm0gtolvY').build()

    # Register the start command handler
    application.add_handler(CommandHandler('start', start))

    # Register the help command handler
    application.add_handler(CommandHandler('help', help_command))

    # Register the quote command handler
    application.add_handler(CommandHandler('quote', quote))

    # Conversation handler for weather request
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(request_zip_code, pattern='^weather$')],
        states={GET_ZIP_CODE: [MessageHandler(filters.TEXT, get_weather_time)]},
        fallbacks=[]
    )
    application.add_handler(conv_handler)

    # Register handler for regular messages, ignoring non-command posts
    application.add_handler(MessageHandler(filters.TEXT, handle_regular_message))

    # Register the button handler
    application.add_handler(CallbackQueryHandler(button))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
