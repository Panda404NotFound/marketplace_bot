from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from database.database import create_product_from_url, add_to_cart, get_user
from utils.marketplace_parser import parse_product_from_url, is_valid_marketplace_url
from keyboards.keyboards import get_main_menu, get_back_menu

class OrderStates(StatesGroup):
    """Состояния для оформления заказа."""
    waiting_for_url = State()
    waiting_for_quantity = State()
    waiting_for_size = State()
    waiting_for_color = State()

async def process_new_order(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик для создания нового заказа."""
    await callback_query.answer()
    
    await callback_query.message.edit_text(
        "🔗 <b>Оформление заказа</b>\n\n"
        "Отправьте ссылку на товар из одного из поддерживаемых маркетплейсов:\n"
        "• Wildberries\n"
        "• Ozon\n"
        "• Яндекс Маркет\n\n"
        "Или нажмите кнопку 'Назад' для возврата в главное меню.",
        reply_markup=get_back_menu(),
        parse_mode='HTML'
    )
    
    # Устанавливаем состояние ожидания URL товара
    await OrderStates.waiting_for_url.set()

async def process_product_url(message: types.Message, state: FSMContext):
    """Обработчик ссылки на товар."""
    url = message.text.strip()
    
    # Проверяем, является ли URL действительным URL маркетплейса
    if not is_valid_marketplace_url(url):
        await message.answer(
            "❌ Некорректная ссылка. Пожалуйста, убедитесь, что вы отправили правильную ссылку "
            "на товар из Wildberries, Ozon или Яндекс Маркета."
        )
        return
    
    # Получаем информацию о товаре по URL
    product_info = parse_product_from_url(url)
    
    if not product_info:
        await message.answer(
            "❌ Не удалось получить информацию о товаре. "
            "Пожалуйста, проверьте ссылку и попробуйте снова."
        )
        return
    
    # Сохраняем информацию о товаре в состояние
    await state.update_data(
        product_url=url,
        product_info=product_info
    )
    
    # Создаем товар в базе данных
    product_id = create_product_from_url(
        url=url,
        marketplace=product_info['marketplace'],
        title=product_info['title'],
        price=product_info['price'],
        description=product_info.get('description'),
        image_url=product_info.get('image_url')
    )
    
    # Сохраняем ID товара в состояние
    await state.update_data(product_id=product_id)
    
    # Отображаем информацию о товаре
    product_text = (
        f"✅ <b>Товар найден</b>\n\n"
        f"<b>{product_info['title']}</b>\n"
        f"Цена: {product_info['price']} ₽\n\n"
        f"<b>Укажите количество товара:</b>"
    )
    
    await message.answer(
        product_text,
        reply_markup=get_back_menu(),
        parse_mode='HTML'
    )
    
    # Переходим к следующему этапу - указанию количества
    await OrderStates.waiting_for_quantity.set()

async def process_product_quantity(message: types.Message, state: FSMContext):
    """Обработчик количества товара."""
    try:
        quantity = int(message.text.strip())
        if quantity <= 0:
            raise ValueError("Количество должно быть положительным")
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите корректное количество товара (целое положительное число)."
        )
        return
    
    # Сохраняем количество в состояние
    await state.update_data(quantity=quantity)
    
    # Запрашиваем размер (если применимо)
    await message.answer(
        "Укажите размер товара (если применимо) или отправьте '-', если размер не требуется:",
        reply_markup=get_back_menu()
    )
    
    # Переходим к следующему этапу - указанию размера
    await OrderStates.waiting_for_size.set()

async def process_product_size(message: types.Message, state: FSMContext):
    """Обработчик размера товара."""
    size = message.text.strip()
    
    # Если пользователь отправил '-', устанавливаем размер как None
    if size == '-':
        size = None
    
    # Сохраняем размер в состояние
    await state.update_data(size=size)
    
    # Запрашиваем цвет (если применимо)
    await message.answer(
        "Укажите цвет товара (если применимо) или отправьте '-', если цвет не требуется:",
        reply_markup=get_back_menu()
    )
    
    # Переходим к следующему этапу - указанию цвета
    await OrderStates.waiting_for_color.set()

async def process_product_color(message: types.Message, state: FSMContext):
    """Обработчик цвета товара."""
    color = message.text.strip()
    
    # Если пользователь отправил '-', устанавливаем цвет как None
    if color == '-':
        color = None
    
    # Получаем все данные из состояния
    data = await state.get_data()
    product_id = data.get('product_id')
    product_info = data.get('product_info')
    quantity = data.get('quantity')
    size = data.get('size')
    
    # Добавляем товар в корзину
    user_id = message.from_user.id
    success = add_to_cart(user_id, product_id, quantity, size, color)
    
    if success:
        # Формируем текст о добавлении товара в корзину
        cart_text = (
            f"✅ <b>Товар добавлен в корзину</b>\n\n"
            f"<b>{product_info['title']}</b>\n"
            f"Цена: {product_info['price']} ₽\n"
            f"Количество: {quantity}\n"
        )
        
        if size:
            cart_text += f"Размер: {size}\n"
        
        if color:
            cart_text += f"Цвет: {color}\n"
        
        cart_text += "\nВы можете продолжить покупки или перейти в корзину."
        
        await message.answer(
            cart_text,
            reply_markup=get_main_menu(),
            parse_mode='HTML'
        )
    else:
        await message.answer(
            "❌ Произошла ошибка при добавлении товара в корзину. Пожалуйста, попробуйте снова.",
            reply_markup=get_main_menu()
        )
    
    # Завершаем состояние
    await state.finish()

async def process_back_to_main_menu(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик возврата в главное меню."""
    await callback_query.answer()
    
    # Завершаем текущее состояние
    await state.finish()
    
    await callback_query.message.edit_text(
        "Выберите, что хотите сделать:",
        reply_markup=get_main_menu()
    )

def register_order_handlers(dp):
    """Регистрация обработчиков для раздела 'Оформить заказ'."""
    dp.register_callback_query_handler(process_new_order, lambda c: c.data == "new_order")
    dp.register_message_handler(process_product_url, state=OrderStates.waiting_for_url)
    dp.register_message_handler(process_product_quantity, state=OrderStates.waiting_for_quantity)
    dp.register_message_handler(process_product_size, state=OrderStates.waiting_for_size)
    dp.register_message_handler(process_product_color, state=OrderStates.waiting_for_color)
    
    # Обработчик возврата в главное меню из любого состояния OrderStates
    dp.register_callback_query_handler(
        process_back_to_main_menu,
        lambda c: c.data in ["back", "main_menu"],
        state=OrderStates.all_states
    ) 