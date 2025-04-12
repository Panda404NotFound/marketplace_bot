#!/usr/bin/env python3
"""
Парсер для маркетплейса Яндекс.Маркет.
"""
import requests
import json
import re
import sys
import time
import random
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Создание объекта UserAgent для генерации случайных User-Agent
ua = UserAgent()

# Пример URL товара Yandex Market
PRODUCT_URL = "https://market.yandex.ru/product--ckovoroda-s-kryshkoi-alwa-26-sm-litaia-s-antiprigarnym-pokrytiem-glubokaia-tsvet-mramor/1045734577?sku=103807672220&uniqueId=28141458&do-waremd5=pu9f7cnsQkmOoIhJeGJaTw&cpc=CDmIaXQJ2nfqqHEN8sTFNX2bmdBfHeylm-8X1f1xACbYhoy57yJOnZ2FowTk6PeBFQiuNoIJLgSAfolIKBB3nR4akx-rTbPcOcRNplPT_U8IzJOS8Rgxiq-lolCaJjqENJKhkOFDcajuzFrVALBOXecAw6mm64OCIS4rqpLx_6Yct-tDThMQKQ5es_38AL_WsdyBVBtc9BBuxS-I21xVQthuZBnLKT6ZStP-vpCU-uFtySte-K_QRg%2C%2C"


