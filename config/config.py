import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Конфигурация бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("Не установлен токен бота. Создайте файл .env с переменной BOT_TOKEN")

# База данных
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///marketplace.db')

# Настройки администратора
ADMIN_ID = os.getenv('ADMIN_ID')

# Рабочие маркетплейсы
MARKETPLACES = {
    'wildberries': 'https://www.wildberries.ru',
    'ozon': 'https://www.ozon.ru',
    'yandex_market': 'https://market.yandex.ru'
}

# Адрес доставки
DEFAULT_DELIVERY_ADDRESS = "Nowesad" 