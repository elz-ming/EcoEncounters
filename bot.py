import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

if os.getenv('ENV') != 'prod':
    from dotenv import load_dotenv
    load_dotenv()

# Define the bot token
TOKEN = os.getenv('API_KEY')

# Define command handlers
async def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hi!')

async def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text('Help!')

async def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Add handlers for the /start and /help commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Add a handler for normal messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    application.run_polling()

if __name__ == '__main__':
    main()