class YandexMarketParser:
    """Парсер для маркетплейса Яндекс.Маркет."""
    
    def __init__(self):
        # Параметры для повторных попыток при обнаружении капчи
        self.max_retries = 3
        
    def get_random_headers(self):
        """Получить случайный набор заголовков с использованием fake_useragent."""
        # Создаем базовый заголовок
        headers = {
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        # Добавляем случайный User-Agent с использованием библиотеки fake_useragent
        try:
            # Используем random метод для получения полностью случайного User-Agent
            headers['User-Agent'] = ua.random
        except Exception as e:
            # Fallback в случае ошибки с fake_useragent
            print(f"Ошибка при генерации User-Agent: {e}")
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36'
        
        return headers
    
    def get_page_content(self, url):
        """Получить HTML-контент страницы."""
        try:
            # Получаем новый случайный заголовок для каждого запроса
            headers = self.get_random_headers()
            
            # Выполняем запрос
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Устанавливаем кодировку
            response.encoding = 'utf-8'
            
            return response.text
        except requests.RequestException as e:
            print(f"Ошибка при получении страницы: {e}")
            return None
    
    def get_marketplace_name(self):
        """Получить название маркетплейса."""
        return "Яндекс.Маркет"
    
    def parse(self, url=None):
        """
        Парсинг данных о товаре с Яндекс.Маркета.
        
        Args:
            url: URL страницы товара (если не указан, используется PRODUCT_URL)
            
        Returns:
            Словарь с данными о товаре:
            {
                'title': название товара,
                'image_url': URL изображения товара,
                'price': цена товара (если доступна),
                'description': описание товара (если доступно),
                'marketplace': идентификатор маркетплейса,
                'captcha_detected': флаг обнаружения капчи
            }
        """
        if url is None:
            url = PRODUCT_URL
        
        # Логика повторных попыток с задержкой при обнаружении капчи
        retries = 0
        while retries < self.max_retries:
            html_content = self.get_page_content(url)
            if not html_content:
                return {
                    'title': "Ошибка при получении страницы",
                    'image_url': None,
                    'marketplace': self.get_marketplace_name(),
                    'error': True
                }
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Проверяем наличие CAPTCHA
            if "Подтвердите, что запросы отправляли вы" in html_content:
                retries += 1
                if retries < self.max_retries:
                    # Генерируем случайную задержку от 5 до 10 секунд
                    delay = random.uniform(5, 10)
                    print(f"\n❌ ОБНАРУЖЕНА CAPTCHA! Повторная попытка {retries}/{self.max_retries} через {delay:.2f} секунд...")
                    time.sleep(delay)
                    continue
                else:
                    return {
                        'title': "Подтвердите, что запросы отправляли вы, а не робот",
                        'image_url': None,
                        'marketplace': self.get_marketplace_name(),
                        'captcha_detected': True
                    }
            
            # Если капча не обнаружена, продолжаем парсинг
            break
        
        result = {
            'title': "Название не найдено",
            'image_url': None,
            'price': None,
            'description': None,
            'marketplace': self.get_marketplace_name(),
            'captcha_detected': False
        }
        
        # Извлечение названия товара
        title_element = soup.select_one('h1')
        if title_element:
            result['title'] = title_element.text.strip()
        
        # Пытаемся найти данные в JSON-LD
        json_ld = soup.select('script[type="application/ld+json"]')
        for script in json_ld:
            try:
                data = json.loads(script.string)
                if '@type' in data and data['@type'] == 'Product':
                    if 'name' in data:
                        result['title'] = data['name']
                    if 'image' in data:
                        if isinstance(data['image'], list) and data['image']:
                            result['image_url'] = data['image'][0]
                        else:
                            result['image_url'] = data['image']
                    # Проверяем наличие акционной цены в JSON-LD
                    if 'offers' in data:
                        if 'lowPrice' in data['offers']:  # Самая низкая цена в предложениях
                            result['price'] = data['offers']['lowPrice']
                        elif 'price' in data['offers']:  # Обычная цена
                            result['price'] = data['offers']['price']
                    if 'description' in data:
                        result['description'] = data['description']
                    break
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Если изображение не найдено, ищем в HTML с использованием разных селекторов
        if not result['image_url']:
            image_selectors = [
                '.cia-cs img', 
                '.n-gallery__image', 
                'img._2gUfn', 
                'img[src*="marketpic"]',
                'img.preview-picture',
                'img[src*="thumbnail"]',
                '.image img',
                'img.logo-image',
                'img.image',
                'img[data-tid="bb42d11f"]'
            ]
            
            for selector in image_selectors:
                img_elements = soup.select(selector)
                for img in img_elements:
                    if img.has_attr('src'):
                        result['image_url'] = img['src']
                        break
                    elif img.has_attr('data-src'):
                        result['image_url'] = img['data-src']
                        break
                
                if result['image_url']:
                    break
        
        # Если цена не найдена, ищем в HTML
        if not result['price']:
            # Сначала ищем акционную цену
            discount_price_selectors = [
                'span[data-auto="offer-price-value"]',
                '.Price-root_discount',
                'span.Price_role_discount',
                'span._3NaXx._33ZFz',
                'span[data-auto="price-value"].Price_discount',
                'span[data-tid="c3eacd93"].Price_discount'
            ]
            
            # Проверяем селекторы со скидочной ценой
            for selector in discount_price_selectors:
                price_element = soup.select_one(selector)
                if price_element:
                    try:
                        # Удаление всех нецифровых символов, кроме точки
                        price_text = re.sub(r'[^\d.]', '', price_element.text.replace(',', '.'))
                        result['price'] = float(price_text)
                        print(f"Найдена акционная цена: {result['price']}")
                        break
                    except (ValueError, TypeError):
                        pass
            
            # Если акционная цена не найдена, ищем обычную цену
            if not result['price']:
                price_selectors = [
                    'span[data-auto="price-value"]',
                    '.price-value',
                    '.price_value',
                    'span._1f9xN',
                    'span._3NaXx._3kWlK',
                    'div[data-tid="c3eacd93"]',
                    'span[data-auto="mainPrice"]'
                ]
                
                for selector in price_selectors:
                    price_element = soup.select_one(selector)
                    if price_element:
                        try:
                            # Удаление всех нецифровых символов, кроме точки
                            price_text = re.sub(r'[^\d.]', '', price_element.text.replace(',', '.'))
                            result['price'] = float(price_text)
                            print(f"Найдена обычная цена: {result['price']}")
                            break
                        except (ValueError, TypeError):
                            pass
        
        # Если описание не найдено, ищем в HTML
        if not result['description']:
            desc_selectors = [
                'div[data-auto="product-description"]',
                '.n-product-description-text',
                'div[data-tid="eee60a47"]',
                'div.specifications-tab'
            ]
            
            for selector in desc_selectors:
                desc_element = soup.select_one(selector)
                if desc_element:
                    result['description'] = desc_element.text.strip()
                    break
        
        return result

    def print_result(self, result):
        """Вывести результат парсинга в консоль."""
        print("\n" + "="*50)
        print(f"Маркетплейс: {result['marketplace']}")
        print("="*50)
        
        if result.get('captcha_detected', False):
            print("\n❌ ОБНАРУЖЕНА CAPTCHA! Попробуйте позже или с другого IP-адреса.")
            return
            
        if result.get('error', False):
            print("\n❌ ОШИБКА ПРИ ПОЛУЧЕНИИ СТРАНИЦЫ!")
            return
            
        print(f"\n📌 Название товара: {result['title']}")
        
        if result['image_url']:
            print(f"\n🖼️ URL изображения: {result['image_url']}")
        else:
            print("\n🖼️ Изображение не найдено")
            
        if result['price']:
            print(f"\n💰 Цена: {result['price']} ₽")
        else:
            print("\n💰 Цена не найдена")
            
        if result['description']:
            print(f"\n📝 Описание: {result['description'][:200]}...")
        else:
            print("\n📝 Описание не найдено")
            
        print("\n" + "="*50)
            

def main():
    # Создаем экземпляр парсера
    parser = YandexMarketParser()
    
    # Определяем URL для парсинга
    url = PRODUCT_URL
    
    # Если переданы аргументы командной строки, используем первый аргумент как URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    print(f"\n🔍 Парсим страницу: {url}")
    
    # Парсим страницу
    result = parser.parse(url)
    
    # Выводим результат
    parser.print_result(result)


if __name__ == "__main__":
    main()
