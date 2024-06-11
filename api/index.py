import os
from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

app = Flask(__name__)

TOKEN = os.getenv('API_KEY')
bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! I am Mighty Macaque!')

async def send_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open('assets/bird_image.jpg', 'rb') as photo:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo)

async def send_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open('assets/bird_audio.mp3', 'rb') as audio:
        await context.bot.send_audio(chat_id=update.effective_chat.id, audio=audio)

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open('assets/bird_video.mp4', 'rb') as video:
        await context.bot.send_video(chat_id=update.effective_chat.id, video=video)

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("photo", send_photo))
application.add_handler(CommandHandler("audio", send_audio))
application.add_handler(CommandHandler("video", send_video))

@app.route('/api/webhook', methods=['POST'])
def webhook():
    async def handle_update(update_json):
        update = Update.de_json(update_json, bot)
        await application.update_queue.put(update)

    update_json = request.get_json(force=True)
    asyncio.run(handle_update(update_json))
    return jsonify({'status': 'ok'})

if __name__ == "__main__":
    app.run(port=5000)
