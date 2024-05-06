# import os
# from io import BytesIO
# from queue import Queue
# import requests
# from flask import Flask, request
# from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackQueryHandler, Dispatcher
# from movies_scraper import search_movies, get_movie


# TOKEN = os.getenv("TOKEN")
# URL = os.getenv("URL")
# bot = Bot(TOKEN)


# def welcome(update, context) -> None:
#     update.message.reply_text(f"Hello {update.message.from_user.first_name}, Welcome to SB Movies.\n"
#                               f"🔥 Download Your Favourite Movies For 💯 Free And 🍿 Enjoy it.")
#     update.message.reply_text("👇 Enter Movie Name 👇")


# def find_movie(update, context):
#     search_results = update.message.reply_text("Processing...")
#     query = update.message.text
#     movies_list = search_movies(query)
#     if movies_list:
#         keyboards = []
#         for movie in movies_list:
#             keyboard = InlineKeyboardButton(movie["title"], callback_data=movie["id"])
#             keyboards.append([keyboard])
#         reply_markup = InlineKeyboardMarkup(keyboards)
#         search_results.edit_text('Search Results...', reply_markup=reply_markup)
#     else:
#         search_results.edit_text('Sorry 🙏, No Result Found!\nCheck If You Have Misspelled The Movie Name.')


# def movie_result(update, context) -> None:
#     query = update.callback_query
#     s = get_movie(query.data)
#     response = requests.get(s["img"])
#     img = BytesIO(response.content)
#     query.message.reply_photo(photo=img, caption=f"🎥 {s['title']}")
#     link = ""
#     links = s["links"]
#     for i in links:
#         link += "🎬" + i + "\n" + links[i] + "\n\n"
#     caption = f"⚡ Fast Download Links :-\n\n{link}"
#     if len(caption) > 4095:
#         for x in range(0, len(caption), 4095):
#             query.message.reply_text(text=caption[x:x+4095])
#     else:
#         query.message.reply_text(text=caption)


# def setup():
#     update_queue = Queue()
#     dispatcher = Dispatcher(bot, update_queue, use_context=True)
#     dispatcher.add_handler(CommandHandler('start', welcome))
#     dispatcher.add_handler(MessageHandler(Filters.text, find_movie))
#     dispatcher.add_handler(CallbackQueryHandler(movie_result))
#     return dispatcher


# app = Flask(__name__)


# @app.route('/')
# def index():
#     return 'Hello World!'


# @app.route('/{}'.format(TOKEN), methods=['GET', 'POST'])
# def respond():
#     update = Update.de_json(request.get_json(force=True), bot)
#     setup().process_update(update)
#     return 'ok'


# @app.route('/setwebhook', methods=['GET', 'POST'])
# def set_webhook():
#     s = bot.setWebhook('{URL}/{HOOK}'.format(URL=URL, HOOK=TOKEN))
#     if s:
#         return "webhook setup ok"
#     else:
#         return "webhook setup failed"

import os
from io import BytesIO
from queue import Queue
import requests
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackQueryHandler, Dispatcher
from movies_scraper import search_movies, get_movie
import logging

# Initialize logger for error tracking
logging.basicConfig(level=logging.INFO)

# Get sensitive data from environment variables
TOKEN = os.getenv("TOKEN")
URL = os.getenv("URL")
if not TOKEN or not URL:
    raise ValueError("Environment variables TOKEN and URL must be set.")

bot = Bot(TOKEN)

app = Flask(__name__)

def welcome(update, context):
    """Welcome message for the bot."""
    user_name = update.message.from_user.first_name
    update.message.reply_text(
        f"Hello {user_name}, Welcome to SB Movies.\n"
        "🔥 Download Your Favourite Movies For 💯 Free And 🍿 Enjoy it."
    )
    update.message.reply_text("👇 Enter Movie Name 👇")


def find_movie(update, context):
    """Find movies based on user query."""
    query = update.message.text
    search_results = update.message.reply_text("Processing...")
    
    try:
        movies_list = search_movies(query)
    except Exception as e:
        logging.error("Error fetching movie list: %s", e)
        search_results.edit_text("An error occurred while searching for movies. Please try again later.")
        return
    
    if movies_list:
        keyboards = [[InlineKeyboardButton(movie["title"], callback_data=movie["id"])] for movie in movies_list]
        reply_markup = InlineKeyboardMarkup(keyboards)
        search_results.edit_text("Search Results...", reply_markup=reply_markup)
    else:
        search_results.edit_text("Sorry 🙏, no results found. Check if you misspelled the movie name.")


def movie_result(update, context):
    """Get details and download links for a specific movie."""
    query = update.callback_query
    
    try:
        movie_details = get_movie(query.data)
    except Exception as e:
        logging.error("Error fetching movie details: %s", e)
        query.message.reply_text("An error occurred while retrieving movie details. Please try again later.")
        return
    
    try:
        img_response = requests.get(movie_details["img"])
        img_response.raise_for_status()  # Ensure the image is successfully fetched
        img = BytesIO(img_response.content)

        query.message.reply_photo(photo=img, caption=f"🎥 {movie_details['title']}")
        
        # Construct the message with download links
        download_links = ""
        for link_name, link_url in movie_details["links"].items():
            download_links += f"🎬 {link_name}: {link_url}\n"

        caption = f"⚡ Fast Download Links:\n\n{download_links}"

        if len(caption) > 4095:
            # Telegram has a limit on message length, split if needed
            for i in range(0, len(caption), 4095):
                query.message.reply_text(caption[i:i+4095])
        else:
            query.message.reply_text(caption)

    except Exception as e:
        logging.error("Error sending movie details: %s", e)
        query.message.reply_text("An error occurred while sending movie details. Please try again later.")


def setup():
    """Set up the Telegram dispatcher."""
    update_queue = Queue()
    dispatcher = Dispatcher(bot, update_queue, use_context=True)
    
    dispatcher.add_handler(CommandHandler('start', welcome))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, find_movie))
    dispatcher.add_handler(CallbackQueryHandler(movie_result))
    
    return dispatcher


@app.route('/')
def index():
    return 'Hello World!'


@app.route('/<path:path>', methods=['GET', 'POST'])
def respond(path):
    """Webhook endpoint for Telegram."""
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher = setup()  # Set up the dispatcher each time to handle updates
    dispatcher.process_update(update)
    return 'ok'


@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    """Set the webhook for the Telegram bot."""
    webhook_url = f"{URL}/{TOKEN}"
    response = bot.setWebhook(webhook_url)
    
    if response:
        return "Webhook setup successful"
    else:
        return "Webhook setup failed"
