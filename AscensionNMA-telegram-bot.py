import requests
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Define API keys and base URLs
WEATHER_API_KEY = "a10a17233a99d6e36c3d99f9493fddf5"
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"
TIME_API_URL = "http://worldtimeapi.org/api/timezone"

# Define the start command callback as async
async def start(update, context):
    await update.message.reply_text("Greetings peasant! I'm your new bot overlord. Send your zip code to get the current time and weather.")

# Define the help command callback as async
async def help_command(update, context):
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Get help\n"
        "Send your zip code to get the current weather and time."
    )
    await update.message.reply_text(help_text)

# Weather and time functionality
async def get_weather_time(update, context):
    zip_code = update.message.text.strip()
    
    # Get weather data from OpenWeatherMap
    weather_params = {
        'zip': zip_code,
        'appid': WEATHER_API_KEY,
        'units': 'imperial'  # Use 'metric' for Celsius
    }
    
    weather_response = requests.get(WEATHER_API_URL, params=weather_params)
    
    if weather_response.status_code == 200:
        weather_data = weather_response.json()
        city_name = weather_data['name']
        temperature = weather_data['main']['temp']
        weather_description = weather_data['weather'][0]['description']

        # Get time data from World Time API (You can improve this to calculate timezone dynamically)
        time_response = requests.get(f"http://worldtimeapi.org/api/timezone/Etc/GMT")
        
        if time_response.status_code == 200:
            time_data = time_response.json()
            current_time = time_data['datetime']

            # Send weather and time info to the user
            await update.message.reply_text(f"Weather in {city_name}:\nTemperature: {temperature}°F\nDescription: {weather_description}\n\nCurrent Time: {current_time}")
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

    # Register the weather and time handler
    weather_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, get_weather_time)
    application.add_handler(weather_handler)

    # Start the bot and run it until you press Ctrl+C
    application.run_polling()

if __name__ == '__main__':
    main()
