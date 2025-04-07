from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config.config import DATABASE_URL
from database.models import Base, User, Product, CartItem, Order, OrderItem

# Создаем движок базы данных
engine = create_engine(DATABASE_URL)

# Создаем фабрику сессий
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def get_session():
    """Получить сессию базы данных."""
    return Session()

def init_db():
    """Инициализировать базу данных."""
    Base.metadata.create_all(engine)

# Методы для работы с пользователями
def get_user(user_id):
    """Получить пользователя по Telegram ID."""
    session = get_session()
    user = session.query(User).filter(User.user_id == user_id).first()
    session.close()
    return user

def create_user(user_id, username=None, first_name=None, last_name=None):
    """Создать нового пользователя."""
    session = get_session()
    user = User(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name
    )
    session.add(user)
    session.commit()
    user_id = user.id
    session.close()
    return user_id

def update_user(user_id, **kwargs):
    """Обновить данные пользователя."""
    session = get_session()
    user = session.query(User).filter(User.user_id == user_id).first()
    if user:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        session.commit()
    session.close()
    return user

# Методы для работы с корзиной
def get_cart_items(user_id):
    """Получить все товары в корзине пользователя."""
    session = get_session()
    user = session.query(User).filter(User.user_id == user_id).first()
    if not user:
        session.close()
        return []
    
    cart_items = session.query(CartItem).filter(CartItem.user_id == user.id).all()
    result = []
    for item in cart_items:
        product = session.query(Product).filter(Product.id == item.product_id).first()
        if product:
            result.append({
                'id': item.id,
                'product': product,
                'quantity': item.quantity,
                'size': item.size,
                'color': item.color
            })
    
    session.close()
    return result

def add_to_cart(user_id, product_id, quantity=1, size=None, color=None):
    """Добавить товар в корзину пользователя."""
    session = get_session()
    user = session.query(User).filter(User.user_id == user_id).first()
    if not user:
        session.close()
        return False
    
    # Проверяем, есть ли уже такой товар в корзине
    cart_item = session.query(CartItem).filter(
        CartItem.user_id == user.id,
        CartItem.product_id == product_id,
        CartItem.size == size,
        CartItem.color == color
    ).first()
    
    if cart_item:
        # Если товар уже есть, увеличиваем количество
        cart_item.quantity += quantity
    else:
        # Если товара нет, создаем новую запись
        cart_item = CartItem(
            user_id=user.id,
            product_id=product_id,
            quantity=quantity,
            size=size,
            color=color
        )
        session.add(cart_item)
    
    session.commit()
    session.close()
    return True

def remove_from_cart(user_id, cart_item_id):
    """Удалить товар из корзины пользователя."""
    session = get_session()
    user = session.query(User).filter(User.user_id == user_id).first()
    if not user:
        session.close()
        return False
    
    cart_item = session.query(CartItem).filter(
        CartItem.id == cart_item_id,
        CartItem.user_id == user.id
    ).first()
    
    if cart_item:
        session.delete(cart_item)
        session.commit()
        session.close()
        return True
    else:
        session.close()
        return False

# Методы для работы с заказами
def create_order(user_id, delivery_address, delivery_time=None, payment_method=None):
    """Создать новый заказ из товаров в корзине."""
    session = get_session()
    user = session.query(User).filter(User.user_id == user_id).first()
    if not user:
        session.close()
        return None
    
    # Получаем товары из корзины
    cart_items = session.query(CartItem).filter(CartItem.user_id == user.id).all()
    if not cart_items:
        session.close()
        return None
    
    # Создаем заказ
    total_amount = 0
    for item in cart_items:
        product = session.query(Product).filter(Product.id == item.product_id).first()
        total_amount += product.price * item.quantity
    
    order = Order(
        user_id=user.id,
        total_amount=total_amount,
        delivery_address=delivery_address,
        delivery_time=delivery_time,
        payment_method=payment_method,
        status="new"
    )
    session.add(order)
    session.flush()  # Чтобы получить id заказа
    
    # Добавляем товары в заказ
    for item in cart_items:
        product = session.query(Product).filter(Product.id == item.product_id).first()
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=product.price,
            size=item.size,
            color=item.color
        )
        session.add(order_item)
    
    # Очищаем корзину пользователя
    for item in cart_items:
        session.delete(item)
    
    session.commit()
    session.close()
    return order.id

def get_orders(user_id):
    """Получить все заказы пользователя."""
    session = get_session()
    user = session.query(User).filter(User.user_id == user_id).first()
    if not user:
        session.close()
        return []
    
    orders = session.query(Order).filter(Order.user_id == user.id).all()
    result = []
    for order in orders:
        items = session.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        order_items = []
        for item in items:
            product = session.query(Product).filter(Product.id == item.product_id).first()
            order_items.append({
                'product': product,
                'quantity': item.quantity,
                'price': item.price,
                'size': item.size,
                'color': item.color
            })
        
        result.append({
            'id': order.id,
            'total_amount': order.total_amount,
            'delivery_address': order.delivery_address,
            'delivery_time': order.delivery_time,
            'payment_method': order.payment_method,
            'status': order.status,
            'created_at': order.created_at,
            'items': order_items
        })
    
    session.close()
    return result

def get_order(order_id):
    """Получить информацию о заказе по ID."""
    session = get_session()
    order = session.query(Order).filter(Order.id == order_id).first()
    if not order:
        session.close()
        return None
    
    items = session.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    order_items = []
    for item in items:
        product = session.query(Product).filter(Product.id == item.product_id).first()
        order_items.append({
            'product': product,
            'quantity': item.quantity,
            'price': item.price,
            'size': item.size,
            'color': item.color
        })
    
    result = {
        'id': order.id,
        'user_id': order.user_id,
        'total_amount': order.total_amount,
        'delivery_address': order.delivery_address,
        'delivery_time': order.delivery_time,
        'payment_method': order.payment_method,
        'status': order.status,
        'created_at': order.created_at,
        'items': order_items
    }
    
    session.close()
    return result

def cancel_order(user_id, order_id):
    """Отменить заказ пользователя."""
    session = get_session()
    user = session.query(User).filter(User.user_id == user_id).first()
    if not user:
        session.close()
        return False
    
    order = session.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user.id
    ).first()
    
    if order and order.status in ["new", "paid"]:
        order.status = "cancelled"
        session.commit()
        session.close()
        return True
    else:
        session.close()
        return False

# Методы для работы с товарами
def create_product_from_url(url, marketplace, title, price, description=None, image_url=None):
    """Создать новый товар из URL."""
    session = get_session()
    product = Product(
        marketplace=marketplace,
        title=title,
        description=description,
        price=price,
        image_url=image_url,
        url=url
    )
    session.add(product)
    session.commit()
    product_id = product.id
    session.close()
    return product_id 