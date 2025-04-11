import os
import re
import json
import requests
import time
import random
from dotenv import load_dotenv
from urllib.parse import urlparse
from fake_useragent import UserAgent

# Загрузка переменных из .env файла
load_dotenv()

# Создание объекта UserAgent для генерации случайных User-Agent
ua = UserAgent()

# Пример URL товара Wildberries
PRODUCT_URL = "https://www.wildberries.ru/catalog/194573148/detail.aspx?targetUrl=SG"

def extract_nm_id_from_url(url):
    """
    Извлекает nmID (ID товара) из URL Wildberries
    
    Пример URL: 
    https://www.wildberries.ru/catalog/194573148/detail.aspx?targetUrl=SG
    """
    # Вариант 1: использование регулярного выражения
    pattern = r'/catalog/(\d+)/detail'
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    
    # Вариант 2: парсинг пути URL
    path_parts = urlparse(url).path.split('/')
    for i, part in enumerate(path_parts):
        if part == "catalog" and i + 1 < len(path_parts):
            if path_parts[i + 1].isdigit():
                return path_parts[i + 1]
    
    # Возвращаем None, если не удалось извлечь ID
    return None

def get_product_info_from_card_api(nm_id):
    """
    Получает информацию о товаре через официальный публичный Card API
    
    nm_id: ID номенклатуры товара в системе Wildberries
    
    Реализует механизм повторных запросов с новым User-Agent при каждой попытке.
    """
    url = f"https://card.wb.ru/cards/detail?nm={nm_id}&appType=1&curr=rub&dest=-1257786"
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Генерируем новый случайный User-Agent при каждой попытке
            current_ua = ua.random
            
            print(f"Запрос к Card API: {url} (попытка {retry_count + 1}/{max_retries})")
            print(f"User-Agent: {current_ua[:30]}...")
            
            headers = {
                'User-Agent': current_ua,
                'Accept': 'application/json',
                'Origin': 'https://www.wildberries.ru',
                'Referer': f'https://www.wildberries.ru/catalog/{nm_id}/detail.aspx'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Код ответа Card API: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if not data.get("data") or not data["data"].get("products") or not data["data"]["products"]:
                    print(f"Информация о товаре с nmID {nm_id} не найдена в Card API")
                    return None
                
                product = data["data"]["products"][0]
                print(f"Информация о товаре получена из Card API: {product.get('name')}")
                return product
            else:
                print(f"Ошибка получения данных из Card API: {response.status_code}")
                retry_count += 1
                
                if retry_count < max_retries:
                    # Случайная задержка перед повторной попыткой от 1 до 3 секунд
                    delay = random.uniform(1, 3)
                    print(f"Повторная попытка через {delay:.2f} секунд...")
                    time.sleep(delay)
                else:
                    print("Исчерпано максимальное количество попыток")
                    return None
                
        except Exception as e:
            print(f"Ошибка при получении информации через Card API: {str(e)}")
            retry_count += 1
            
            if retry_count < max_retries:
                # Случайная задержка перед повторной попыткой от 2 до 5 секунд
                delay = random.uniform(2, 5)
                print(f"Повторная попытка через {delay:.2f} секунд...")
                time.sleep(delay)
            else:
                print("Исчерпано максимальное количество попыток")
                return None
    
    return None

def parse_and_display_product_info(url):
    """Анализирует URL, получает и отображает информацию о товаре"""
    
    # Извлечение nmID товара из URL
    nm_id = extract_nm_id_from_url(url)
    
    if not nm_id:
        print(f"Не удалось извлечь nmID товара из URL: {url}")
        return
    
    print(f"Извлечен nmID товара: {nm_id}")
    
    # Получаем информацию из Card API
    card_data = get_product_info_from_card_api(nm_id)
    
    # Проверяем, удалось ли получить данные
    if not card_data:
        print("Не удалось получить информацию о товаре")
        return
    
    # Формирование результата
    result = {
        "nm_id": card_data.get("id"),
        "name": card_data.get("name", "Название не указано"),
        "brand": card_data.get("brand", "Бренд не указан"),
    }
    
    # Цены
    if "priceU" in card_data:
        result["price"] = card_data["priceU"] / 100
    
    if "salePriceU" in card_data:
        result["discount_price"] = card_data["salePriceU"] / 100
    
    # Размеры и цвета
    if "sizes" in card_data and card_data["sizes"]:
        sizes = []
        for size_info in card_data["sizes"]:
            size_name = size_info.get("name", "Размер не указан")
            size_origName = size_info.get("origName", "")
            size_entry = {"name": size_name, "origName": size_origName}
            
            # Цвета для размера
            if size_info.get("colors"):
                colors = [color.get("name", "Цвет не указан") for color in size_info["colors"]]
                size_entry["colors"] = colors
            
            sizes.append(size_entry)
        
        result["available_sizes"] = sizes
    
    # Вывод информации в консоль
    print("\n=== Информация о товаре ===")
    print(f"nmID: {result.get('nm_id', 'Не указан')}")
    print(f"Название: {result.get('name', 'Не указано')}")
    print(f"Бренд: {result.get('brand', 'Не указан')}")
    
    if "price" in result:
        print(f"Цена: {result['price']}")
    
    if "discount_price" in result:
        print(f"Цена со скидкой: {result['discount_price']}")
    
    if "available_sizes" in result:
        print("\nДоступные размеры:")
        for size in result["available_sizes"]:
            if isinstance(size, dict):
                print(f"- {size.get('name', '')} ({size.get('origName', '')})")
                if "colors" in size:
                    print("  Доступные цвета:")
                    for color in size["colors"]:
                        print(f"  * {color}")
            else:
                print(f"- {size}")
    
    # Дополнительная информация (опционально)
    if "description" in card_data and card_data["description"]:
        result["description"] = card_data["description"]
        print("\nОписание:")
        print(result["description"])
    
    # Категория товара (опционально)
    if "subjectId" in card_data:
        result["category_id"] = card_data["subjectId"]
    
    print("\n=== Полная информация ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return result

if __name__ == "__main__":
    print("Парсер товаров Wildberries (официальный API)")
    print(f"Анализ URL: {PRODUCT_URL}")
    
    parse_and_display_product_info(PRODUCT_URL)