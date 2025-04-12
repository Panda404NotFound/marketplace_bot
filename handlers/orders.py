from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from database.database import create_product_from_url, add_to_cart, get_user
from utils.marketplace_parser import parse_product_from_url, is_valid_marketplace_url
from keyboards.keyboards import (
    get_main_menu, get_back_menu, get_quantity_keyboard, get_size_keyboard, 
    get_color_keyboard, get_skip_size_keyboard, get_skip_color_keyboard,
    get_notes_keyboard
)

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
    """Обработчик URL товара."""
    url = message.text.strip()
    
    # Проверяем, является ли URL действительным URL маркетплейса
    if not is_valid_marketplace_url(url):
        await message.answer(
            "❌ Некорректная ссылка. Пожалуйста, убедитесь, что вы отправили правильную ссылку "
            "на товар из Wildberries, Ozon или Яндекс Маркета.",
            reply_markup=get_main_menu()
        )
        # Сбрасываем состояние
        await state.finish()
        return
    
    # Проверяем, является ли ссылка на Ozon и выводим специальное сообщение
    if 'ozon.ru' in url.lower():
        await message.answer(
            "⚠️ <b>Маркетплейс Ozon временно не поддерживается</b>\n\n"
            "В настоящий момент функциональность для Ozon находится в разработке.\n"
            "Пожалуйста, используйте товары из Wildberries или Яндекс.Маркет.",
            parse_mode='HTML',
            reply_markup=get_main_menu()
        )
        # Сбрасываем состояние
        await state.finish()
        return
    
    # Отправляем сообщение о процессе парсинга
    wait_message = await message.answer("⏳ Получаем информацию о товаре...")
    
    # Получаем информацию о товаре по URL
    product_info = parse_product_from_url(url)
    
    # Удаляем сообщение о ожидании
    await wait_message.delete()
    
    if not product_info:
        await message.answer(
            "❌ Не удалось получить информацию о товаре. "
            "Пожалуйста, проверьте ссылку и попробуйте снова.",
            reply_markup=get_main_menu()
        )
        # Сбрасываем состояние
        await state.finish()
        return
    
    # Проверяем наличие ошибки (добавлено для обработки капчи и других ошибок)
    if product_info.get('error', False) or product_info.get('price', 0.0) == 0.0:
        # Формируем тип ошибки в зависимости от наличия описания капчи
        if "капча" in product_info.get('description', '').lower() or "captcha" in product_info.get('description', '').lower():
            error_text = "❌ Товар не найден. Пожалуйста, попробуйте еще раз...."
        else:
            error_text = f"❌ Не удалось получить корректную информацию о товаре. {product_info.get('description', 'Пожалуйста, проверьте ссылку и попробуйте снова.')}"
            
        await message.answer(
            error_text,
            reply_markup=get_main_menu()
        )
        # Сбрасываем состояние, чтобы бот не ждал повторного ввода URL
        await state.finish()
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
    
    # Формируем текст о товаре
    marketplace_name = {
        'wildberries': 'Wildberries',
        'ozon': 'Ozon',
        'yandex_market': 'Яндекс.Маркет'
    }.get(product_info['marketplace'], product_info['marketplace'])
    
    product_text = (
        f"✅ <b>Товар найден</b>\n\n"
        f"<b>{product_info['title']}</b>\n"
        f"Маркетплейс: {marketplace_name}\n"
        f"Цена: {product_info['price']} ₽\n\n"
    )
    
    # Добавляем информацию о доступных размерах, если есть
    if 'available_sizes' in product_info and product_info['available_sizes']:
        size_text = "📏 <b>Доступные размеры:</b>\n"
        for size in product_info['available_sizes'][:5]:  # Ограничиваем количество отображаемых размеров
            if isinstance(size, dict):
                size_name = size.get('name', '')
                orig_name = size.get('origName', '')
                size_display = f"{size_name}" if not orig_name else f"{size_name} ({orig_name})"
                size_text += f"- {size_display}\n"
                
                # Добавляем информацию о цветах, если есть
                if 'colors' in size and size['colors']:
                    size_text += "  Доступные цвета:\n"
                    for color in size['colors'][:3]:  # Ограничиваем количество отображаемых цветов
                        size_text += f"  • {color}\n"
        
        # Если размеров больше 5, добавляем информацию об этом
        if len(product_info['available_sizes']) > 5:
            size_text += f"...и еще {len(product_info['available_sizes']) - 5} размеров\n"
        
        product_text += size_text + "\n"
    
    # Проверяем маркетплейс товара
    if product_info.get('marketplace') == 'wildberries':
        # Для Wildberries не отправляем изображения
        await message.answer(
            product_text,
            parse_mode='HTML'
        )
    # Для других маркетплейсов сохраняем прежнюю логику
    elif product_info.get('image_url'):
        try:
            # Добавляем отладочное сообщение перед отправкой изображения
            print(f"Пытаемся отправить изображение: {product_info['image_url']}")
            print(f"Тип URL изображения: {type(product_info['image_url'])}")
            print(f"Длина URL изображения: {len(product_info['image_url']) if product_info['image_url'] else 0}")
            
            # Отправляем изображение с текстом
            await message.answer_photo(
                photo=product_info['image_url'],
                caption=product_text,
                parse_mode='HTML'
            )
        except Exception as e:
            # Если не удалось отправить изображение, отправляем только текст
            print(f"Ошибка при отправке изображения: {e}")
            print(f"Детали ошибки: {str(e)}, тип ошибки: {type(e)}")
            
            await message.answer(
                product_text,
                parse_mode='HTML'
            )
    else:
        # Если у товара нет изображения, отправляем только текст
        await message.answer(
            product_text,
            parse_mode='HTML'
        )
    
    # Отдельное сообщение для запроса количества товара с клавиатурой
    await message.answer(
        "<b>Укажите количество товара:</b>",
        reply_markup=get_quantity_keyboard(),
        parse_mode='HTML'
    )
    
    # Переходим к следующему этапу - указанию количества
    await OrderStates.waiting_for_quantity.set()

