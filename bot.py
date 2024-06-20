# ================== #
# ===== Import ===== #
# ================== #
import os
from datetime import datetime, timezone, timedelta
import logging
from pymongo import MongoClient
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

# ========================= #
# ===== Logging Logic ===== #
# ========================= #
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ====================================== #
# ===== Load Environment Variables ===== #
# ====================================== #
if os.getenv('ENV') is None:
    from dotenv import load_dotenv
    load_dotenv()

TOKEN = os.getenv('API_KEY')

MONGO_USER = os.getenv('MONGO_USER')
MONGO_PWD = os.getenv('MONGO_PWD')
MONGO_CLUSTER = os.getenv('MONGO_CLUSTER')
MONGO_APP = os.getenv('MONGO_APP')
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PWD}@{MONGO_CLUSTER}/?retryWrites=true&w=majority&appName={MONGO_APP}"

# ========================= #
# ===== MongoDB setup ===== #
# ========================= #
client = MongoClient(MONGO_URI)
MONGO_DB = os.getenv('MONGO_DB')
db = client[MONGO_DB]
users_col = db.users
question_sets_col = db.question_sets
stats_col = db.stats
assets_col = db.assets

# ============================ #
# ===== Helper Functions ===== #
# ============================ #
def formatText(text):
    return text.replace("!", "\\!").replace(".", "\\.").replace("(", "\\(").replace(")", "\\)").replace("#", "\\#").replace("-", "\\-")

# ======================== #
# ===== User Journey ===== #
# ======================== #

# 1. After the user press /start, this will run to store or retrieve the user's data
async def handleStart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user_id = update.effective_chat.id
    user = users_col.find_one({"_id": user_id})
    if not user:
        users_col.insert_one({
            "_id": user_id,
            "username": update.effective_chat.username,
            "difficulty": "Easy",
            "correct_today": 0,
            "incorrect_today": 0,
            "badge": ""
        })
    else:
        context.user_data['correct_answers'] = user["correct_today"]
        context.user_data['incorrect_answers'] = user["incorrect_today"]

    # Initialize context variables
    context.user_data['current_message_id'] = None
    context.user_data['current_message_text'] = None
    context.user_data['additional_message_text'] = None
    context.user_data['selected_topic'] = None
    context.user_data['correct_answers'] = 0
    context.user_data['incorrect_answers'] = 0

    await sendTopicChoice(update, context)

# 2. Continuing from the /start button, a message to select game choice and inform the existence of /mode button
async def sendTopicChoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user = users_col.find_one({"_id": user_id})
    difficulty = user["difficulty"]
    previous_message_id = context.user_data.get('current_message_id')
    additional_text = context.user_data.get('additional_message_text')

    if difficulty == "Easy":
        emoji = "🐥"
    elif difficulty == "Intermediate":
        emoji = "🐔"

    text = (
        """*Pick your EcoEncounter today!*\n"""
        f"""{emoji} Mode: {difficulty} {emoji}\n"""
        """Use /mode to adjust difficulty\n"""
    )

    if additional_text:
        text = additional_text + text

    text = formatText(text)

    message = await context.bot.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🐒 Mighty Macaque", callback_data='mighty_macaque')],
            [InlineKeyboardButton("🕊️ Pigeon Plight", callback_data='pigeon_plight')]
        ]),
        parse_mode=constants.ParseMode.MARKDOWN_V2
    )

    if previous_message_id:
        await context.bot.delete_message(chat_id=user_id, message_id=previous_message_id)

    # Store the initial message ID in the user_data
    context.user_data['current_message_id'] = message.message_id
    context.user_data['current_message_text'] = text

