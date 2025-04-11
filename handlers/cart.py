from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from database.database import get_cart_items, get_orders, remove_from_cart, create_order, cancel_order, clear_cart
from config.config import DEFAULT_DELIVERY_ADDRESS
from keyboards.keyboards import get_cart_menu, get_back_menu, get_payment_methods, get_orders_to_delete, get_confirmation_keyboard, get_main_menu, get_payment_info_keyboard, get_user_orders_menu
from keyboards.fallback import save_navigation_state, reset_navigation_history

class PaymentStates(StatesGroup):
    """Состояния для оплаты заказов."""
    waiting_for_payment_method = State()

async def process_cart(callback_query: types.CallbackQuery):
    """Обработчик для перехода в раздел 'Моя корзина'."""
    try:
        await callback_query.answer()
        
        # Сохраняем текущее состояние навигации
        user_id = callback_query.from_user.id
        
        # При переходе к основным разделам лучше не сохранять историю
        # Это поможет избежать цикличных переходов между основными разделами
        if callback_query.data == "cart":
            reset_navigation_history(user_id)
        
        await save_navigation_state(user_id, 'cart')
        
        await callback_query.message.edit_text(
            "🛒 <b>Моя корзина</b>\n\n"
            "В этом разделе вы можете управлять товарами в вашей корзине, "
            "оформлять и оплачивать заказы.",
            reply_markup=get_cart_menu(),
            parse_mode='HTML'
        )
    except Exception as e:
        # print(f"Error in process_cart for user {user_id}: {e}")
        try:
            await callback_query.message.edit_text(
                "Произошла ошибка. Выберите действие:",
                reply_markup=get_main_menu()
            )
        except:
            pass

async def process_my_orders(callback_query: types.CallbackQuery):
    """Обработчик для просмотра товаров в корзине."""
    await callback_query.answer()
    
    # Сохраняем текущее состояние навигации
    user_id = callback_query.from_user.id
    await save_navigation_state(user_id, 'my_orders')
    
    cart_items = get_cart_items(user_id)
    
    if not cart_items:
        cart_text = "🛒 <b>Моя корзина</b>\n\nВаша корзина пуста."
        await callback_query.message.edit_text(
            cart_text,
            reply_markup=get_back_menu(),
            parse_mode='HTML'
        )
        return
    
    # Формируем текст о товарах в корзине
    cart_text = "🛒 <b>Товары в корзине</b>\n\n"
    total_amount = 0
    
    # Подготовим данные для клавиатуры
    orders_for_keyboard = []
    
    for i, item in enumerate(cart_items, 1):
        product = item['product']
        quantity = item['quantity']
        size = item['size'] or "Не указан"
        color = item['color'] or "Не указан"
        
        # Расчет цены с учетом количества
        item_price = product.price * quantity
        total_amount += item_price
        
        # Получаем информацию о маркетплейсе
        marketplace_name = {
            'wildberries': 'Wildberries',
            'ozon': 'Ozon',
            'yandex_market': 'Яндекс.Маркет'
        }.get(product.marketplace, product.marketplace)
        
        cart_text += (
            f"<b>{i}. {product.title}</b>\n"
            f"Маркетплейс: {marketplace_name}\n"
            f"Цена: {product.price} ₽ x {quantity} = {item_price} ₽\n"
            f"Размер: {size}\n"
            f"Цвет: {color}\n\n"
        )
        
        # Добавляем товар для клавиатуры
        orders_for_keyboard.append({
            'id': item['id'],
            'total_amount': item_price,
            'status': 'new'  # Все товары в корзине имеют статус 'new'
        })
    
    cart_text += f"<b>Итого: {total_amount} ₽</b>"
    
    # Создаем клавиатуру с кнопкой "Оплатить все заказы"
    keyboard = get_user_orders_menu(orders_for_keyboard, has_pay_all_button=True)
    
    # Упрощаем - отправляем только текст без изображений
    await callback_query.message.edit_text(
        cart_text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )

