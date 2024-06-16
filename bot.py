import os
import logging
from telegram import (
    Update, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    constants
)
from telegram.ext import ( 
    Application,     
    CallbackQueryHandler, 
    CommandHandler, 
    ContextTypes,
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

if os.getenv('ENV') is None:
    from dotenv import load_dotenv
    load_dotenv()

TOKEN = os.getenv('API_KEY')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=user_id,
        text="Welcome! Click the button below to generate an image.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Generate Image", callback_data='generate_image')]
        ])
    )

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.message.chat.id

    # Generate the image
    image_url = 'https://mighty-macaque-30f16fdc84f3.herokuapp.com/images/badge_1'
    
    await context.bot.send_photo(
        chat_id=user_id,
        photo=image_url,
        caption="Here is your generated image!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Share to Instagram", callback_data=f'share_to_instagram')]
        ])
    )

async def share_to_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.message.chat.id

    # Extract the image URL from the callback data
    image_url = 'https://mighty-macaque-30f16fdc84f3.herokuapp.com/images/badge_1'

    # Provide the link to share the image to Instagram
    share_link = f'instagram://story-camera?AssetPath={image_url}'
    
    await context.bot.send_message(
        chat_id=user_id,
        text=f"Click [here]({share_link}) to share the image on Instagram.",
        parse_mode=constants.ParseMode.MARKDOWN_V2
    )

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Add handlers for the /start command and callbacks
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(generate_image, pattern='generate_image'))
    application.add_handler(CallbackQueryHandler(share_to_instagram, pattern='share_to_instagram'))

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    application.run_polling()

if __name__ == '__main__':
    main()
