import re
from config.config import MARKETPLACES

# Импортируем классы парсеров
from parser.wb_parser import extract_nm_id_from_url, get_product_info_from_card_api, parse_and_display_product_info
from parser.yandex_parser import YandexMarketParser

def identify_marketplace(url):
    """Определить маркетплейс по URL."""
    # Сначала пытаемся извлечь URL из текста, если пользователь отправил его с текстом
    url_match = re.search(r'https?://\S+', url)
    if url_match:
        url = url_match.group(0)
        
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
    # Извлекаем URL из текста, если пользователь отправил его с текстом
    url_match = re.search(r'https?://\S+', url)
    if url_match:
        url = url_match.group(0)
    
    marketplace = identify_marketplace(url)
    if marketplace:
        # Проверка на формат URL
        if marketplace == 'wildberries':
            return bool(re.match(r'https?://(www\.)?wildberries\.ru/.*', url))
        elif marketplace == 'ozon':
            return bool(re.match(r'https?://(www\.)?ozon\.ru/.*', url))
        elif marketplace == 'yandex_market':
            return bool(re.match(r'https?://market\.yandex\.ru/.*', url))
    return False

def parse_wildberries_product(url):
    """
    Парсинг товара с Wildberries.
    
    Использует реальный парсер из wb_parser.py.
    """
    try:
        # Получаем ID товара из URL
        nm_id = extract_nm_id_from_url(url)
        
        if not nm_id:
            print("Не удалось извлечь ID товара из URL Wildberries")
            # Возвращаем заглушку, если не удалось извлечь ID
            return {
                'marketplace': 'wildberries',
                'title': 'Товар Wildberries',
                'description': 'Не удалось получить информацию о товаре',
                'price': 0.0,
                'image_url': None,
                'url': url,
                'available_sizes': []
            }
        
        # Получаем информацию о товаре через Card API
        product_info = get_product_info_from_card_api(nm_id)
        
        if not product_info:
            print("Не удалось получить информацию о товаре Wildberries через Card API")
            # Возвращаем заглушку, если не удалось получить информацию
            return {
                'marketplace': 'wildberries',
                'title': 'Товар Wildberries',
                'description': 'Не удалось получить информацию о товаре',
                'price': 0.0,
                'image_url': None,
                'url': url,
                'available_sizes': []
            }
        
        # Формируем результат в нужном формате
        result = {
            'marketplace': 'wildberries',
            'title': product_info.get('name', 'Название не указано'),
            'description': product_info.get('description', ''),
            'url': url,
            'image_url': None  # Для Wildberries не используем изображения
        }
        
        # Обработка цены
        try:
            if 'salePriceU' in product_info:
                # Используем акционную цену (со скидкой), если она есть
                result['price'] = product_info['salePriceU'] / 100
            elif 'priceU' in product_info:
                # Если нет акционной цены, используем обычную цену
                result['price'] = product_info['priceU'] / 100
            else:
                result['price'] = 0
        except Exception as price_error:
            print(f"Ошибка при обработке цены: {price_error}")
            result['price'] = 0
            
        # Добавляем информацию о размерах и цветах
        try:
            sizes_info = []
            if 'sizes' in product_info and product_info['sizes']:
                for size_info in product_info['sizes']:
                    size_name = size_info.get('name', 'Размер не указан')
                    size_orig_name = size_info.get('origName', '')
                    
                    colors = []
                    if size_info.get('colors'):
                        colors = [color.get('name', 'Цвет не указан') for color in size_info['colors']]
                    
                    sizes_info.append({
                        'name': size_name,
                        'origName': size_orig_name,
                        'colors': colors
                    })
            
            result['available_sizes'] = sizes_info
        except Exception as sizes_error:
            print(f"Ошибка при обработке размеров: {sizes_error}")
            result['available_sizes'] = []
        
        return result
    except Exception as e:
        print(f"Ошибка при парсинге товара с Wildberries: {str(e)}")
        # Возвращаем заглушку в случае общей ошибки
        return {
            'marketplace': 'wildberries',
            'title': 'Товар Wildberries',
            'description': 'Произошла ошибка при получении информации о товаре',
            'price': 0.0,
            'image_url': None,
            'url': url,
            'available_sizes': []
        }

def parse_ozon_product(url):
    """
    Парсинг товара с Ozon.
    
    TODO: Функциональность для Ozon находится в разработке.
    """
    # Заглушка с указанием о недоступности маркетплейса
    return {
        'marketplace': 'ozon',
        'title': 'Товар с Ozon',
        'description': 'Магазин Ozon временно не поддерживается. Пожалуйста, используйте другие маркетплейсы.',
        'price': 0.0,
        'image_url': None,
        'url': url,
        'available_sizes': [],
        'error': True  # Флаг ошибки для блокировки оформления
    }

def parse_yandex_market_product(url):
    """
    Парсинг товара с Яндекс Маркета.
    
    Использует реальный парсер из yandex_parser.py.
    """
    try:
        # Создаем экземпляр парсера Яндекс.Маркета
        parser = YandexMarketParser()
        
        # Получаем информацию о товаре
        result = parser.parse(url)
        
        # Проверяем результат на ошибки
        if not result:
            print("Парсер Яндекс.Маркета вернул пустой результат")
            return get_yandex_market_fallback(url)
            
        if result.get('captcha_detected'):
            print("Обнаружена капча на странице Яндекс.Маркета")
            return get_yandex_market_fallback(url, "Товар не найден, попробуйте еще раз...")
            
        if result.get('error'):
            print("Произошла ошибка при парсинге Яндекс.Маркета")
            return get_yandex_market_fallback(url)
        
        # Преобразуем результат в нужный формат
        formatted_result = {
            'marketplace': 'yandex_market',
            'title': result.get('title', 'Название не указано'),
            'description': result.get('description', ''),
            'price': result.get('price', 0.0),
            'image_url': result.get('image_url'),
            'url': url,
            'available_sizes': []  # Яндекс.Маркет не предоставляет информацию о размерах
        }
        
        return formatted_result
    except Exception as e:
        print(f"Ошибка при парсинге товара с Яндекс.Маркета: {str(e)}")
        return get_yandex_market_fallback(url)

def get_yandex_market_fallback(url, reason="Не удалось получить информацию о товаре"):
    """Заглушка для товара Яндекс.Маркета в случае ошибок."""
    return {
        'marketplace': 'yandex_market',
        'title': 'Товар Яндекс.Маркета',
        'description': reason,
        'price': 0.0,
        'image_url': None,
        'url': url,
        'available_sizes': [],
        'error': True  # Добавляем флаг ошибки
    }

def parse_product_from_url(url):
    """Парсинг товара по URL."""
    try:
        # Извлекаем URL из текста, если пользователь отправил его с текстом
        url_match = re.search(r'https?://\S+', url)
        if url_match:
            url = url_match.group(0)
        
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
    except Exception as e:
        print(f"Ошибка при парсинге URL {url}: {str(e)}")
        return {
            'marketplace': 'unknown',
            'title': 'Товар не удалось обработать',
            'description': f'Произошла ошибка при обработке товара: {str(e)}',
            'price': 0.0,
            'image_url': None,
            'url': url,
            'available_sizes': [],
            'error': True
        } 