import logging
import os
import re
import textwrap

import redis
from dotenv import load_dotenv
from handle_elasticpath_store import (
    add_product_to_cart,
    create_customer,
    delete_cart_item,
    get_cart_items,
    get_product,
    get_product_image,
    get_product_stock,
    get_products,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)


_database = None


def start(bot, update):
    products = get_products()
    keyboard = [[InlineKeyboardButton(product['name'], callback_data=product['id']) for product in products]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        f'Привет, {update.message.chat.username} \n Я бот рыбного магазина!',
        reply_markup=reply_markup,
        )

    return 'HANDLE_PRODUCT'


def handle_menu(bot, update):
    products = get_products()
    keyboard = [[InlineKeyboardButton(product['name'], callback_data=product['id']) for product in products]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text(
        'Меню',
        reply_markup=reply_markup,
    )
    bot.delete_message(chat_id=update.callback_query.message.chat.id,
                       message_id=update.callback_query.message.message_id)

    return 'HANDLE_PRODUCT'


def create_cart_text_and_keyboard(cart):
    cart_text = ''
    keyboard = []
    if cart['data']:
        for cart_items in cart['data']:
            display_price_with_tax = cart_items['meta']['display_price']['with_tax']
            formatted_price = display_price_with_tax['unit']['formatted']
            cart_text += textwrap.dedent(
                f'''
                {cart_items["name"]}
                {cart_items["description"]}
                {formatted_price} per kg 
                {cart_items["quantity"]} kg in cart
                for {display_price_with_tax["value"]["formatted"]}
                '''
            )
            keyboard.append([InlineKeyboardButton(f'Убрать из корзины {cart_items["name"]}',
                                                  callback_data=f'Убрать {cart_items["id"]}')])
    else:
        cart_text = 'У вас еще нет товаров в корзине'

    return cart_text, keyboard


def delete_from_cart(bot, update):
    query = update.callback_query
    chat_id = query.message.chat.id
    _, item_id = query.data.split()
    cart = delete_cart_item(chat_id, item_id)
    cart_text, keyboard = create_cart_text_and_keyboard(cart)
    keyboard.append([InlineKeyboardButton('В меню', callback_data='Назад')])
    keyboard.append([InlineKeyboardButton('Оплатить', callback_data='Оплатить')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=query.message.chat_id, text=cart_text, reply_markup=reply_markup)
    bot.delete_message(chat_id=update.callback_query.message.chat.id,
                       message_id=update.callback_query.message.message_id)

    return 'VIEW_CART'


def view_cart(bot, update):
    query = update.callback_query
    chat_id = query.message.chat.id
    cart = get_cart_items(chat_id)
    cart_text, keyboard = create_cart_text_and_keyboard(cart)
    keyboard.append([InlineKeyboardButton('В меню', callback_data='Назад')])
    keyboard.append([InlineKeyboardButton('Оплатить', callback_data='Оплатить')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=query.message.chat_id, text=cart_text, reply_markup=reply_markup)
    bot.delete_message(chat_id=update.callback_query.message.chat.id,
                       message_id=update.callback_query.message.message_id)

    return 'VIEW_CART'


def add_to_cart(bot, update):
    query = update.callback_query
    chat_id = query.message.chat.id
    _, item_quantity, product_sku = query.data.split()
    add_product_to_cart(chat_id, product_sku, int(item_quantity))

    return 'HANDLE_PRODUCT'


def handle_product(bot, update):
    query = update.callback_query
    product = get_product(query.data)
    product_name = product['name']
    product_sku = product['sku']
    product_description = product['description']
    display_price_with_tax = product['meta']['display_price']['with_tax']
    formatted_price = display_price_with_tax['formatted']
    product_stock = get_product_stock(query.data)
    total_stock = f'{product_stock["total"]} units in stock'
    if product['meta']['stock']['availability'] == 'out-stock':
        total_stock = 'Нет в наличии'
    weight = f'per {product["weight"]["kg"]} kg'
    price_and_weight = f'{formatted_price} {weight}'
    if formatted_price == '$0.00':
        price_and_weight = 'Цена не определена'
    text = f'{product_name}\n{price_and_weight}\n{total_stock}\n{product_description}'
    keyboard = [
        [InlineKeyboardButton('1 kg', callback_data=f'weight 1 {product_sku}'),
         InlineKeyboardButton('2 kg', callback_data=f'weight 2 {product_sku}'),
         InlineKeyboardButton('5 kg', callback_data=f'weight 5 {product_sku}')],
        [InlineKeyboardButton('Корзина', callback_data='Корзина')],
        [InlineKeyboardButton('Назад', callback_data='Назад')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if not product['relationships']:
        bot.send_message(chat_id=query.message.chat_id, text=text, reply_markup=reply_markup)
    else:
        image_link = get_product_image()
        bot.send_photo(
            chat_id=query.message.chat_id,
            photo=image_link,
            caption=text,
            reply_markup=reply_markup,
        )
    bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)

    return 'HANDLE_PRODUCT'


def check_email(bot, update):
    email = update.message.text
    match = re.search(r'[\w.-]+@[\w.-]+.\w+', email)
    if match:
        create_customer(email)
        bot.send_message(chat_id=update.message.chat_id, text=f'{email} сохранен')

        return 'HANDLE_MENU'
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Введите верный email')

        return 'CHECK_EMAIL'


def waiting_email(bot, update):
    bot.send_message(chat_id=update.callback_query.message.chat_id, text='Введите email')

    return 'CHECK_EMAIL'


def handle_users_reply(bot, update):
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id

    if user_reply == '/start':
        user_state = 'START'
    elif user_reply == 'Назад':
        user_state = 'HANDLE_MENU'
    elif user_reply.startswith('weight'):
        user_state = 'ADD_TO_CART'
    elif user_reply == 'Корзина':
        user_state = 'VIEW_CART'
    elif user_reply == 'Оплатить':
        user_state = 'WAITING_EMAIL'
    elif user_reply.startswith('Убрать'):
        user_state = 'DELETE_FROM_CART'
    else:
        user_state = db.get(chat_id).decode("utf-8")

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_PRODUCT': handle_product,
        'VIEW_CART': view_cart,
        'ADD_TO_CART': add_to_cart,
        'DELETE_FROM_CART': delete_from_cart,
        'WAITING_EMAIL': waiting_email,
        'CHECK_EMAIL': check_email,
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
