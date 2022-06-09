import logging
import os

import requests
from dotenv import load_dotenv


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


def get_product(headers):
    products_url = 'https://api.moltin.com/v2/products'
    response = requests.get(products_url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_cart():
    response = requests.get(f'https://api.moltin.com/v2/carts/abc', headers=headers)
    response.raise_for_status()
    return response.json()


def add_product_to_cart(headers):
    json_data = {
        'data': {
            'sku': '01',
            'type': 'cart_item',
            'quantity': 1,
        },
    }
    response = requests.post('https://api.moltin.com/v2/carts/abc/items', headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()


def main() -> None:
    load_dotenv()
    try:
        token = get_moltin_token()
        headers = {
            'Authorization': f'Bearer {token}',
        }
        get_product(headers)
        add_product_to_cart(headers)
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        logging.warning(e)


if __name__ == '__main__':
    main()
