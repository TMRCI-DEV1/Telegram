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
    CallbackQueryHandler,
    CallbackContext,
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
    "If ifs and buts were candies and nuts, we'd all have a Merry Fucking Christmas! - Anonymous (aka Jimmy Crypto)"
]

# Define states for the conversation handler
GET_ZIP_CODE = range(1)

# Start command with inline buttons
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Help", callback_data='help'),
            InlineKeyboardButton("Quote", callback_data='quote')
        ],
        [
            InlineKeyboardButton("Weather", callback_data='weather')
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    msg = await update.message.reply_text(
        "Greetings peasant! I'm your new bot overlord. Choose one of the options below:",
        reply_markup=markup
    )
    asyncio.create_task(schedule_message_deletion(update.message, msg))
    logger.info("Start command processed.")

# Callback for inline buttons
async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    logger.info(f"Button pressed with callback data: {data}")  # Log button press for debugging
    await query.answer()  # Answer the callback to stop Telegram from showing "loading..."

    if data == 'help':
        await help_command(query, context)
    elif data == 'quote':
        await quote_command(query, context)
    elif data == 'weather':
        logger.info("Weather button pressed. Transitioning to zip code request.")
        await request_zip_code(query, context)  # Fix: added handling for the weather button
    elif data == 'start':
        await start_callback(query, context)
    else:
        logger.warning(f"Unknown callback data: {data}")

# Help command
async def help_command(query: Update, context: CallbackContext):
    logger.info("Help command triggered")
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Get help\n"
        "/quote - Get a random quote\n"
        "Click 'Weather' to get the current weather and time by entering your zip code."
    )
    keyboard = [[InlineKeyboardButton("Back", callback_data='start')]]
    markup = InlineKeyboardMarkup(keyboard)
    msg = await query.message.reply_text(help_text, reply_markup=markup)
    asyncio.create_task(schedule_message_deletion(query.message, msg))
    logger.info("Help command response sent.")

# Quote command
async def quote_command(query: Update, context: CallbackContext):
    logger.info("Quote command triggered")
    random_quote = random.choice(QUOTES)
    keyboard = [[InlineKeyboardButton("Back", callback_data='start')]]
    markup = InlineKeyboardMarkup(keyboard)
    msg = await query.message.reply_text(random_quote, reply_markup=markup)
    asyncio.create_task(schedule_message_deletion(query.message, msg))
    logger.info("Quote command response sent.")

# Start callback (from 'Back' button)
async def start_callback(query: Update, context: CallbackContext):
    logger.info("Back to start command triggered.")
    keyboard = [
        [
            InlineKeyboardButton("Help", callback_data='help'),
            InlineKeyboardButton("Quote", callback_data='quote')
        ],
        [
            InlineKeyboardButton("Weather", callback_data='weather')
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    msg = await query.message.reply_text(
        "Greetings peasant! I'm your new bot overlord. Choose one of the options below:",
        reply_markup=markup
    )
    asyncio.create_task(schedule_message_deletion(query.message, msg))
    logger.info("Back to start command processed.")

# Handle the weather button click and prompt for zip code
async def request_zip_code(query: Update, context: CallbackContext):
    logger.info("Weather button clicked. Asking for zip code.")
    msg = await query.message.reply_text("Please enter your zip code to get the current weather:")
    # Store the prompt message in user_data for deletion later (if desired)
    context.user_data['zip_code_prompt'] = msg
    asyncio.create_task(schedule_message_deletion(query.message, msg))
    return GET_ZIP_CODE  # Transition to GET_ZIP_CODE state

# Process the zip code and get the weather
async def get_weather_time(update: Update, context: CallbackContext):
    zip_code = update.message.text.strip()
    logger.info(f"Processing zip code: {zip_code}")
    full_zip_code = f"{zip_code},US"

    try:
        weather_params = {'zip': full_zip_code, 'appid': WEATHER_API_KEY, 'units': 'imperial'}
        weather_response = requests.get(WEATHER_API_URL, params=weather_params)

        if weather_response.status_code == 200:
            weather_data = weather_response.json()
            city_name = weather_data.get('name')
            country = weather_data['sys'].get('country')
            lat = weather_data['coord'].get('lat')
            lon = weather_data['coord'].get('lon')
            temperature = weather_data['main'].get('temp')
            weather_description = weather_data['weather'][0].get('description')

            weather_text = (
                f"Weather in {city_name}, {country} (Lat: {lat}, Lon: {lon}):\n"
                f"Temperature: {temperature}°F\n"
                f"Description: {weather_description}"
            )
            msg = await update.message.reply_text(weather_text)
        else:
            msg = await update.message.reply_text("Invalid zip code. Please try again.")
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
        msg = await update.message.reply_text("An error occurred while fetching the weather. Please try again.")

    asyncio.create_task(schedule_message_deletion(update.message, msg))

    return ConversationHandler.END  # End the conversation

# Schedule message deletion for multiple messages
async def schedule_message_deletion(*messages):
    await asyncio.sleep(10)
    for msg in messages:
        try:
            if msg:
                await msg.delete()
        except Exception as e:
            logger.warning(f"Failed to delete message: {e}")

# Error handler to catch and log exceptions
async def error_handler(update: object, context: CallbackContext):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

# Main function to set up the bot
def main():
    application = Application.builder().token('7823996299:AAHOsTyetmM50ZggjK2h_NWUR-Vm0gtolvY').build()

    # Register ConversationHandler for weather request
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(request_zip_code, pattern='^weather$')],
        states={
            GET_ZIP_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weather_time)]
        },
        fallbacks=[]
    )
    application.add_handler(conv_handler)

    # Register the start command handler
    application.add_handler(CommandHandler('start', start))

    # Callback handler for other inline buttons (help, quote, back to start)
    application.add_handler(CallbackQueryHandler(button_callback, pattern='^(help|quote|start)$'))

    # Register the error handler
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
