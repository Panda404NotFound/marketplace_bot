"""
Модуль для отправки уведомлений администратору и в группу.
"""

import os
from aiogram import Bot
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Получение идентификатора чата из переменных окружения
CHAT_ID = os.getenv('CHAT_ID')
if not CHAT_ID:
    raise ValueError("Не установлен CHAT_ID. Создайте файл .env с переменной CHAT_ID")

# Получение имени менеджера
MANAGER_NAME = os.getenv('MANAGER_NAME', 'manager')


async def send_order_to_chat(bot: Bot, user_id: int, username: Optional[str], order_data: Dict[str, Any]) -> bool:
    """
    Отправляет информацию о заказе в групповой чат.
    
    Args:
        bot: Экземпляр бота
        user_id: ID пользователя, сделавшего заказ
        username: Имя пользователя (@username) в Telegram
        order_data: Данные о заказе
        
    Returns:
        bool: True, если сообщение отправлено успешно
    """
    try:
        # Формируем текст сообщения
        message_text = f"📦 <b>НОВЫЙ ОПЛАЧЕННЫЙ ЗАКАЗ</b>\n\n"
        
        # Информация о пользователе
        user_info = f"👤 <b>Пользователь:</b> {user_id}"
        if username:
            user_info += f" (@{username})"
        message_text += f"{user_info}\n\n"
        
        # Информация о заказе
        message_text += f"🧾 <b>Номер заказа:</b> {order_data['order_id']}\n"
        
        # Преобразуем метод оплаты для лучшего отображения
        payment_method = order_data['payment_method'].upper()
        payment_method_display = {
            'MIR': 'Карта МИР',
            'VISA_MC': 'VISA/MASTERCARD',
            'APPLE': 'Apple Pay'
        }.get(payment_method, payment_method)
        
        # Получаем статус заказа
        status = order_data.get('status', 'paid')
        status_display = {
            'new': 'Ожидает подтверждения',
            'paid': 'Оплачен',
            'shipped': 'Отправлен',
            'delivered': 'Доставлен',
            'cancelled': 'Отменен'
        }.get(status, 'Оплачен')
        
        message_text += f"💳 <b>Способ оплаты:</b> {payment_method_display}\n"
        message_text += f"🚚 <b>Адрес доставки:</b> {order_data['delivery_address']}\n"
        message_text += f"🔹 <b>Статус заказа:</b> {status_display}\n\n"
        
        # Товары в заказе
        message_text += f"📋 <b>Товары в заказе:</b>\n\n"
        
        total_amount = 0
        for i, item in enumerate(order_data['items'], 1):
            try:
                product = item['product']
                quantity = item['quantity']
                size = item['size'] or "Не указан"
                color = item['color'] or "Не указаны"
                product_url = product.get('url', '')
                
                # Получаем информацию о маркетплейсе
                marketplace = product.get('marketplace', '').lower()
                marketplace_name = {
                    'wildberries': 'Wildberries',
                    'ozon': 'Ozon',
                    'yandex_market': 'Яндекс.Маркет'
                }.get(marketplace, product.get('marketplace', 'Неизвестно'))
                
                # Расчет цены товара
                product_price = product.get('price', 0)
                item_price = product_price * quantity
                total_amount += item_price
                
                # Формируем название товара со ссылкой, если URL доступен
                product_title = product.get('title', 'Без названия')
                if product_url:
                    product_title_with_link = f'<a href="{product_url}">{product_title}</a>'
                else:
                    product_title_with_link = f'<b>{product_title}</b>'
                
                message_text += (
                    f"{i}. {product_title_with_link}\n"
                    f"   Маркетплейс: {marketplace_name}\n"
                    f"   Цена: {product_price} ₽ x {quantity} = {item_price} ₽\n"
                    f"   Размер: {size}\n"
                    f"   Примечания: {color}\n\n"
                )
            except Exception as item_error:
                print(f"Ошибка при обработке товара: {item_error}")
                message_text += f"{i}. <b>Информация о товаре недоступна</b>\n\n"
        
        message_text += f"<b>Итого:</b> {total_amount} ₽\n\n"
        
        # Отправляем сообщение в чат с отключенным предпросмотром ссылок
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message_text,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        return True
    
    except Exception as e:
        print(f"Ошибка при отправке сообщения в чат: {e}")
        return False 