import os
import logging
import redis
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

from handle_elasticpath_store import get_products, get_product, get_product_stock

_database = None
PRODUCTS = get_products()
KEYBOARD = [[InlineKeyboardButton(product['name'], callback_data=product['id']) for product in PRODUCTS]]

def start(bot, update):
    reply_markup = InlineKeyboardMarkup(KEYBOARD)
    update.message.reply_text(
        f'Привет, {update.message.chat.username} \n Я бот рыбного магазина!',
        reply_markup=reply_markup,
        )
    return 'HANDLE_MENU'


def echo(bot, update):
    users_reply = update.message.text
    update.message.reply_text(users_reply)
    return "ECHO"


def handle_menu(bot, update):
    query = update.callback_query
    product = get_product(query.data)
    product_name = product["name"]
    product_description = product["description"]
    display_price_with_tax = product['meta']['display_price']['with_tax']
    formatted_price = display_price_with_tax['formatted']
    wight_kg = product['weight']['kg']
    product_stock = get_product_stock(query.data)
    print(product_stock)
    reply_markup = InlineKeyboardMarkup(KEYBOARD)
    text = f'{product_name} \n {formatted_price} per {wight_kg} kg \n' \
           f'{product_stock["total"]} units in stock \n'  \
           f'{product_description}'

    bot.edit_message_text(
        text=text,
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=reply_markup,
    )

    return 'START'


def handle_users_reply(bot, update):
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode("utf-8")

    states_functions = {
        'START': start,
        'ECHO': echo,
        'HANDLE_MENU': handle_menu,
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(bot, update)
        db.set(chat_id, next_state)
    except Exception as err:
        logging.warning(err)


def get_database_connection():
    global _database
    if not _database:
        database_password = os.getenv("REDIS_PASSWORD")
        database_host = os.getenv("REDIS_HOST")
        database_port = os.getenv("REDIS_PORT")
        _database = redis.Redis(host=database_host, port=database_port, password=database_password)
    return _database


if __name__ == '__main__':
    load_dotenv()
    token = os.getenv("TG_TOKEN")
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()