async def process_quantity_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик для выбора количества товара через inline-клавиатуру."""
    await callback_query.answer()
    
    # Получаем выбранное количество из callback_data
    quantity_str = callback_query.data.replace('quantity_', '')
    
    if quantity_str == 'manual':
        # Пользователь выбрал ручной ввод, запрашиваем количество
        await callback_query.message.edit_text(
            "<b>Укажите количество товара:</b>\n\nВведите число:",
            parse_mode='HTML'
        )
        return
    
    try:
        quantity = int(quantity_str)
        
        # Сохраняем количество в состояние
        await state.update_data(quantity=quantity)
        
        # Получаем данные о товаре из состояния
        data = await state.get_data()
        product_info = data.get('product_info', {})
        
        # Проверяем, есть ли информация о размерах товара
        available_sizes = product_info.get('available_sizes', [])
        marketplace = product_info.get('marketplace', '')
        
        if available_sizes:
            # Создаем клавиатуру для выбора размера
            await callback_query.message.edit_text(
                "<b>Доступные размеры:</b>",
                reply_markup=get_size_keyboard(available_sizes),
                parse_mode='HTML'
            )
            
            # Переходим к следующему этапу - указанию размера
            await OrderStates.waiting_for_size.set()
        elif marketplace in ['yandex_market', 'ozon']:
            # Для Яндекс.Маркет и Озон предлагаем клавиатуру пропуска
            await callback_query.message.edit_text(
                "Укажите размер товара (если применимо) или нажмите 'Пропустить', если размер не требуется:",
                reply_markup=get_skip_size_keyboard()
            )
            
            # Переходим к следующему этапу - указанию размера
            await OrderStates.waiting_for_size.set()
        else:
            # Для других маркетплейсов или случаев без размеров просто запрашиваем размер текстом
            await callback_query.message.edit_text(
                "Укажите размер товара (если применимо) или отправьте '-', если размер не требуется:",
                reply_markup=get_back_menu()
            )
            
            # Переходим к следующему этапу - указанию размера
            await OrderStates.waiting_for_size.set()
    except ValueError:
        # Ошибка при конвертации в число
        await callback_query.message.edit_text(
            "❌ Произошла ошибка. Пожалуйста, укажите количество товара вручную:",
            reply_markup=get_back_menu()
        )
        return

async def process_product_quantity(message: types.Message, state: FSMContext):
    """Обработчик количества товара при ручном вводе."""
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
    
    # Получаем данные о товаре из состояния
    data = await state.get_data()
    product_info = data.get('product_info', {})
    
    # Проверяем, есть ли информация о размерах товара
    available_sizes = product_info.get('available_sizes', [])
    
    if available_sizes:
        # Если есть доступные размеры, показываем их с клавиатурой выбора
        await message.answer(
            "<b>Доступные размеры:</b>",
            reply_markup=get_size_keyboard(available_sizes),
            parse_mode='HTML'
        )
    else:
        # Если нет информации о размерах, запрашиваем размер текстом
        await message.answer(
            "Укажите размер товара (если применимо) или отправьте '-', если размер не требуется:",
            reply_markup=get_back_menu()
        )
    
    # Переходим к следующему этапу - указанию размера
    await OrderStates.waiting_for_size.set()

async def process_size_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик для выбора размера товара через inline-клавиатуру."""
    await callback_query.answer()
    
    # Получаем выбранный размер из callback_data
    size_str = callback_query.data.replace('size_', '')
    
    if size_str == 'none':
        # Пользователь выбрал "Не требуется" или "Пропустить"
        size = None
        
        # Сохраняем размер в состояние
        await state.update_data(size=size)
        
        # Получаем данные из состояния
        data = await state.get_data()
        product_info = data.get('product_info', {})
        
        # Запрашиваем примечания к товару
        await callback_query.message.edit_text(
            "Укажите примечания к товару (если требуется) или нажмите 'Пропустить':",
            reply_markup=get_notes_keyboard()
        )
        
        # Переходим к следующему этапу - указанию цвета/примечаний
        await OrderStates.waiting_for_color.set()
        return
    elif size_str == 'manual':
        # Пользователь выбрал "Ввести вручную", запрашиваем размер текстом
        await callback_query.message.edit_text(
            "Введите размер товара:",
            reply_markup=get_back_menu()
        )
        return
    else:
        size = size_str
    
    # Сохраняем размер в состояние
    await state.update_data(size=size)
    
    # Получаем данные из состояния
    data = await state.get_data()
    product_info = data.get('product_info', {})
    marketplace = product_info.get('marketplace', '')
    
    # Получаем доступные цвета для выбранного размера
    available_colors = []
    if size and 'available_sizes' in product_info:
        for s in product_info['available_sizes']:
            if isinstance(s, dict) and s.get('name') == size:
                available_colors = s.get('colors', [])
                break
    
    # Сохраняем доступные цвета в состояние
    await state.update_data(available_colors=available_colors)
    
    if available_colors:
        # Создаем клавиатуру для выбора цвета
        await callback_query.message.edit_text(
            "<b>Доступные цвета:</b>",
            reply_markup=get_color_keyboard(available_colors),
            parse_mode='HTML'
        )
    elif marketplace in ['yandex_market', 'ozon']:
        # Для Яндекс.Маркет и Озон предлагаем примечания к товару
        await callback_query.message.edit_text(
            "Укажите примечания к товару (если требуется) или нажмите 'Пропустить':",
            reply_markup=get_notes_keyboard()
        )
    else:
        # Если нет доступных цветов, запрашиваем примечания к товару
        await callback_query.message.edit_text(
            "Укажите примечания к товару (если требуется) или нажмите 'Пропустить':",
            reply_markup=get_notes_keyboard()
        )
    
    # Переходим к следующему этапу - указанию цвета/примечаний
    await OrderStates.waiting_for_color.set()

