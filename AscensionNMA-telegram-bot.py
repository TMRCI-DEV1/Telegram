from telegram.ext import Application, CommandHandler

# Define the start command callback as async
async def start(update, context):
    await update.message.reply_text("Greetings peasant! I'm your new bot overlord.")

# Define the help command callback as async
async def help_command(update, context):
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Get help"
    )
    await update.message.reply_text(help_text)

def main():
    # Create the application with the bot token
    application = Application.builder().token('7823996299:AAHOsTyetmM50ZggjK2h_NWUR-Vm0gtolvY').build()

    # Register the start command handler
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # Register the help command handler
    help_handler = CommandHandler('help', help_command)
    application.add_handler(help_handler)

    # Start the bot and run it until you press Ctrl+C
    application.run_polling()

if __name__ == '__main__':
    main()
