# Telegram Бот-Маркетплейс

Telegram бот для создания персонального маркетплейса, позволяющий пользователям добавлять товары из Wildberries, Ozon и Яндекс Маркета, просматривать свою корзину и оформлять заказы.

## Функциональность

- Регистрация пользователей
- Добавление товаров по ссылкам с популярных маркетплейсов
- Управление корзиной
- Оформление и отслеживание заказов
- Удобное Inline-меню для навигации

## Структура проекта

```
marketplace_bot/
├── config/             # Настройки бота
├── database/           # Работа с базой данных
├── handlers/           # Обработчики команд и сообщений
├── keyboards/          # Клавиатуры и меню
├── models/             # Модели данных
├── services/           # Внешние сервисы
├── utils/              # Вспомогательные функции
└── main.py             # Точка входа
```

## Требования

- Python 3.7+
- aiogram
- SQLAlchemy
- python-dotenv

## Установка и запуск

1. Клонируйте репозиторий:

```bash
git clone https://github.com/yourusername/marketplace-bot.git
cd marketplace-bot
```

2. Установите зависимости:

```bash
pip install -r marketplace_bot/requirements.txt
```

3. Создайте файл `.env` на основе `.env.example` и добавьте в него свой токен бота:

```bash
cp .env.example .env
# Отредактируйте .env и добавьте токен бота
```

4. Запустите бота:

```bash
python -m marketplace_bot.main
```

## Использование

1. Откройте бота в Telegram и нажмите `/start`
2. Следуйте инструкциям для регистрации
3. Используйте встроенное меню для навигации
4. Чтобы добавить товар в корзину, отправьте ссылку на товар из поддерживаемого маркетплейса

## Заметки для разработчиков

В текущей версии бота многие функции (парсинг товаров, обработка оплаты и т.д.) реализованы в виде заглушек и могут быть доработаны в будущем.

## Лицензия

MIT 