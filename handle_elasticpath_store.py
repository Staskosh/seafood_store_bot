import os

import requests


def get_moltin_token():
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    client_id = os.getenv('MOLTIN_CLIENT_ID')
    client_secret = os.getenv('MOLTIN_CLIENT_SECRET_KEY')
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    response = requests.post('https://api.moltin.com/oauth/access_token', headers=headers, data=payload)
    response.raise_for_status()
    return response.json()['access_token']


def get_products():
    token = get_moltin_token()
    headers = {
        'Authorization': f'Bearer {token}',
    }
    products_url = 'https://api.moltin.com/v2/products'
    response = requests.get(products_url, headers=headers)
    response.raise_for_status()
    products = response.json()['data']

    return products


def create_customer(email):
    token = get_moltin_token()
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


def get_product_stock(product_id):
    token = get_moltin_token()
    headers = {
        'Authorization': f'Bearer {token}',
    }
    product_stock_url = f'https://api.moltin.com/v2/inventories/{product_id}'
    response = requests.get(product_stock_url, headers=headers)
    response.raise_for_status()
    stock = response.json()['data']

    return stock


def get_product_image():
    token = get_moltin_token()
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get('https://api.moltin.com/v2/files', headers=headers)
    response.raise_for_status()
    raw_file_data = response.json()['data']
    file_data, *_ = raw_file_data

    return file_data['link']['href']


def get_product(product_id):
    token = get_moltin_token()
    headers = {
        'Authorization': f'Bearer {token}',
    }
    products_url = f'https://api.moltin.com/v2/products/{product_id}'
    response = requests.get(products_url, headers=headers)
    response.raise_for_status()
    product = response.json()['data']

    return product


def delete_cart_item(chat_id, item_id):
    token = get_moltin_token()
    headers = {
        'Authorization': f'Bearer {token}',
    }
    cart_url = f'https://api.moltin.com/v2/carts/{chat_id}/items/{item_id}'
    response = requests.delete(cart_url, headers=headers)
    response.raise_for_status()

    return response.json()


def get_cart_items(chat_id):
    token = get_moltin_token()
    headers = {
        'Authorization': f'Bearer {token}',
    }
    cart_items_url = f'https://api.moltin.com/v2/carts/{chat_id}/items'
    response = requests.get(cart_items_url, headers=headers)
    response.raise_for_status()

    return response.json()


def add_product_to_cart(chat_id, product_sku, item_quantity):
    token = get_moltin_token()
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
