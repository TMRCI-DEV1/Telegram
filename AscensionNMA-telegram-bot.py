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

# Start command with inline buttons
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Help", callback_data='help'),
         InlineKeyboardButton("Quote", callback_data='quote')],
        [InlineKeyboardButton("Weather", callback_data='weather')]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    msg = await update.message.reply_text(
        "Greetings peasant! I'm your new bot overlord. Choose one of the options below:",
        reply_markup=markup
    )
    asyncio.create_task(schedule_message_deletion(update.message, msg))

# Callback for inline buttons
async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    logger.info(f"Button pressed with callback data: {query.data}")  # Log button press for debugging
    await query.answer()

    if query.data == 'help':
        await help_command(query, context)
    elif query.data == 'quote':
        await quote(query, context)
    elif query.data == 'weather':
        await request_zip_code(query, context)

# Help command
async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Get help\n"
        "/quote - Get a random quote\n"
        "Click 'Weather' to get the current weather and time by entering your zip code."
    )
    keyboard = [[InlineKeyboardButton("Back", callback_data='start')]]
    markup = InlineKeyboardMarkup(keyboard)
    msg = await update.callback_query.message.reply_text(help_text, reply_markup=markup)
    asyncio.create_task(schedule_message_deletion(update.callback_query.message, msg))

# Quote command
async def quote(update: Update, context: CallbackContext):
    random_quote = random.choice(QUOTES)
    keyboard = [[InlineKeyboardButton("Back", callback_data='start')]]
    markup = InlineKeyboardMarkup(keyboard)
    msg = await update.callback_query.message.reply_text(random_quote, reply_markup=markup)
    asyncio.create_task(schedule_message_deletion(update.callback_query.message, msg))

# Handle the weather button click and prompt for zip code
async def request_zip_code(update: Update, context: CallbackContext):
    logger.info("Weather button clicked. Asking for zip code.")  # Log weather button press
    msg = await update.callback_query.message.reply_text("Please enter your zip code to get the current weather:")
    asyncio.create_task(schedule_message_deletion(update.callback_query.message, msg))
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

            msg = await update.message.reply_text(
                f"Weather in {city_name}, {country} (Lat: {lat}, Lon: {lon}):\n"
                f"Temperature: {temperature}°F\n"
                f"Description: {weather_description}\n\n"
                f"Current Time: {current_time}"
            )
        else:
            msg = await update.message.reply_text("Sorry, I couldn't get the time for your location.")
    else:
        msg = await update.message.reply_text("Invalid zip code. Please try again.")

    # Schedule deletion of both the user input and the bot's response
    asyncio.create_task(schedule_message_deletion(update.message, msg))

    return ConversationHandler.END

# Schedule message deletion for both user and bot messages
async def schedule_message_deletion(user_message, bot_message):
    await asyncio.sleep(10)  # Wait for 10 seconds before deleting
    try:
        if user_message:
            await user_message.delete()  # Delete the user's message
        if bot_message:
            await bot_message.delete()  # Delete the bot's response
    except Exception as e:
        logger.warning(f"Failed to delete message: {e}")

# Main function to set up the bot
def main():
    application = Application.builder().token('7823996299:AAHOsTyetmM50ZggjK2h_NWUR-Vm0gtolvY').build()

    # Register the start command handler
    application.add_handler(CommandHandler('start', start))

    # Callback handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))

    # Conversation handler for weather request
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(request_zip_code, pattern='weather')],
        states={GET_ZIP_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weather_time)]},
        fallbacks=[]
    )
    application.add_handler(conv_handler)

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
