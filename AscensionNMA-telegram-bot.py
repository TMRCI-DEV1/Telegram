import random
import requests
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Define API keys and base URLs
WEATHER_API_KEY = "a10a17233a99d6e36c3d99f9493fddf5"
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"

# List of quotes
QUOTES = [
    "The only limit to our realization of tomorrow is our doubts of today. - Franklin D. Roosevelt",
    "Do not wait to strike till the iron is hot; but make it hot by striking. - William Butler Yeats",
    "Whether you think you can, or you think you can't--you're right. - Henry Ford",
    "The best way to predict the future is to invent it. - Alan Kay"
]

# Start command
async def start(update, context):
    await update.message.reply_text("Greetings peasant! I'm your new bot overlord. Send your zip code to get the current time and weather.")

# Help command
async def help_command(update, context):
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Get help\n"
        "/quote - Get a random quote\n"
        "Send your zip code to get the current weather and time."
    )
    await update.message.reply_text(help_text)

# Quote command
async def quote(update, context):
    # Send a random quote from the list
    random_quote = random.choice(QUOTES)
    await update.message.reply_text(random_quote)

# Weather and time functionality
async def get_weather_time(update, context):
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

    # Register the weather and time handler
    weather_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, get_weather_time)
    application.add_handler(weather_handler)

    # Start the bot and run it until you press Ctrl+C
    application.run_polling()

if __name__ == '__main__':
    main()
