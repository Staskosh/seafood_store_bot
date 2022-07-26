import datetime
import os

import requests


def check_and_get_moltin_token(client_id, client_secret):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    token_expires_time = os.getenv('ELASTICPATH_TOKEN_EXPIRES_TIME')
    test_timestamp = datetime.datetime.now().timestamp()
    if not token_expires_time or int(token_expires_time) <= test_timestamp:
        response = requests.post('https://api.moltin.com/oauth/access_token', headers=headers, data=payload)
        response.raise_for_status()
        os.environ['ELASTICPATH_TOKEN'] = response.json()['access_token']
        os.environ['ELASTICPATH_TOKEN_EXPIRES_TIME'] = str(response.json()['expires'])
        return response.json()['access_token']
    else:
        return os.getenv('ELASTICPATH_TOKEN')


def get_products(client_id, client_secret):
    token = check_and_get_moltin_token(client_id, client_secret)
    headers = {
        'Authorization': f'Bearer {token}',
    }
    products_url = 'https://api.moltin.com/v2/products'
    response = requests.get(products_url, headers=headers)
    response.raise_for_status()
    products = response.json()['data']

    return products


def create_customer(email, client_id, client_secret):
    token = check_and_get_moltin_token(client_id, client_secret)
    headers = {
        'Authorization': f'Bearer {token}',
    }

    payload = {
        'data': {
            'type': 'customer',
            'name': email,
            'email': email,
            'password': '',
        },
    }
    response = requests.post('https://api.moltin.com/v2/customers', headers=headers, json=payload)
    response.raise_for_status()


def get_product_stock(product_id, client_id, client_secret):
    token = check_and_get_moltin_token(client_id, client_secret)
    headers = {
        'Authorization': f'Bearer {token}',
    }
    product_stock_url = f'https://api.moltin.com/v2/inventories/{product_id}'
    response = requests.get(product_stock_url, headers=headers)
    response.raise_for_status()
    stock = response.json()['data']

    return stock


def get_product_image(client_id, client_secret):
    token = check_and_get_moltin_token(client_id, client_secret)
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get('https://api.moltin.com/v2/files', headers=headers)
    response.raise_for_status()
    raw_file_data = response.json()['data']
    file_data, *_ = raw_file_data

    return file_data['link']['href']


def get_product(product_id, client_id, client_secret):
    token = check_and_get_moltin_token(client_id, client_secret)
    headers = {
        'Authorization': f'Bearer {token}',
    }
    products_url = f'https://api.moltin.com/v2/products/{product_id}'
    response = requests.get(products_url, headers=headers)
    response.raise_for_status()
    product = response.json()['data']

    return product


def delete_cart_item(chat_id, item_id, client_id, client_secret):
    token = check_and_get_moltin_token(client_id, client_secret)
    headers = {
        'Authorization': f'Bearer {token}',
    }
    cart_url = f'https://api.moltin.com/v2/carts/{chat_id}/items/{item_id}'
    response = requests.delete(cart_url, headers=headers)
    response.raise_for_status()

    return response.json()


def get_cart_items(chat_id, client_id, client_secret):
    token = check_and_get_moltin_token(client_id, client_secret)
    headers = {
        'Authorization': f'Bearer {token}',
    }
    cart_items_url = f'https://api.moltin.com/v2/carts/{chat_id}/items'
    response = requests.get(cart_items_url, headers=headers)
    response.raise_for_status()

    return response.json()


def add_product_to_cart(chat_id, product_sku, item_quantity, client_id, client_secret):
    token = check_and_get_moltin_token(client_id, client_secret)
    headers = {
        'Authorization': f'Bearer {token}',
    }
    payload = {
        'data': {
            'sku': product_sku,
            'type': 'cart_item',
            'quantity': item_quantity,
        },
    }
    cart_url = f'https://api.moltin.com/v2/carts/{chat_id}/items'
    response = requests.post(cart_url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()