# 3. After the user selects Mighty Macaque or Pigeon Plight, the following is executed
async def handleTopicChoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    topic = query.data
    user_id = update.effective_chat.id
    user = users_col.find_one({"_id": user_id})
    difficulty = user["difficulty"]

    # Check if the selected topic is available
    is_available = question_sets_col.find_one({"topic": topic, "difficulty": difficulty}) is not None
    
    if not is_available:
        text=f"Sorry, {topic.replace('_', ' ').title()} ({difficulty}) is unavailable now. Please select another mode.\n\n"

        # Store the add on message text in the user_data
        context.user_data['additional_message_text'] = text

        # Resend the topic choice message
        await sendTopicChoice(update, context)

    else:
        text=f"\nYou've selected: {topic.replace('_', ' ').title()}\n\n"
        text=formatText(text)

        # Store the add on message text in the user_data
        context.user_data['selected_topic'] = topic
        context.user_data['additional_message_text'] = text

        # Start the topic
        await sendTopicStart(update, context, topic)

async def sendTopicStart(update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str):
    user_id = update.effective_chat.id
    previous_message_id = context.user_data.get('current_message_id')
    previous_message_text = context.user_data.get('current_message_text')
    additional_text = context.user_data.get('additional_message_text')

    if previous_message_id and additional_text:
        text = previous_message_text + additional_text

    await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=previous_message_id,
            text=text,
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )
    
    badge_image = assets_col.find_one({"filename": "badge_silhouette"}).get('data')
    badge_text = "Digital Badges will be earned through daily interactions with the game. Let’s see how good you are in completing this quiz amongst others! 🏆💯"

    # Send an image (update with the actual image path or URL)
    await context.bot.send_photo(
        chat_id=user_id,
        photo=badge_image,
        caption=badge_text
    )

    # Retrieve the image for the selected topic from MongoDB
    topic_image = assets_col.find_one({"filename": f"{topic}"}).get('data')

    if topic_image:
        message = await context.bot.send_photo(
            chat_id=user_id,
            photo=topic_image,
            caption=f"You have chosen to walk the path of the {topic.replace('_', ' ').title()}.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Next", callback_data=f'topic_start')]
            ])
        )

    # Store the initial message ID in the user_data
    context.user_data['current_message_id'] = message.message_id
    context.user_data['current_message_text'] = message.caption

async def handleTopicStart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_chat.id
    previous_message_id = context.user_data.get('current_message_id')
    previous_message_text = context.user_data.get('current_message_text')

    text = previous_message_text + "\n\nGood Luck! 🎉🎉🎉"

    if previous_message_id:
        await context.bot.edit_message_caption(
                chat_id=user_id,
                message_id=previous_message_id,
                caption=text
            )

    # Proceed to send the question set for the selected topic
    await sendQuestionSet(update, context)

async def sendQuestionSet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user = users_col.find_one({"_id": user_id})
    difficulty = user["difficulty"]

    # Retrieve the selected topic from the user's data
    topic = context.user_data['selected_topic']
    
    # Retrieve a random question set for the selected difficulty
    question_set = question_sets_col.aggregate([
        {"$match": {"difficulty": difficulty, "topic": topic}},
        {"$sample": {"size": 1}}
    ]).next()

    if not question_set:
        await context.bot.send_message(
            chat_id=user_id,
            text="Sorry, no questions are available for the selected difficulty."
        )
        return

    # Store the current question set in the user_data
    context.user_data['current_question_set'] = question_set
    context.user_data['current_question_index'] = 0
    
    # Send the first question in the set
    await sendQuestion(update, context)

async def sendQuestion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    question_set = context.user_data['current_question_set']
    question_index = context.user_data['current_question_index']

    question = question_set['questions'][question_index]
    question_text = question['question']

    keyboard = [[InlineKeyboardButton(option['text'], callback_data=option['option_id'])] for option in question["options"]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"""*__Encounter #{question_index + 1} of {len(question_set['questions'])}__*\n"""
        f"""{question_text}"""
    )

    text = formatText(text)

    question_image = question['image']
    if question_image: 
        message = await context.bot.send_photo(
            chat_id=user_id,
            photo=question_image,
            caption=text,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )
    else:
        message = await context.bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )

    # Store the initial message ID in the user_data
    context.user_data['current_message_id'] = message.message_id
    context.user_data['current_message_text'] = message.caption

