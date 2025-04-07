import re
from config.config import MARKETPLACES

def identify_marketplace(url):
    """Определить маркетплейс по URL."""
    if 'wildberries.ru' in url:
        return 'wildberries'
    elif 'ozon.ru' in url:
        return 'ozon'
    elif 'market.yandex.ru' in url:
        return 'yandex_market'
    else:
        return None

def is_valid_marketplace_url(url):
    """Проверить, является ли URL действительным URL маркетплейса."""
    marketplace = identify_marketplace(url)
    if marketplace:
        # Проверка на формат URL
        if marketplace == 'wildberries':
            return bool(re.match(r'https?://www\.wildberries\.ru/.*', url))
        elif marketplace == 'ozon':
            return bool(re.match(r'https?://www\.ozon\.ru/.*', url))
        elif marketplace == 'yandex_market':
            return bool(re.match(r'https?://market\.yandex\.ru/.*', url))
    return False

def parse_wildberries_product(url):
    """
    Парсинг товара с Wildberries.
    
    TODO: Реализовать парсинг с использованием библиотеки requests и BeautifulSoup.
    Сейчас просто заглушка.
    """
    # Заглушка
    return {
        'marketplace': 'wildberries',
        'title': 'Товар с Wildberries',
        'description': 'Описание товара с Wildberries',
        'price': 1000.0,
        'image_url': 'https://example.com/image.jpg',
        'url': url,
    }

def parse_ozon_product(url):
    """
    Парсинг товара с Ozon.
    
    TODO: Реализовать парсинг с использованием библиотеки requests и BeautifulSoup.
    Сейчас просто заглушка.
    """
    # Заглушка
    return {
        'marketplace': 'ozon',
        'title': 'Товар с Ozon',
        'description': 'Описание товара с Ozon',
        'price': 1500.0,
        'image_url': 'https://example.com/image.jpg',
        'url': url,
    }

def parse_yandex_market_product(url):
    """
    Парсинг товара с Яндекс Маркета.
    
    TODO: Реализовать парсинг с использованием библиотеки requests и BeautifulSoup.
    Сейчас просто заглушка.
    """
    # Заглушка
    return {
        'marketplace': 'yandex_market',
        'title': 'Товар с Яндекс Маркета',
        'description': 'Описание товара с Яндекс Маркета',
        'price': 2000.0,
        'image_url': 'https://example.com/image.jpg',
        'url': url,
    }

def parse_product_from_url(url):
    """Парсинг товара по URL."""
    marketplace = identify_marketplace(url)
    if not marketplace:
        return None
    
    if marketplace == 'wildberries':
        return parse_wildberries_product(url)
    elif marketplace == 'ozon':
        return parse_ozon_product(url)
    elif marketplace == 'yandex_market':
        return parse_yandex_market_product(url)
    else:
        return None 