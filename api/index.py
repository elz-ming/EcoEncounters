import os
import logging
import html
import asyncio
from flask import Flask, Response, abort, make_response, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, TypeHandler
from dataclasses import dataclass
from http import HTTPStatus
import uvicorn
from asgiref.wsgi import WsgiToAsgi

# Configuration constants
URL = os.getenv('WEBHOOK_URL')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', '123456'))
TOKEN = os.getenv('API_KEY')

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@dataclass
class WebhookUpdate:
    user_id: int
    payload: str

class CustomContext(ContextTypes.DEFAULT_TYPE):
    @classmethod
    def from_update(cls, update, application):
        if isinstance(update, WebhookUpdate):
            return cls(application=application, user_id=update.user_id)
        return super().from_update(update, application)

async def start(update: Update, context: CustomContext):
    payload_url = html.escape(f"{URL}/submitpayload?user_id=<your user id>&payload=<payload>")
    text = f"To check if the bot is still running, call <code>{URL}/healthcheck</code>.\n\nTo post a custom update, call <code>{payload_url}</code>."
    await update.message.reply_html(text=text)

async def webhook_update(update: WebhookUpdate, context: CustomContext):
    chat_member = await context.bot.get_chat_member(chat_id=update.user_id, user_id=update.user_id)
    payloads = context.user_data.setdefault("payloads", [])
    payloads.append(update.payload)
    combined_payloads = "</code>\n• <code>".join(payloads)
    text = f"The user {chat_member.user.mention_html()} has sent a new payload. So far they have sent the following payloads: \n\n• <code>{combined_payloads}</code>"
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode="HTML")

async def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(TypeHandler(WebhookUpdate, webhook_update))
    await application.bot.set_webhook(url=f"{URL}/telegram")

    flask_app = Flask(__name__)

    @flask_app.post("/telegram")
    async def telegram() -> Response:
        await application.update_queue.put(Update.de_json(data=request.json, bot=application.bot))
        return Response(status=HTTPStatus.OK)

    @flask_app.route("/submitpayload", methods=["GET", "POST"])
    async def custom_updates() -> Response:
        try:
            user_id = int(request.args["user_id"])
            payload = request.args["payload"]
        except KeyError:
            abort(HTTPStatus.BAD_REQUEST, "Please pass both `user_id` and `payload` as query parameters.")
        except ValueError:
            abort(HTTPStatus.BAD_REQUEST, "The `user_id` must be an integer!")
        await application.update_queue.put(WebhookUpdate(user_id=user_id, payload=payload))
        return Response(status=HTTPStatus.OK)

    @flask_app.get("/healthcheck")
    async def health() -> Response:
        response = make_response("The bot is still running fine :)", HTTPStatus.OK)
        response.mimetype = "text/plain"
        return response

    return WsgiToAsgi(flask_app)

asgi_app = asyncio.run(main())