async def handleAnswer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.message.chat.id
    selected_option_id = query.data
    question_set = context.user_data['current_question_set']
    question_index = context.user_data['current_question_index']
    question = question_set['questions'][question_index]
    selected_option = next(option for option in question["options"] if option['option_id'] == selected_option_id)
    is_correct = selected_option['correct']

    # Update option selection counts
    question_text = question['question']
    question_sets_col.update_one(
        {"questions.question": question_text, "questions.options.option_id": selected_option_id},
        {"$inc": {"questions.$[question].options.$[option].selected_today": 1}},
        array_filters=[{"question.question": question_text}, {"option.option_id": selected_option_id}]
    )

    # Update question statistics
    if is_correct:
        users_col.update_one({"_id": user_id}, {"$inc": {"correct_today": 1}})
        question_sets_col.update_one(
            {"questions.question": question_text},
            {"$inc": {"questions.$[question].correct_today": 1}},
            array_filters=[{"question.question": question_text}]
        )
        context.user_data['correct_answers'] = context.user_data.get('correct_answers') + 1
    else:
        users_col.update_one({"_id": user_id}, {"$inc": {"incorrect_today": 1}})
        question_sets_col.update_one(
            {"questions.question": question_text},
            {"$inc": {"questions.$[question].incorrect_today": 1}},
            array_filters=[{"question.question": question_text}]
        )
        context.user_data['incorrect_answers'] = context.user_data.get('incorrect_answers') + 1

    # Retrieve updated question data
    updated_question = question_sets_col.find_one({"questions.question": question_text}, {"questions.$": 1})
    updated_options = updated_question['questions'][0]['options']

    # Calculate the total number of attempts for the question
    total_attempts_today = updated_question['questions'][0]['correct_today'] + updated_question['questions'][0]['incorrect_today']

    # Format the response message
    response_text = f"Encounter #{question_index + 1} of {len(question_set['questions'])}\n{question['question']}\n\n"
    for option in updated_options:
        selected_indicator = "✅" if option['correct'] else "❌"
        bold_start = "<b>" if option['option_id'] == selected_option_id else ""
        bold_end = "</b>" if option['option_id'] == selected_option_id else ""
        percentage = int((option['selected_today'] / total_attempts_today) * 100 if total_attempts_today > 0 else 0)
        response_text += f"{bold_start}{percentage}% - {selected_indicator} {option['text']}{bold_end}\n"
    
    
    # Edit the original message to show the response
    await query.edit_message_caption(
        caption=response_text, 
        parse_mode=constants.ParseMode.HTML
    )

    # Send explanation images
    explanation_image = selected_option.get('explanation_image')
    if not is_correct and explanation_image:
        await context.bot.send_photo(
            chat_id=user_id,
            photo=explanation_image
        )

    explanation = f"{selected_option['explanation']}"
    await context.bot.send_message(
            chat_id=user_id,
            text=explanation
        )

    # Send the correct answer explanation image if the answer is incorrect
    correct_option = next(option for option in question["options"] if option['correct'])
    correct_explanation_image = correct_option.get('explanation_image')
    if correct_explanation_image:
        await context.bot.send_photo(
            chat_id=user_id,
            photo=correct_explanation_image
        )

    # Move to the next question or end the set
    if question_index + 1 < len(question_set['questions']):
        context.user_data['current_question_index'] += 1
        message = await context.bot.send_message(
            chat_id=user_id,
            text="Next question coming up...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Next", callback_data=f'next_question')]
            ])
        )
        context.user_data['current_message_id'] = message.message_id
    else:
        correct_answers = context.user_data.get('correct_answers')
        incorrect_answers = context.user_data.get('incorrect_answers')

        badge_filename = "badge_1star"
        caption = "*Great start!* You earn yourself an EcoEnthusiast badge for your efforts today. Feel proud of your achievement and share on your instagram! See you tomorrow."

        if correct_answers == 3:
            badge_filename = "badge_3star"
            caption = "*Awesome! You have answered 3 out of 3 questions perfectly.* You earn yourself an EcoExperts badge for your efforts today. Feel proud of your achievement and share on your instagram! See you tomorrow."
        elif correct_answers == 2:
            badge_filename = "badge_2star"
            caption = "*Excellent work! You have answered 2 out of 3 questions correctly.* You earn yourself an EcoExplorer badge for your efforts today. Feel proud of your achievement and share on your instagram! See you tomorrow."

        caption = formatText(caption)

        badge = assets_col.find_one({"filename": badge_filename})
        await context.bot.send_photo(
            chat_id=user_id,
            photo=badge['data'],
            caption=caption,
            parse_mode=constants.ParseMode.MARKDOWN_V2
        )
        
