import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, ConversationHandler, filters
import openai
import base64
from PIL import Image
import io
import requests
import os

# Load your tokens from environment variables for better security
TELEGRAM_TOKEN = ('6874182590:AAH9CE1bBrSDSFtPsYKrGXcHilniORhbL6w')
OPENAI_API_KEY = ('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')

openai.api_key = OPENAI_API_KEY
api_url = "https://api.openai.com/v1/chat/completions"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

model = 'gpt-4'

chat_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    await update.message.reply_text('Привет! Я Umit AI. Я могу помочь определить заболевания растений по фото, предложить решения и отвечать на ваши вопросы о сельском хозяйстве.')
    if chat_id not in chat_histories:
        chat_histories[chat_id] = [{"role": "system", "content": "Я Umit AI. Я могу помочь определить заболевания растений, предложить решения и отвечать на ваши вопросы о сельском хозяйстве."}]

def encode_image_from_bytes(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    base64_image = encode_image_from_bytes(photo_bytes)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    payload = {
  "model": "gpt-4-turbo",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Определить болезнь растения и предложить способы лечения растения."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image}"
          }
        }
      ]
    }
  ],
  "max_tokens": 300
}

    
    response = requests.post(api_url, headers=headers, json=payload)
    response.raise_for_status()
    response_data = response.json()
    bot_message = response_data['choices'][0]['message']['content']
    await update.message.reply_text(bot_message)
    chat_histories[update.message.chat_id].append({"role": "assistant", "content": bot_message})
    

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    user_message = update.message.text
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []

    chat_histories[chat_id].append({"role": "user", "content": user_message})
    try:
        response = openai.ChatCompletion.create(model=model, messages=chat_histories[chat_id])
        bot_message = response.choices[0].message['content']
        await update.message.reply_text(bot_message)
        chat_histories[chat_id].append({"role": "assistant", "content": bot_message})
    except openai.Error as e:
        await update.message.reply_text('Error processing your message.')
        logger.error(f"OpenAI request failed: {e}")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Text() & ~filters.Command(), echo))
    application.run_polling()

if __name__ == '__main__':
    main()
