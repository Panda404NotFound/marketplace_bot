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
    """Обработчик URL товара."""
    url = message.text.strip()
    
    # Проверяем, является ли URL действительным URL маркетплейса
    if not is_valid_marketplace_url(url):
        await message.answer(
            "❌ Некорректная ссылка. Пожалуйста, убедитесь, что вы отправили правильную ссылку "
            "на товар из Wildberries, Ozon или Яндекс Маркета."
        )
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
    
    product_text += "<b>Укажите количество товара:</b>"
    
    # Проверяем маркетплейс товара
    if product_info.get('marketplace') == 'wildberries':
        # Для Wildberries не отправляем изображения
        await message.answer(
            product_text,
            reply_markup=get_back_menu(),
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
                reply_markup=get_back_menu(),
                parse_mode='HTML'
            )
        except Exception as e:
            # Если не удалось отправить изображение, отправляем только текст
            print(f"Ошибка при отправке изображения: {e}")
            print(f"Детали ошибки: {str(e)}, тип ошибки: {type(e)}")
            
            await message.answer(
                product_text,
                reply_markup=get_back_menu(),
                parse_mode='HTML'
            )
    else:
        # Если у товара нет изображения, отправляем только текст
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
    
    # Получаем данные о товаре из состояния
    data = await state.get_data()
    product_info = data.get('product_info', {})
    
    # Если пользователь отправил '-', устанавливаем размер как None
    if size == '-':
        size = None
        await state.update_data(size=size)
        
        # Запрашиваем цвет товара
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
    
    # Если есть доступные цвета для выбранного размера, предлагаем их выбрать
    if available_colors:
        color_text = "Выберите цвет из доступных вариантов:\n\n"
        for color in available_colors[:10]:  # Ограничиваем количество отображаемых цветов
            color_text += f"- {color}\n"
        
        # Если цветов больше 10, добавляем информацию об этом
        if len(available_colors) > 10:
            color_text += f"\n...и еще {len(available_colors) - 10} цветов"
        
        color_text += "\n\nИли отправьте '-', если цвет не важен."
        
        await message.answer(
            color_text,
            reply_markup=get_back_menu()
        )
    else:
        # Если нет информации о цветах, просто запрашиваем цвет
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
    else:
        # Получаем данные из состояния
        data = await state.get_data()
        available_colors = data.get('available_colors', [])
        
        # Проверяем, соответствует ли указанный цвет доступным цветам
        if available_colors and color not in available_colors:
            color_options = "\n".join([f"- {c}" for c in available_colors[:10]])
            
            # Если цветов больше 10, добавляем информацию об этом
            if len(available_colors) > 10:
                color_options += f"\n...и еще {len(available_colors) - 10} цветов"
            
            await message.answer(
                f"❌ Указанный цвет недоступен. Выберите из доступных цветов:\n\n{color_options}\n\n"
                f"Или отправьте '-', если цвет не важен.",
                reply_markup=get_back_menu()
            )
            return
    
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
        
        # Расчет итоговой суммы
        total_price = product_info['price'] * quantity
        cart_text += f"\n<b>Итоговая сумма:</b> {total_price} ₽\n\n"
        
        cart_text += "Вы можете продолжить покупки или перейти в корзину."
        
        # Проверяем маркетплейс товара
        if product_info.get('marketplace') == 'wildberries':
            # Для Wildberries не отправляем изображения
            await message.answer(
                cart_text,
                reply_markup=get_main_menu(),
                parse_mode='HTML'
            )
        # Если у товара есть изображение и это не Wildberries, пробуем отправить его вместе с текстом
        elif product_info.get('image_url'):
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
            # Если у товара нет изображения, отправляем только текст
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