async def handleNextQuestion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.message.chat.id
    previous_message_id = context.user_data.get('current_message_id')

    await context.bot.delete_message(
        chat_id=user_id, 
        message_id=previous_message_id
    )

    await sendQuestion(update, context)

async def handleMode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    # If the topic has not been selected, allow changing difficulty
    if context.user_data.get('selected_topic') is None:
        await changeMode(update, context)
    else:
        # If the topic has been selected, allow changing difficulty but send back to topic selection
        context.user_data['change_mode_return_to_topic'] = True
        await changeMode(update, context)

async def changeMode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    message = await context.bot.send_message(
        chat_id=user_id,
        text="Select difficulty:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Easy", callback_data='Easy')],
            [InlineKeyboardButton("Intermediate", callback_data='Intermediate')],
        ])
    )

    context.user_data['current_message_id'] = message.message_id

async def setMode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.message.chat.id
    difficulty = query.data
    previous_message_id = context.user_data['current_message_id']

    users_col.update_one(
        {"_id": user_id},
        {"$set": {"difficulty": difficulty}}
    )

    if previous_message_id:
        await context.bot.delete_message(chat_id=user_id, message_id=previous_message_id)
    
    context.user_data.clear()
    # Redirect to topic selection
    await handleStart(update, context)

async def reset_statistics(context: ContextTypes.DEFAULT_TYPE):
    users_col.update_many({}, {"$set": {"correct_today": 0, "incorrect_today": 0}})
    question_sets_col.update_many({}, {"$set": {"questions.$[].correct_today": 0, "questions.$[].incorrect_today": 0, "questions.$[].options.$[].selected_today": 0}})

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Add handlers for the /start command and callbacks
    application.add_handler(CommandHandler("start", handleStart))
    application.add_handler(CommandHandler("mode", handleMode))

    application.add_handler(CallbackQueryHandler(handleTopicChoice, pattern='^(mighty_macaque|pigeon_plight)$'))
    application.add_handler(CallbackQueryHandler(handleTopicStart, pattern='topic_start'))
    application.add_handler(CallbackQueryHandler(handleAnswer, pattern='^\d+$'))
    application.add_handler(CallbackQueryHandler(handleNextQuestion, pattern='^next_question$'))
    application.add_handler(CallbackQueryHandler(setMode, pattern='^(Easy|Intermediate)$'))

    # Schedule daily reset at 10 AM UTC
    job_queue = application.job_queue
    reset_time = datetime.now(timezone.utc).replace(hour=10, minute=0, second=0, microsecond=0)
    if reset_time < datetime.now(timezone.utc):
        reset_time += timedelta(days=1)
    job_queue.run_repeating(reset_statistics, interval=timedelta(days=1), first=reset_time)

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    application.run_polling()

if __name__ == '__main__':
    main()
