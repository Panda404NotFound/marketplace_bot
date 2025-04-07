from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from database.database import get_cart_items, get_orders, remove_from_cart, create_order, cancel_order
from config.config import DEFAULT_DELIVERY_ADDRESS
from keyboards.keyboards import get_cart_menu, get_back_menu, get_payment_methods, get_orders_to_delete, get_confirmation_keyboard, get_main_menu

class PaymentStates(StatesGroup):
    """Состояния для оплаты заказов."""
    waiting_for_payment_method = State()

async def process_cart(callback_query: types.CallbackQuery):
    """Обработчик для перехода в раздел 'Моя корзина'."""
    await callback_query.answer()
    
    await callback_query.message.edit_text(
        "🛒 <b>Моя корзина</b>\n\n"
        "В этом разделе вы можете управлять товарами в вашей корзине, "
        "оформлять и оплачивать заказы.",
        reply_markup=get_cart_menu(),
        parse_mode='HTML'
    )

async def process_my_orders(callback_query: types.CallbackQuery):
    """Обработчик для просмотра товаров в корзине."""
    await callback_query.answer()
    
    user_id = callback_query.from_user.id
    cart_items = get_cart_items(user_id)
    
    if not cart_items:
        cart_text = "🛒 <b>Моя корзина</b>\n\nВаша корзина пуста."
    else:
        cart_text = "🛒 <b>Товары в корзине</b>\n\n"
        total_amount = 0
        
        for i, item in enumerate(cart_items, 1):
            product = item['product']
            quantity = item['quantity']
            size = item['size'] or "Не указан"
            color = item['color'] or "Не указан"
            item_price = product.price * quantity
            total_amount += item_price
            
            cart_text += (
                f"<b>{i}. {product.title}</b>\n"
                f"Цена: {product.price} ₽ x {quantity} = {item_price} ₽\n"
                f"Размер: {size}\n"
                f"Цвет: {color}\n\n"
            )
        
        cart_text += f"<b>Итого: {total_amount} ₽</b>"
    
    await callback_query.message.edit_text(
        cart_text,
        reply_markup=get_back_menu(),
        parse_mode='HTML'
    )

async def process_delete_order(callback_query: types.CallbackQuery):
    """Обработчик для удаления заказов."""
    await callback_query.answer()
    
    user_id = callback_query.from_user.id
    cart_items = get_cart_items(user_id)
    
    if not cart_items:
        await callback_query.message.edit_text(
            "🛒 <b>Удаление товаров</b>\n\nВаша корзина пуста.",
            reply_markup=get_back_menu(),
            parse_mode='HTML'
        )
        return
    
    # Преобразуем товары в формат для клавиатуры
    orders_for_keyboard = []
    for item in cart_items:
        product = item['product']
        quantity = item['quantity']
        price = product.price * quantity
        
        orders_for_keyboard.append({
            'id': item['id'],  # ID записи в корзине
            'total_amount': price
        })
    
    await callback_query.message.edit_text(
        "🛒 <b>Удаление товаров</b>\n\n"
        "Выберите товар, который хотите удалить из корзины:",
        reply_markup=get_orders_to_delete(orders_for_keyboard),
        parse_mode='HTML'
    )

async def process_remove_order(callback_query: types.CallbackQuery):
    """Обработчик для подтверждения удаления товара из корзины."""
    await callback_query.answer()
    
    # Извлекаем ID товара из callback_data
    cart_item_id = int(callback_query.data.split('_')[-1])
    
    await callback_query.message.edit_text(
        "🗑️ <b>Подтверждение удаления</b>\n\n"
        "Вы уверены, что хотите удалить этот товар из корзины?",
        reply_markup=get_confirmation_keyboard("remove_cart_item", cart_item_id),
        parse_mode='HTML'
    )

async def process_confirm_remove_cart_item(callback_query: types.CallbackQuery):
    """Обработчик для подтверждения удаления товара из корзины."""
    await callback_query.answer()
    
    # Извлекаем ID товара из callback_data
    cart_item_id = int(callback_query.data.split('_')[-1])
    
    user_id = callback_query.from_user.id
    success = remove_from_cart(user_id, cart_item_id)
    
    if success:
        await callback_query.message.edit_text(
            "✅ <b>Товар успешно удален из корзины</b>",
            reply_markup=get_cart_menu(),
            parse_mode='HTML'
        )
    else:
        await callback_query.message.edit_text(
            "❌ <b>Не удалось удалить товар из корзины</b>\n\n"
            "Пожалуйста, попробуйте снова.",
            reply_markup=get_cart_menu(),
            parse_mode='HTML'
        )

