from flask import Flask, request, Response
import requests
import os
from dotenv import load_dotenv

app = Flask(__name__)


# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv('API_KEY')

# To get chat ID and message sent by client
def message_parser(message):
    chat_id = message['message']['chat']['id']
    text = message['message']['text']
    print("Chat ID:", chat_id)
    print("Message:", text)
    return chat_id, text


# To send a text message using Telegram API
def send_message_telegram(chat_id, text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    response = requests.post(url, json=payload)
    return response


# To send a photo using Telegram API
def send_photo_telegram(chat_id, photo_path):
    url = f'https://api.telegram.org/bot{TOKEN}/sendPhoto'
    files = {'photo': open(photo_path, 'rb')}
    data = {'chat_id': chat_id}
    response = requests.post(url, files=files, data=data)
    return response


# To send a video using Telegram API
def send_video_telegram(chat_id, video_path):
    url = f'https://api.telegram.org/bot{TOKEN}/sendVideo'
    files = {'video': open(video_path, 'rb')}
    data = {'chat_id': chat_id}
    response = requests.post(url, files=files, data=data)
    return response


# To send an audio using Telegram API
def send_audio_telegram(chat_id, audio_path):
    url = f'https://api.telegram.org/bot{TOKEN}/sendAudio'
    files = {'audio': open(audio_path, 'rb')}
    data = {'chat_id': chat_id}
    response = requests.post(url, files=files, data=data)
    return response


# To send multiple-choice question using Telegram API
def send_multiple_choice_telegram(chat_id, question, options):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    keyboard = [[{"text": option, "callback_data": option}] for option in options]
    reply_markup = {"inline_keyboard": keyboard}
    payload = {
        'chat_id': chat_id,
        'text': question,
        'reply_markup': reply_markup
    }
    response = requests.post(url, json=payload)
    return response


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        msg = request.get_json()
        chat_id, incoming_que = message_parser(msg)
        if incoming_que.lower() == "photo":
            send_photo_telegram(chat_id, 'path_to_your_photo.jpg')
        elif incoming_que.lower() == "video":
            send_video_telegram(chat_id, 'path_to_your_video.mp4')
        elif incoming_que.lower() == "audio":
            send_audio_telegram(chat_id, 'path_to_your_audio.mp3')
        elif incoming_que.lower() == "question":
            question = "What is your favorite color?"
            options = ["Red", "Blue", "Green", "Yellow"]
            send_multiple_choice_telegram(chat_id, question, options)
        else:
            answer = "Still testing"
            send_message_telegram(chat_id, answer)
        return Response('ok', status=200)
    else:
        return "<h1>Telegram Bot is running</h1>"


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False, port=5000)