# utils/telegram_bot.py - ИСПРАВЛЕННАЯ версия с правильными функциями

import requests
from bot_data import BOT_TOKEN

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_telegram_message(chat_id, text):
    """Базовая отправка сообщения"""
    try:
        response = requests.post(
            f"{BASE_URL}/sendMessage", 
            data={
                "chat_id": chat_id, 
                "text": text, 
                "parse_mode": "HTML"
            }, 
            timeout=10
        )
        result = response.json()
        if result.get('ok'):
            return True
        else:
            print(f"❌ Telegram API error: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Telegram send error: {e}")
        return False

def send_booking_notification(booking, notification_type='created'):
    """
    Отправить уведомление о заявке
    
    Args:
        booking: объект заявки
        notification_type: тип уведомления ('created', 'confirmed', 'cancelled', 'completed')
    """
    print(f"\n📱 === TELEGRAM УВЕДОМЛЕНИЕ ===")
    print(f"📋 Заявка: #{booking.id}")
    print(f"📞 Телефон: {booking.phone}")
    print(f"🔔 Тип: {notification_type}")
    
    try:
        if not booking.phone:
            print("❌ Нет номера телефона")
            return False
        
        # Импортируем здесь, чтобы избежать циклических импортов
        from models import TelegramUser
        
        # Ищем пользователя по телефону
        user = TelegramUser.query.filter_by(phone=booking.phone, is_verified=True).first()
        
        if not user:
            print(f"❌ Пользователь с телефоном {booking.phone} не зарегистрирован в Telegram")
            print("💡 Пользователь должен написать /start боту @korolevstvo_chudes_bot")
            return False
        
        print(f"👤 Найден пользователь: {user.get_display_name()}")
        print(f"📱 Telegram ID: {user.telegram_id}")
        
        # Получаем данные для сообщения
        service_name = booking.service.title if booking.service else 'Не указана'
        date_str = booking.event_date.strftime('%d.%m.%Y') if booking.event_date else 'Не указана'
        time_str = booking.event_time.strftime('%H:%M') if booking.event_time else 'Не указано'
        
        # Формируем сообщение в зависимости от типа
        if notification_type == 'created':
            message = f"""🎉 <b>Новая заявка принята!</b>

<b>Заявка #{booking.id}</b>
🎪 Услуга: {service_name}
📅 Дата: {date_str}
👤 Имя: {booking.name}

✅ Мы получили вашу заявку и скоро свяжемся с вами!

📞 Вопросы: 8 (705) 519 5222"""

        elif notification_type == 'confirmed':
            message = f"""✅ <b>Заявка подтверждена!</b>

<b>Заявка #{booking.id}</b>
🎪 Услуга: {service_name}
📅 Дата: {date_str}
🕐 Время: {time_str}
📍 Место: {booking.location or 'Будет уточнено'}

🎉 Ваш праздник состоится! Мы готовимся к волшебству!

📞 Контакт: 8 (705) 519 5222"""

        elif notification_type == 'cancelled':
            message = f"""😔 <b>Заявка отменена</b>

<b>Заявка #{booking.id}</b>
К сожалению, заявка была отменена.

💬 Если у вас есть вопросы, свяжитесь с нами:
📞 8 (705) 519 5222

Мы поможем организовать ваш идеальный праздник! 🎪"""

        elif notification_type == 'completed':
            message = f"""🎉 <b>Праздник завершен!</b>

<b>Заявка #{booking.id}</b>
Спасибо, что выбрали Королевство Чудес!

Надеемся, праздник получился волшебным! ✨

🌟 Поделитесь впечатлениями - оставьте отзыв на сайте!

📞 Заказать еще один праздник: 8 (705) 519 5222
🌐 prazdnikvdom.kz"""

        else:
            print(f"❌ Неизвестный тип уведомления: {notification_type}")
            return False
        
        print(f"📝 Сообщение сформировано:")
        print(f"📄 Длина: {len(message)} символов")
        
        # Отправляем сообщение
        print(f"📤 Отправляем сообщение...")
        result = send_telegram_message(user.telegram_id, message)
        
        if result:
            print(f"🎉 Уведомление отправлено УСПЕШНО!")
            
            # Обновляем активность пользователя
            user.update_activity()
            
            return True
        else:
            print(f"❌ Ошибка отправки уведомления")
            return False
            
    except Exception as e:
        print(f"💥 КРИТИЧЕСКАЯ ОШИБКА в send_booking_notification: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print(f"🏁 === КОНЕЦ TELEGRAM УВЕДОМЛЕНИЯ ===\n")

# Дополнительные функции для совместимости со старым кодом
def send_booking_created_notification(booking):
    """Уведомление о создании заявки"""
    return send_booking_notification(booking, 'created')

def send_booking_confirmed_notification(booking):
    """Уведомление о подтверждении заявки"""
    return send_booking_notification(booking, 'confirmed')

def send_booking_cancelled_notification(booking):
    """Уведомление об отмене заявки"""
    return send_booking_notification(booking, 'cancelled')

def send_booking_completed_notification(booking):
    """Уведомление о завершении заявки"""
    return send_booking_notification(booking, 'completed')

# Функция для проверки подключения к боту
def test_bot_connection():
    """Проверить подключение к Telegram боту"""
    try:
        response = requests.get(f"{BASE_URL}/getMe", timeout=10)
        result = response.json()
        
        if result.get('ok'):
            bot_info = result['result']
            print(f"✅ Бот подключен: @{bot_info['username']}")
            print(f"   ID: {bot_info['id']}")
            print(f"   Имя: {bot_info['first_name']}")
            return True
        else:
            print(f"❌ Ошибка подключения: {result.get('description')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования бота: {e}")
        return False

# Функция для отладки - проверить пользователя по телефону
def debug_check_user(phone):
    """Отладочная функция - проверить пользователя по телефону"""
    try:
        from app import create_app
        from models import TelegramUser
        
        app = create_app()
        with app.app_context():
            user = TelegramUser.query.filter_by(phone=phone).first()
            
            if user:
                print(f"👤 Пользователь найден:")
                print(f"   Имя: {user.get_display_name()}")
                print(f"   Телефон: {user.phone}")
                print(f"   Telegram ID: {user.telegram_id}")
                print(f"   Верифицирован: {user.is_verified}")
                print(f"   Регистрация: {user.created_at}")
                print(f"   Активность: {user.last_activity}")
                return user
            else:
                print(f"❌ Пользователь с телефоном {phone} не найден")
                return None
                
    except Exception as e:
        print(f"❌ Ошибка проверки пользователя: {e}")
        return None