async def process_pay_orders(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик для перехода к оплате заказов."""
    await callback_query.answer()
    
    user_id = callback_query.from_user.id
    cart_items = get_cart_items(user_id)
    
    if not cart_items:
        await callback_query.message.edit_text(
            "🛒 <b>Оплата заказов</b>\n\nВаша корзина пуста.",
            reply_markup=get_back_menu(),
            parse_mode='HTML'
        )
        return
    
    # Рассчитываем общую стоимость
    total_amount = 0
    for item in cart_items:
        product = item['product']
        quantity = item['quantity']
        total_amount += product.price * quantity
    
    # Сохраняем данные о заказе в состояние
    await state.update_data(
        cart_items=cart_items,
        total_amount=total_amount,
        delivery_address=DEFAULT_DELIVERY_ADDRESS
    )
    
    payment_text = (
        f"💰 <b>Оплата заказа</b>\n\n"
        f"Общая стоимость: {total_amount} ₽\n"
        f"Адрес доставки: {DEFAULT_DELIVERY_ADDRESS}\n\n"
        f"Выберите способ оплаты:"
    )
    
    await callback_query.message.edit_text(
        payment_text,
        reply_markup=get_payment_methods(),
        parse_mode='HTML'
    )
    
    # Устанавливаем состояние ожидания выбора метода оплаты
    await PaymentStates.waiting_for_payment_method.set()

async def process_payment_method(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик для выбора метода оплаты."""
    await callback_query.answer()
    
    # Получаем метод оплаты из callback_data
    payment_method = callback_query.data.replace('pay_', '')
    
    # Получаем данные о заказе из состояния
    data = await state.get_data()
    delivery_address = data.get('delivery_address')
    
    # Создаем заказ
    user_id = callback_query.from_user.id
    order_id = create_order(
        user_id=user_id,
        delivery_address=delivery_address,
        payment_method=payment_method
    )
    
    if order_id:
        # Заказ успешно создан
        await callback_query.message.edit_text(
            f"✅ <b>Заказ оформлен</b>\n\n"
            f"Номер заказа: {order_id}\n"
            f"Метод оплаты: {payment_method.upper()}\n"
            f"Адрес доставки: {delivery_address}\n\n"
            f"<i>Это тестовый бот, оплата не производится.</i>\n"
            f"<i>В реальном боте здесь была бы интеграция с платежной системой.</i>",
            reply_markup=get_main_menu(),
            parse_mode='HTML'
        )
    else:
        # Ошибка при создании заказа
        await callback_query.message.edit_text(
            "❌ <b>Ошибка при оформлении заказа</b>\n\n"
            "Пожалуйста, попробуйте снова.",
            reply_markup=get_cart_menu(),
            parse_mode='HTML'
        )
    
    # Завершаем состояние
    await state.finish()

async def process_cancel_action(callback_query: types.CallbackQuery):
    """Обработчик для отмены действия."""
    await callback_query.answer()
    
    await callback_query.message.edit_text(
        "❌ <b>Действие отменено</b>",
        reply_markup=get_cart_menu(),
        parse_mode='HTML'
    )

def register_cart_handlers(dp):
    """Регистрация обработчиков раздела 'Моя корзина'."""
    dp.register_callback_query_handler(process_cart, lambda c: c.data == "cart")
    dp.register_callback_query_handler(process_my_orders, lambda c: c.data == "my_orders")
    dp.register_callback_query_handler(process_delete_order, lambda c: c.data == "delete_order")
    dp.register_callback_query_handler(
        process_remove_order,
        lambda c: c.data.startswith("remove_order_")
    )
    dp.register_callback_query_handler(
        process_confirm_remove_cart_item,
        lambda c: c.data.startswith("confirm_remove_cart_item_")
    )
    dp.register_callback_query_handler(process_pay_orders, lambda c: c.data == "pay_orders")
    dp.register_callback_query_handler(
        process_payment_method,
        lambda c: c.data in ["pay_apple", "pay_google", "pay_card"],
        state=PaymentStates.waiting_for_payment_method
    )
    dp.register_callback_query_handler(process_cancel_action, lambda c: c.data == "cancel_action") 