async def process_color_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик для выбора цвета товара или ввода примечаний через inline-клавиатуру."""
    await callback_query.answer()
    
    # Получаем выбранное действие из callback_data
    action_str = callback_query.data.replace('color_', '')
    
    if action_str == 'none':
        # Пользователь выбрал "Не требуется" или "Пропустить"
        notes = None
    elif action_str == 'manual':
        # Пользователь выбрал "Ввести примечание", запрашиваем примечание текстом
        await callback_query.message.edit_text(
            "Введите примечания к товару:",
            reply_markup=get_back_menu()
        )
        return
    else:
        # Если был выбран конкретный цвет из списка
        notes = action_str
    
    # Добавляем товар в корзину с примечанием вместо цвета
    await add_product_to_cart(callback_query.message, state, callback_query.from_user.id, notes)

async def add_product_to_cart(message, state, user_id, notes=None):
    """Функция для добавления товара в корзину."""
    # Получаем все данные из состояния
    data = await state.get_data()
    product_id = data.get('product_id')
    product_info = data.get('product_info')
    quantity = data.get('quantity')
    size = data.get('size')
    
    # Добавляем товар в корзину
    success = add_to_cart(user_id, product_id, quantity, size, notes)
    
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
        
        if notes:
            cart_text += f"Примечания: {notes}\n"
        
        # Расчет итоговой суммы с явным преобразованием в число
        try:
            price = float(product_info['price'])
            total_price = price * quantity
            cart_text += f"\n<b>Итоговая сумма:</b> {total_price:.2f} ₽\n\n"
        except (ValueError, TypeError):
            # Если не удалось преобразовать цену в число, выводим сообщение
            cart_text += f"\n<b>Итоговая сумма:</b> Не удалось рассчитать\n\n"
        
        cart_text += "Вы можете продолжить покупки или перейти в корзину."
        
        # Проверяем тип сообщения
        if hasattr(message, 'edit_text'):  # Это callback_query.message
            try:
                await message.edit_text(
                    cart_text,
                    reply_markup=get_main_menu(),
                    parse_mode='HTML'
                )
            except Exception:
                # Если не удалось отредактировать сообщение, отправляем новое
                bot = message.bot
                await bot.send_message(
                    chat_id=user_id,
                    text=cart_text,
                    reply_markup=get_main_menu(),
                    parse_mode='HTML'
                )
        else:  # Это обычное message
            # Проверяем маркетплейс товара
            if product_info.get('marketplace') == 'wildberries' or not product_info.get('image_url'):
                # Для Wildberries или товаров без изображения отправляем только текст
                await message.answer(
                    cart_text,
                    reply_markup=get_main_menu(),
                    parse_mode='HTML'
                )
            else:
                # Для товаров с изображением пробуем отправить фото
                try:
                    await message.answer_photo(
                        photo=product_info['image_url'],
                        caption=cart_text,
                        reply_markup=get_main_menu(),
                        parse_mode='HTML'
                    )
                except Exception:
                    # Если не удалось отправить изображение, отправляем только текст
                    await message.answer(
                        cart_text,
                        reply_markup=get_main_menu(),
                        parse_mode='HTML'
                    )
    else:
        # Обработка ошибки в зависимости от типа сообщения
        error_text = "❌ Произошла ошибка при добавлении товара в корзину. Пожалуйста, попробуйте снова."
        
        if hasattr(message, 'edit_text'):  # Это callback_query.message
            try:
                await message.edit_text(
                    error_text,
                    reply_markup=get_main_menu()
                )
            except Exception:
                bot = message.bot
                await bot.send_message(
                    chat_id=user_id,
                    text=error_text,
                    reply_markup=get_main_menu()
                )
        else:  # Это обычное message
            await message.answer(
                error_text,
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
        "Выберите, что хотите сделать:\n"
        "• 👤 Мой кабинет - профиль, заказы, настройки\n"
        "• 🛍️ Оформить заказ - добавить новый товар\n"
        "• 🚚 Доставка - информация о доставке\n"
        "• 🛒 Моя корзина - управление товарами\n\n"
        "📌 В любой момент можно вернуться в главное меню или ввести /help для справки",
        reply_markup=get_main_menu()
    )

async def process_product_size(message: types.Message, state: FSMContext):
    """Обработчик размера товара при текстовом вводе."""
    size = message.text.strip()
    
    # Получаем данные о товаре из состояния
    data = await state.get_data()
    product_info = data.get('product_info', {})
    marketplace = product_info.get('marketplace', '')
    
    # Если пользователь отправил '-', устанавливаем размер как None
    if size == '-':
        size = None
        await state.update_data(size=size)
        
        # Если это Yandex или Ozon, сразу добавляем товар в корзину без запроса цвета
        if marketplace in ['yandex_market', 'ozon']:
            await add_product_to_cart(message, state, message.from_user.id, notes=None)
            return
        else:
            # Для других маркетплейсов запрашиваем цвет товара
            await message.answer(
                "Укажите цвет товара (если применимо) или отправьте '-', если цвет не требуется:",
                reply_markup=get_back_menu()
            )
            
            # Переходим к следующему этапу - указанию цвета
            await OrderStates.waiting_for_color.set()
            return
    
    # Проверяем, есть ли информация о размерах товара
    available_sizes = product_info.get('available_sizes', [])
    valid_size = False
    
    # Список для хранения доступных цветов для выбранного размера
    available_colors = []
    
    # Проверяем, соответствует ли указанный размер доступным размерам
    for s in available_sizes:
        if isinstance(s, dict) and (s.get('name') == size or s.get('origName') == size):
            valid_size = True
            # Сохраняем доступные цвета для этого размера
            available_colors = s.get('colors', [])
            break
    
    if available_sizes and not valid_size:
        # Если размер не соответствует доступным, отправляем сообщение с доступными размерами
        size_options = "\n".join([
            f"- {s.get('name', '')} " + (f"({s.get('origName', '')})" if s.get('origName') else '')
            for s in available_sizes[:10] if isinstance(s, dict)
        ])
        
        # Если размеров больше 10, добавляем информацию об этом
        if len(available_sizes) > 10:
            size_options += f"\n...и еще {len(available_sizes) - 10} размеров"
        
        await message.answer(
            f"❌ Указанный размер недоступен. Выберите из доступных размеров:\n\n{size_options}\n\n"
            f"Или отправьте '-', если размер не важен.",
            reply_markup=get_back_menu()
        )
        return
    
    # Сохраняем размер и доступные цвета в состояние
    await state.update_data(size=size, available_colors=available_colors)
    
    # Если это Yandex или Ozon и нет доступных цветов, сразу добавляем товар в корзину
    if marketplace in ['yandex_market', 'ozon'] and not available_colors:
        await add_product_to_cart(message, state, message.from_user.id, notes=None)
        return
    
    # Если есть доступные цвета для выбранного размера, предлагаем их выбрать
    if available_colors:
        # Создаем клавиатуру для выбора цвета
        await message.answer(
            "<b>Доступные цвета:</b>",
            reply_markup=get_color_keyboard(available_colors),
            parse_mode='HTML'
        )
    else:
        # Если нет информации о цветах, просто запрашиваем цвет
        await message.answer(
            "Укажите цвет товара (если применимо) или отправьте '-', если цвет не требуется:",
            reply_markup=get_back_menu()
        )
    
    # Переходим к следующему этапу - указанию цвета
    await OrderStates.waiting_for_color.set()

async def process_product_notes(message: types.Message, state: FSMContext):
    """Обработчик примечаний к товару при текстовом вводе."""
    notes = message.text.strip()
    
    # Если пользователь отправил '-', устанавливаем примечания как None
    if notes == '-':
        notes = None
    
    # Добавляем товар в корзину с использованием общей функции
    await add_product_to_cart(message, state, message.from_user.id, notes)

def register_order_handlers(dp):
    """Регистрация обработчиков для раздела 'Оформить заказ'."""
    dp.register_callback_query_handler(process_new_order, lambda c: c.data == "new_order")
    dp.register_message_handler(process_product_url, state=OrderStates.waiting_for_url)
    dp.register_message_handler(process_product_quantity, state=OrderStates.waiting_for_quantity)
    
    # Обработчики для inline-кнопок
    dp.register_callback_query_handler(
        process_quantity_selection, 
        lambda c: c.data.startswith("quantity_"), 
        state=OrderStates.waiting_for_quantity
    )
    dp.register_callback_query_handler(
        process_size_selection, 
        lambda c: c.data.startswith("size_"), 
        state=OrderStates.waiting_for_size
    )
    dp.register_callback_query_handler(
        process_color_selection, 
        lambda c: c.data.startswith("color_"), 
        state=OrderStates.waiting_for_color
    )
    
    dp.register_message_handler(process_product_size, state=OrderStates.waiting_for_size)
    dp.register_message_handler(process_product_notes, state=OrderStates.waiting_for_color)
    
    # Обработчик возврата в главное меню из любого состояния OrderStates
    dp.register_callback_query_handler(
        process_back_to_main_menu,
        lambda c: c.data in ["back", "main_menu"],
        state=OrderStates.all_states
    ) 