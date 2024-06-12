import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ( 
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    CallbackContext,
    ContextTypes
)

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

# To be moved to .json later
QUESTION_BANK = [
    {
        "question": "Where do our local macaques live in?",
        "options": [
            ("Forest", True),
            ("HDB corridor", False),
            ("Motorbike", False),
            ("Park bench", False)
        ]
    }
]

# Define command handlers
async def start_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    message = (
        "I'm a bot, please talk to me!\n\n"
        "Here are some commands you can use:\n"
        "/help - I need help!\n"
        "/photo - Send a photo\n"
        "/audio - Send an audio\n"
        "/video - Send a video\n"
        "/mcq - Sample MCQ\n"
    )
    await update.message.reply_text(message)

async def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text('How can I help you? ~ELZ')

async def photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('asset/bird_image.jpg', 'rb'))

async def audio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open('asset/bird_audio.mp3', 'rb'))

async def video_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_video(chat_id=update.effective_chat.id, video=open('asset/bird_video.mp4', 'rb'))

async def mcq_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    question = QUESTION_BANK[0]['question']
    options = QUESTION_BANK[0]['options']

    keyboard = [
        [InlineKeyboardButton(option, callback_data=str(correct)) for option, correct in options]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(question, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(question, reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button clicks."""
    query = update.callback_query
    await query.answer()
    is_correct = query.data == "True"

    if is_correct:
        await query.edit_message_text(text="That is correct!")
    else:
        await query.edit_message_text(text="Incorrect! Please try again.")
        await mcq_command(update, context)


def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Add handlers for the /start and /help commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler('photo', photo_command))
    application.add_handler(CommandHandler('audio', audio_command))
    application.add_handler(CommandHandler('video', video_command))
    application.add_handler(CommandHandler("mcq", mcq_command))

    application.add_handler(CallbackQueryHandler(button))

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    application.run_polling()

if __name__ == '__main__':
    main()
