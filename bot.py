import os
import json
from datetime import time, timedelta
import random
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
    MessageHandler,
    filters
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
    TOKEN = os.getenv('API_KEY_dev')
else:
    TOKEN = os.getenv('API_KEY_')

# Load question data from JSON file
with open('asset/question_bank.json', 'r') as file:
    question_bank = json.load(file)['questions']

# Global variable to manage user state
user_data = {}

# Function to get a random question the user has not yet answered
def get_random_question(user_id):
    answered_questions = user_data.get(user_id, {}).get('answered_questions', [])
    unanswered_questions = [q for q in question_bank if q not in answered_questions]

    if not unanswered_questions:
        # Reset the questions if all have been answered
        user_data[user_id]['answered_questions'] = []
        unanswered_questions = question_bank

    return random.choice(unanswered_questions)

def get_stamp_image(stamps):
    if stamps == 0:
        return 'asset/stamp_card_0.png'
    elif stamps == 1:
        return 'asset/stamp_card_1.png'
    elif stamps == 2:
        return 'asset/stamp_card_2.png'
    elif stamps == 3:
        return 'asset/stamp_card_0.png'
    elif stamps == 4:
        return 'asset/stamp_card_0.png'
    else:
        return 'asset/stamp_card_0.png'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user_id = update.effective_chat.id

    if user_id not in user_data:
        # First interaction
        user_data[user_id] = {'answered_questions': [], 'stamps': 0, 'first_try': True, 'first_question': True}

    await send_question(update, context)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    # Ensure a new question is generated if the current one is None
    if 'current_question' not in context.user_data or context.user_data['current_question'] is None:
        question = get_random_question(user_id)
        context.user_data['current_question'] = question
    else:
        question = context.user_data['current_question']
    user_data[user_id]['first_try'] = True

    keyboard = [[InlineKeyboardButton(option['text'], callback_data=str(option['correct']))] for option in question["options"]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if user_data[user_id]['first_question']:
        text = (
            f"Glad to have you onboard. Today's topic will be...{question['topic']}!"
        )
        user_data[user_id]['first_question'] = False
    else:
        text = (
            f"Let's move on! The next topic will be...{question['topic']}!"
        )
    await context.bot.send_message(
        chat_id=user_id,
        text=text
    )

    await context.bot.send_photo(
        chat_id=user_id,
        photo=question['topic_image_path'],
    )
    
    question_text = (
        """*__Question of the Day__*\n"""
        f"""{question["question"]}"""
    )

    await context.bot.send_message(chat_id=user_id, text=question_text, reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN_V2)

async def resend_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    question = context.user_data['current_question']

    keyboard = [[InlineKeyboardButton(option['text'], callback_data=str(option['correct']))] for option in question["options"]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=user_id, text="Please try again:", reply_markup=reply_markup)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.message.chat.id
    is_correct = query.data == "True"
    question = context.user_data['current_question']

    if is_correct:
        await context.bot.send_message(chat_id=user_id, text=question["correct_response"])
        if user_data[user_id]['first_try']:
            user_data[user_id]['stamps'] += 1
            stamps = user_data[user_id]['stamps']
            await context.bot.send_photo(chat_id=user_id, photo=open(get_stamp_image(stamps), 'rb'))
            await context.bot.send_message(chat_id=user_id, text="You have filled up your stamp card for today!")
        user_data[user_id]['answered_questions'].append(question)
        context.user_data['current_question'] = None
        await context.bot.send_message(
            chat_id=user_id,
            text="Would you like to answer one more question for today?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Yes, please", callback_data='yes')],
                [InlineKeyboardButton("No, thank you", callback_data='no')]
            ])
        )
    else:
        user_data[user_id]['first_try'] = False
        await context.bot.send_message(chat_id=user_id, text=question["incorrect_response"])
        await resend_question(update, context)

async def handle_yes_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.message.chat.id

    if query.data == 'yes':
        await send_question(update, context)
    elif query.data == 'no':
        await query.edit_message_text(text="Awesome, you've just learned a new fact! Come back tomorrow for another!")

        # # Schedule daily question
        # application.job_queue.run_daily(daily_notification, time=time(hour=10, minute=0, second=0))

        # Schedule daily question for testing: run once after 30 seconds
        context.job_queue.run_once(daily_notification, when=timedelta(seconds=10))

async def daily_notification(context: ContextTypes.DEFAULT_TYPE):
    for user_id in user_data.keys():
        await context.bot.send_message(
            chat_id=user_id,
            text="Hi! New question is in! Let's fill up your stamp today!"
        )
        stamps = user_data[user_id]['stamps']
        await context.bot.send_photo(chat_id=user_id, photo=open(get_stamp_image(stamps), 'rb'))
        await context.bot.send_message(
            chat_id=user_id,
            text="Click the button below to start",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Start", callback_data='start')]])
        )

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Add handlers for the /start command and callbacks
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern='^(True|False)$'))
    application.add_handler(CallbackQueryHandler(handle_yes_no, pattern='^(yes|no)$'))
    application.add_handler(CallbackQueryHandler(start, pattern='^start$'))

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    application.run_polling()

if __name__ == '__main__':
    main()
