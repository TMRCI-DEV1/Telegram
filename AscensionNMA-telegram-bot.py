import logging
import requests
import random
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext

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

# Start command with persistent reply keyboard
async def start(update: Update, context: CallbackContext):
    # Define the buttons for the keyboard
    reply_keyboard = [['/help', '/quote', 'Weather']]
    
    # Set up the keyboard markup without one_time_keyboard, so it remains visible
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Greetings peasant! I'm your new bot overlord. Choose one of the options below:",
        reply_markup=markup
    )

# Help command
async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Get help\n"
        "/quote - Get a random quote\n"
        "Click 'Weather' to get the current weather and time by entering your zip code."
    )
    await update.message.reply_text(help_text)

# Quote command
async def quote(update: Update, context: CallbackContext):
    random_quote = random.choice(QUOTES)
    await update.message.reply_text(random_quote)

# Handle the weather button click and prompt for zip code
async def request_zip_code(update: Update, context: CallbackContext):
    await update.message.reply_text("Please enter your zip code to get the current weather:")
    return GET_ZIP_CODE  # This will wait for the user to enter the zip code

# Process the zip code and get the weather
async def get_weather_time(update: Update, context: CallbackContext):
    zip_code = update.message.text.strip()
    
    # Ensure that the country code is included with the zip code (default to US)
    full_zip_code = f"{zip_code},US"

    # Get weather data from OpenWeatherMap
    weather_params = {
        'zip': full_zip_code,
        'appid': WEATHER_API_KEY,
        'units': 'imperial'  # Use 'metric' for Celsius, 'imperial' for Fahrenheit
    }
    
    weather_response = requests.get(WEATHER_API_URL, params=weather_params)
    
    if weather_response.status_code == 200:
        weather_data = weather_response.json()
        
        # Extract relevant information
        city_name = weather_data.get('name')
        country = weather_data['sys'].get('country')
        lat = weather_data['coord'].get('lat')
        lon = weather_data['coord'].get('lon')
        temperature = weather_data['main'].get('temp')
        weather_description = weather_data['weather'][0].get('description')

        # Get time data from World Time API using a generic GMT time for simplicity
        time_response = requests.get(f"http://worldtimeapi.org/api/timezone/Etc/GMT")
        
        if time_response.status_code == 200:
            time_data = time_response.json()
            current_time = time_data['datetime']

            # Send weather and time info to the user
            await update.message.reply_text(
                f"Weather in {city_name}, {country} (Lat: {lat}, Lon: {lon}):\n"
                f"Temperature: {temperature}°F\n"
                f"Description: {weather_description}\n\n"
                f"Current Time: {current_time}"
            )
        else:
            await update.message.reply_text("Sorry, I couldn't get the time for your location.")
    else:
        await update.message.reply_text("Invalid zip code. Please try again.")
    
    return ConversationHandler.END  # End the conversation

# Handle channel posts and commands
async def handle_channel_post(update: Update, context: CallbackContext):
    logger.info(f"Received a post in the channel: {update.channel_post.text}")

    post_text = update.channel_post.text
    if post_text.startswith("/"):
        # Manually process commands posted in the channel
        await context.dispatcher.process_update(update)
    else:
        # Respond to non-command messages
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Channel post received: {post_text}")

# Handle regular messages in direct chat
async def handle_regular_message(update: Update, context: CallbackContext):
    logger.info(f"Received a regular message: {update.message.text}")

    text = update.message.text.strip()
    
    # Respond to the message (like the channel post) as needed
    await update.message.reply_text(f"Received: {text}")

def main():
    # Create the application with the bot token
    application = Application.builder().token('7823996299:AAHOsTyetmM50ZggjK2h_NWUR-Vm0gtolvY').build()

    # Register the start command handler
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # Register the help command handler
    help_handler = CommandHandler('help', help_command)
    application.add_handler(help_handler)

    # Register the quote command handler
    quote_handler = CommandHandler('quote', quote)
    application.add_handler(quote_handler)

    # Conversation handler for weather request
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^(Weather)$'), request_zip_code)],
        states={
            GET_ZIP_CODE: [MessageHandler(filters.TEXT, get_weather_time)],
        },
        fallbacks=[]
    )
    application.add_handler(conv_handler)

    # Register handler for channel posts and commands
    channel_handler = MessageHandler(filters.UpdateType.CHANNEL_POST, handle_channel_post)
    application.add_handler(channel_handler)

    # Register handler for regular messages (commands and non-commands) in DMs
    message_handler = MessageHandler(filters.TEXT, handle_regular_message)
    application.add_handler(message_handler)

    # Start the bot and run it until you press Ctrl+C
    application.run_polling()

if __name__ == '__main__':
    main()