async def process_delete_order(callback_query: types.CallbackQuery):
    """Обработчик для удаления заказов."""
    await callback_query.answer()
    
    # Сохраняем текущее состояние навигации
    user_id = callback_query.from_user.id
    await save_navigation_state(user_id, 'delete_order')
    
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
    """Обработчик для перехода к оплате всех заказов одним платежом."""
    await callback_query.answer()
    
    # Сохраняем текущее состояние навигации
    user_id = callback_query.from_user.id
    await save_navigation_state(user_id, 'payment')
    
    cart_items = get_cart_items(user_id)
    
    if not cart_items:
        await callback_query.message.edit_text(
            "🛒 <b>Оплата заказов</b>\n\nВаша корзина пуста.",
            reply_markup=get_back_menu(),
            parse_mode='HTML'
        )
        return
    
    # Рассчитываем общую стоимость всех товаров в корзине
    total_amount = 0
    items_text = ""
    
    for i, item in enumerate(cart_items, 1):
        product = item['product']
        quantity = item['quantity']
        size = item['size'] or "Не указан"
        color = item['color'] or "Не указан"
        
        # Расчет цены с учетом количества
        item_price = product.price * quantity
        total_amount += item_price
        
        # Получаем информацию о маркетплейсе
        marketplace_name = {
            'wildberries': 'Wildberries',
            'ozon': 'Ozon',
            'yandex_market': 'Яндекс.Маркет'
        }.get(product.marketplace, product.marketplace)
        
        items_text += (
            f"<b>{i}. {product.title}</b>\n"
            f"Маркетплейс: {marketplace_name}\n"
            f"Цена: {product.price} ₽ x {quantity} = {item_price} ₽\n"
            f"Размер: {size}\n"
            f"Цвет: {color}\n\n"
        )
    
    # Сохраняем данные о заказе в состояние
    await state.update_data(
        cart_items=cart_items,
        total_amount=total_amount,
        delivery_address=DEFAULT_DELIVERY_ADDRESS,  # Гарантируем, что адрес всегда установлен
        is_combined_order=True  # Флаг, указывающий, что это объединенный заказ
    )
    
    payment_text = (
        f"💰 <b>Объединенная оплата заказов</b>\n\n"
        f"<b>Товары в корзине:</b>\n\n"
        f"{items_text}"
        f"<b>Общая стоимость:</b> {total_amount} ₽\n"
        f"<b>Адрес доставки:</b> {DEFAULT_DELIVERY_ADDRESS}\n\n"
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
    delivery_address = data.get('delivery_address', DEFAULT_DELIVERY_ADDRESS)  # Гарантируем значение по умолчанию
    is_combined_order = data.get('is_combined_order', False)  # Проверяем, это объединенный заказ или отдельный
    
    # Создаем заказ
    user_id = callback_query.from_user.id
    order_id = create_order(
        user_id=user_id,
        delivery_address=delivery_address,
        payment_method=payment_method
    )
    
    if order_id:
        payment_info = ""
        from admin.notification import MANAGER_NAME
        manager_username = f"@{MANAGER_NAME}"
        
        # Формируем информацию о платеже в зависимости от выбранного метода
        if payment_method == "mir":
            payment_info = (
                "💳 <b>Оплата картой МИР</b>\n\n"
                "Номер карты: 2202 2063 9165 2067\n"
                "Получатель: Наталья Наталья Наталья\n\n"
                f"После оплаты нажмите кнопку «✅ Оплатил»."
            )
        elif payment_method == "visa_mc":
            payment_info = (
                "💳 <b>Оплата картой Visa/Mastercard</b>\n\n"
                "Номер карты: 4455 6677 8899 0011\n"
                "Получатель: Наталья Произвольная Карта\n\n"
                f"После оплаты нажмите кнопку «✅ Оплатил»."
            )
        else:
            payment_info = "Выбран неизвестный метод оплаты."
        
        # Добавляем сообщение для пользователя
        payment_info += f"\n\nВаш заказ будет передан менеджеру {manager_username} после подтверждения оплаты."
            
        # Заказ успешно создан
        await callback_query.message.edit_text(
            f"✅ <b>Заказ оформлен</b>\n\n"
            f"Номер заказа: {order_id}\n"
            f"Метод оплаты: {payment_method.upper()}\n"
            f"Адрес доставки: {delivery_address}\n\n"
            f"{payment_info}",
            reply_markup=get_payment_info_keyboard(order_id),
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

async def process_paid_order(callback_query: types.CallbackQuery):
    """Обработчик для кнопки 'Оплатил'."""
    await callback_query.answer()
    
    # Получаем ID заказа из callback_data
    order_id = int(callback_query.data.split('_')[-1])
    
    # Получаем данные пользователя
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    # Получаем данные заказа - используем user_id из Telegram, а не из БД
    from database.database import get_order_details, update_order_status
    order_data = get_order_details(user_id, order_id)
    
    if not order_data:
        print(f"Ошибка: Не удалось найти информацию о заказе {order_id} для пользователя {user_id}")
        await callback_query.message.edit_text(
            "❌ <b>Ошибка</b>\n\n"
            "Не удалось найти информацию о заказе.",
            reply_markup=get_cart_menu(),
            parse_mode='HTML'
        )
        return
    
    # Обновляем статус заказа на "paid"
    success = update_order_status(order_id, "paid")
    if not success:
        print(f"Ошибка: Не удалось обновить статус заказа {order_id}")
        
    # Отправляем информацию о заказе в чат
    from admin.notification import send_order_to_chat
    success = await send_order_to_chat(
        bot=callback_query.bot,
        user_id=user_id,
        username=username,
        order_data=order_data
    )
    
    if success:
        await callback_query.message.edit_text(
            "✅ <b>Спасибо за оплату!</b>\n\n"
            "Информация о вашем заказе отправлена менеджеру.\n"
            "С вами свяжутся в ближайшее время для подтверждения заказа.",
            reply_markup=get_main_menu(),
            parse_mode='HTML'
        )
    else:
        await callback_query.message.edit_text(
            "❌ <b>Ошибка</b>\n\n"
            "Не удалось отправить информацию о заказе.\n"
            "Пожалуйста, свяжитесь с менеджером напрямую.",
            reply_markup=get_main_menu(),
            parse_mode='HTML'
        )

async def process_cancel_action(callback_query: types.CallbackQuery):
    """Обработчик для отмены действия."""
    await callback_query.answer()
    
    await callback_query.message.edit_text(
        "❌ <b>Действие отменено</b>",
        reply_markup=get_cart_menu(),
        parse_mode='HTML'
    )

async def process_remove_all_orders(callback_query: types.CallbackQuery):
    """Обработчик для подтверждения удаления всех товаров из корзины."""
    try:
        await callback_query.answer()
        
        await callback_query.message.edit_text(
            "🗑️ <b>Подтверждение удаления</b>\n\n"
            "Вы уверены, что хотите удалить ВСЕ товары из корзины?",
            reply_markup=get_confirmation_keyboard("remove_all_cart_items", 0),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Ошибка при обработке запроса на удаление всех товаров: {e}")
        try:
            await callback_query.message.edit_text(
                "Произошла ошибка. Выберите действие:",
                reply_markup=get_cart_menu()
            )
        except:
            pass

async def process_confirm_remove_all_cart_items(callback_query: types.CallbackQuery):
    """Обработчик для подтверждения удаления всех товаров из корзины."""
    try:
        await callback_query.answer()
        
        user_id = callback_query.from_user.id
        success = clear_cart(user_id)
        
        if success:
            await callback_query.message.edit_text(
                "✅ <b>Все товары успешно удалены из корзины</b>",
                reply_markup=get_cart_menu(),
                parse_mode='HTML'
            )
        else:
            await callback_query.message.edit_text(
                "❌ <b>Не удалось удалить товары из корзины</b>\n\n"
                "Пожалуйста, попробуйте снова.",
                reply_markup=get_cart_menu(),
                parse_mode='HTML'
            )
    except Exception as e:
        print(f"Ошибка при удалении всех товаров: {e}")
        try:
            await callback_query.message.edit_text(
                "Произошла ошибка. Выберите действие:",
                reply_markup=get_cart_menu()
            )
        except:
            pass

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
        lambda c: c.data in ["pay_mir", "pay_visa_mc"],
        state=PaymentStates.waiting_for_payment_method
    )
    dp.register_callback_query_handler(
        process_paid_order,
        lambda c: c.data.startswith("paid_order_")
    )
    dp.register_callback_query_handler(process_cancel_action, lambda c: c.data == "cancel_action")
    dp.register_callback_query_handler(process_remove_all_orders, lambda c: c.data == "remove_all_orders")
    dp.register_callback_query_handler(
        process_confirm_remove_all_cart_items,
        lambda c: c.data == "confirm_remove_all_cart_items_0"
    ) 