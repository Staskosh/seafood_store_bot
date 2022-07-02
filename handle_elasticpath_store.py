import os

import requests


def get_moltin_token():
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    client_id = os.getenv('MOLTIN_CLIENT_ID')
    client_secret = os.getenv('MOLTIN_CLIENT_SECRET_KEY')
    data = f'client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials'
    response = requests.post('https://api.moltin.com/oauth/access_token', headers=headers, data=data)
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

    json_data = {
        'data': {
            'type': 'customer',
            'name': email,
            'email': email,
            'password': '',
        },
    }

    response = requests.post('https://api.moltin.com/v2/customers', headers=headers, json=json_data)
    response.raise_for_status()


def get_product_stock(product_id):
    token = get_moltin_token()
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(f'https://api.moltin.com/v2/inventories/{product_id}', headers=headers)
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


def delete_cart_item(item_id):
    token = get_moltin_token()
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.delete(f'https://api.moltin.com/v2/carts/abc/items/{item_id}', headers=headers)
    response.raise_for_status()

    return response.json()


def get_cart_items():
    token = get_moltin_token()
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(f'https://api.moltin.com/v2/carts/abc/items', headers=headers)
    response.raise_for_status()

    return response.json()


def add_product_to_cart(product_sku, item_quantity):
    token = get_moltin_token()
    headers = {
        'Authorization': f'Bearer {token}',
    }
    json_data = {
        'data': {
            'sku': product_sku,
            'type': 'cart_item',
            'quantity': item_quantity,
        },
    }
    response = requests.post('https://api.moltin.com/v2/carts/abc/items', headers=headers, json=json_data)
    response.raise_for_status()

    return response.json()
