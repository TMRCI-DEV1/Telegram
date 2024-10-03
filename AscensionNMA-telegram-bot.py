import logging
import requests
import random
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler, CallbackContext
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

# Start command with persistent inline buttons
async def start(update: Update, context: CallbackContext):
    inline_keyboard = [
        [InlineKeyboardButton("Help", callback_data='help')],
        [InlineKeyboardButton("Quote", callback_data='quote')],
        [InlineKeyboardButton("Weather", callback_data='weather')]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard)
    msg = await update.message.reply_text(
        "Greetings peasant! I'm your new bot overlord. Choose one of the options below:",
        reply_markup=markup
    )
    # Schedule deletion of command messages
    asyncio.create_task(schedule_message_deletion(update.message, msg))

# Callback query handler for inline buttons
async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # Acknowledge the button press

    if query.data == 'help':
        await help_command(query.message, context)
    elif query.data == 'quote':
        await quote(query.message, context)
    elif query.data == 'weather':
        await request_zip_code(query.message, context)

# Help command
async def help_command(message: Update, context: CallbackContext):
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Get help\n"
        "/quote - Get a random quote\n"
        "Click 'Weather' to get the current weather and time by entering your zip code."
    )
    msg = await message.reply_text(help_text)
    asyncio.create_task(schedule_message_deletion(message, msg))

# Quote command
async def quote(message: Update, context: CallbackContext):
    random_quote = random.choice(QUOTES)
    msg = await message.reply_text(random_quote)
    asyncio.create_task(schedule_message_deletion(message, msg))

# Handle the weather button click and prompt for zip code
async def request_zip_code(message: Update, context: CallbackContext):
    msg = await message.reply_text("Please enter your zip code to get the current weather:")
    asyncio.create_task(schedule_message_deletion(message, msg))
    return GET_ZIP_CODE

# Process the zip code and get the weather
async def get_weather_time(update: Update, context: CallbackContext):
    zip_code = update.message.text.strip()
    full_zip_code = f"{zip_code},US"

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

        time_response = requests.get(f"http://worldtimeapi.org/api/timezone/Etc/GMT")
        if time_response.status_code == 200:
            time_data = time_response.json()
            current_time = time_data['datetime']

            weather_msg = await update.message.reply_text(
                f"Weather in {city_name}, {country} (Lat: {lat}, Lon: {lon}):\n"
                f"Temperature: {temperature}°F\n"
                f"Description: {weather_description}\n\n"
                f"Current Time: {current_time}"
            )
        else:
            weather_msg = await update.message.reply_text("Sorry, I couldn't get the time for your location.")
    else:
        weather_msg = await update.message.reply_text("Invalid zip code. Please try again.")
    
    # Schedule deletion of both user message and bot's weather response
    asyncio.create_task(schedule_message_deletion(update.message, weather_msg))
    return ConversationHandler.END

# Schedule message deletion for both user and bot messages
async def schedule_message_deletion(user_message, bot_message):
    await asyncio.sleep(10)  # Wait for 10 seconds before deleting
    try:
        await user_message.delete()
        await bot_message.delete()
    except Exception as e:
        logger.warning(f"Failed to delete message: {e}")

# Handle regular messages
async def handle_regular_message(update: Update, context: CallbackContext):
    logger.info(f"Received a regular message: {update.message.text}")
    text = update.message.text.strip()
    if text.startswith("/"):
        msg = await update.message.reply_text(f"Received: {text}")
        asyncio.create_task(schedule_message_deletion(update.message, msg))
    else:
        logger.info("Non-command message received, ignoring.")

def main():
    application = Application.builder().token('7823996299:AAHOsTyetmM50ZggjK2h_NWUR-Vm0gtolvY').build()

    # Register the start command handler
    application.add_handler(CommandHandler('start', start))

    # Register button callbacks
    application.add_handler(CallbackQueryHandler(button_callback))

    # Conversation handler for weather request
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^(Weather)$'), request_zip_code)],
        states={GET_ZIP_CODE: [MessageHandler(filters.TEXT, get_weather_time)]},
        fallbacks=[]
    )
    application.add_handler(conv_handler)

    # Register handler for regular messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_regular_message))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
