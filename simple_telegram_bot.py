import requests
import json
import time
import sys
import os
import re
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройки бота
from bot_data import BOT_TOKEN
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

class SimpleTelegramBot:
    def __init__(self):
        self.base_url = BASE_URL
        self.last_update_id = 0
        self.running = False
        
    def send_message(self, chat_id, text, parse_mode="HTML"):
        """Отправить сообщение"""
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        try:
            response = requests.post(url, data=payload, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                print(f"✅ Сообщение отправлено в чат {chat_id}")
                return result
            else:
                print(f"❌ Ошибка отправки: {result.get('description')}")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка отправки сообщения: {e}")
            return None
    
    def get_updates(self, offset=None, timeout=30):
        """Получить обновления от Telegram"""
        url = f"{self.base_url}/getUpdates"
        params = {
            'timeout': timeout,
            'allowed_updates': ['message']
        }
        
        if offset:
            params['offset'] = offset
            
        try:
            response = requests.get(url, params=params, timeout=timeout + 5)
            return response.json()
        except requests.exceptions.Timeout:
            return {'ok': True, 'result': []}
        except Exception as e:
            print(f"❌ Ошибка получения обновлений: {e}")
            return {'ok': False, 'result': []}
    
    def process_message(self, message):
        """Простая обработка сообщений"""
        try:
            chat_id = str(message['chat']['id'])
            text = message.get('text', '').strip()
            user_data = message['from']
            
            print(f"📨 {user_data.get('first_name', 'Unknown')} ({chat_id}): {text}")
            
            # Импортируем модели
            from app import create_app
            from models import db, TelegramUser
            
            app = create_app()
            with app.app_context():
                # Находим или создаем пользователя
                user = TelegramUser.query.filter_by(telegram_id=chat_id).first()
                
                if not user:
                    user = TelegramUser(
                        telegram_id=chat_id,
                        username=user_data.get('username'),
                        first_name=user_data.get('first_name'),
                        last_name=user_data.get('last_name'),
                        registration_step='start'
                    )
                    db.session.add(user)
                    db.session.commit()
                    print(f"👤 Новый пользователь: {user.get_display_name()}")
                
                # Простая обработка команд
                if text == '/start':
                    self.handle_start(user)
                elif text == '/help':
                    self.handle_help(user)
                elif text == '/my_bookings' or text == '/mybookings':
                    self.handle_my_bookings(user)
                elif user.registration_step == 'phone':
                    self.handle_phone(user, text)
                else:
                    # Любое другое сообщение - справка
                    self.handle_help(user)
                
                user.update_activity()
                
        except Exception as e:
            print(f"❌ Ошибка обработки сообщения: {e}")
            # Отправляем сообщение об ошибке пользователю
            self.send_message(chat_id, "❌ Произошла ошибка. Попробуйте позже или напишите /start")
    
    def handle_start(self, user):
        """Команда /start"""
        if user.is_verified:
            # Пользователь уже зарегистрирован
            message = f"""
🎪 <b>Добро пожаловать, {user.first_name}!</b>

Вы уже зарегистрированы в системе уведомлений.

<b>Ваши данные:</b>
📞 Телефон: {user.phone}
📧 Email: {user.email or 'не указан'}

Теперь вы будете получать уведомления о ваших заявках!

<b>Команды:</b>
/my_bookings - Мои заявки
/help - Справка
            """
        else:
            # Новый пользователь
            message = f"""
🎪 <b>Добро пожаловать в Королевство Чудес!</b>

Привет, {user.first_name}! 

Этот бот будет присылать вам уведомления о ваших заявках на праздники.

📱 <b>Для начала отправьте свой номер телефона:</b>

Примеры формата:
• +77051234567
• 87051234567  
• 77051234567

<i>Используйте тот же номер, что указываете при заказе на сайте.</i>
            """
            user.registration_step = 'phone'
            from models import db
            db.session.commit()
        
        self.send_message(user.telegram_id, message)
    
    def handle_phone(self, user, phone_text):
        """Обработка ввода телефона"""
        from models import db
        
        # Очищаем номер
        phone = re.sub(r'[^\d+]', '', phone_text)
        
        # Проверяем формат (казахстанские номера)
        if not re.match(r'^(\+7|8|7)\d{10}$', phone):
            message = """
❌ <b>Неверный формат номера!</b>

Пожалуйста, отправьте номер в правильном формате:
• +77051234567
• 87051234567
• 77051234567

Попробуйте еще раз:
            """
            self.send_message(user.telegram_id, message)
            return
        
        # Нормализуем номер к формату +7XXXXXXXXXX
        if phone.startswith('8'):
            phone = '+7' + phone[1:]
        elif phone.startswith('7') and not phone.startswith('+7'):
            phone = '+' + phone
        
        # Сохраняем телефон и завершаем регистрацию
        user.phone = phone
        user.is_verified = True
        user.registration_step = 'verified'
        db.session.commit()
        
        message = f"""
✅ <b>Регистрация завершена!</b>

📞 Ваш номер: {phone}

Теперь вы будете получать уведомления о ваших заявках в Telegram!

<b>Что дальше?</b>
1. Заказывайте праздники на сайте prazdnikvdom.kz
2. Указывайте этот же номер телефона при заказе
3. Получайте уведомления прямо сюда!

<b>Команды:</b>
/my_bookings - Мои заявки
/help - Справка
        """
        
        self.send_message(user.telegram_id, message)
    
    def handle_my_bookings(self, user):
        """Показать заявки пользователя"""
        if not user.is_verified:
            message = """
❌ <b>Регистрация не завершена</b>

Сначала зарегистрируйтесь с помощью команды /start
            """
            self.send_message(user.telegram_id, message)
            return
        
        # Получаем заявки
        bookings = user.get_recent_bookings(5)
        
        if not bookings:
            message = """
📋 <b>Заявки не найдены</b>

У вас пока нет заявок в системе.

🌐 Сделайте заказ на сайте prazdnikvdom.kz и получите уведомление!
            """
        else:
            message = "📋 <b>Ваши последние заявки:</b>\n\n"
            
            for booking in bookings:
                status_emoji = {
                    'new': '🆕',
                    'confirmed': '✅', 
                    'cancelled': '❌',
                    'completed': '🎉'
                }.get(booking.status, '📝')
                
                service_name = booking.service.title if booking.service else 'Не указана'
                event_date = booking.event_date.strftime('%d.%m.%Y') if booking.event_date else 'Не указана'
                
                status_text = {
                    'new': 'Новая заявка',
                    'confirmed': 'Подтверждена',
                    'cancelled': 'Отменена', 
                    'completed': 'Выполнена'
                }.get(booking.status, booking.status)
                
                message += f"""
{status_emoji} <b>Заявка #{booking.id}</b>
🎪 {service_name}
📅 {event_date}
📊 {status_text}
🕐 {booking.created_at.strftime('%d.%m.%Y')}

"""
        
        self.send_message(user.telegram_id, message)
    
    def handle_help(self, user):
        """Справка"""
        message = """
🎪 <b>Справка - Королевство Чудес</b>

<b>Команды бота:</b>
/start - Регистрация в системе уведомлений
/my_bookings - Показать мои заявки
/help - Эта справка

<b>Как это работает:</b>
1️⃣ Зарегистрируйтесь в боте (/start)
2️⃣ Укажите свой номер телефона
3️⃣ Заказывайте праздники на сайте с этим номером
4️⃣ Получайте уведомления о статусе заявок!

<b>Контакты:</b>
📞 +7 (XXX) XXX-XX-XX
🌐 prazdnikvdom.kz
📧 info@prazdnikvdom.kz
        """
        
        self.send_message(user.telegram_id, message)
    
    def start_listening(self):
        """Запуск прослушивания"""
        print("🤖 Запуск Telegram Bot для уведомлений...")
        print(f"📡 Режим: Long Polling")
        print("💬 Ожидание регистраций пользователей...")
        print("=" * 50)
        
        # Проверяем подключение к боту
        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            if response.json().get('ok'):
                bot_info = response.json()['result']
                print(f"✅ Бот подключен: @{bot_info['username']}")
            else:
                print("❌ Ошибка подключения к боту")
                return
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return
        
        # Удаляем webhook
        try:
            requests.post(f"{self.base_url}/deleteWebhook", timeout=10)
            # print("🗑️ Webhook удален")
        except:
            pass
        
        self.running = True
        
        # Основной цикл
        while self.running:
            try:
                updates = self.get_updates(offset=self.last_update_id + 1)
                
                if not updates.get('ok'):
                    time.sleep(5)
                    continue
                
                messages = updates.get('result', [])
                
                for update in messages:
                    try:
                        self.last_update_id = update['update_id']
                        
                        if 'message' in update:
                            self.process_message(update['message'])
                    
                    except Exception as e:
                        print(f"❌ Ошибка обработки: {e}")
                        continue
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n⏹️ Остановка бота...")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                time.sleep(10)
        
        print("✅ Бот остановлен")

# Функции для отправки уведомлений (основная задача!)
def send_booking_notification(phone, message):
    """Отправить уведомление пользователю по номеру телефона"""
    try:
        from app import create_app
        from models import TelegramUser
        
        app = create_app()
        with app.app_context():
            # Находим пользователя по телефону
            user = TelegramUser.query.filter_by(phone=phone, is_verified=True).first()
            
            if not user:
                print(f"❌ Пользователь с телефоном {phone} не найден в Telegram")
                return False
            
            # Отправляем уведомление
            bot = SimpleTelegramBot()
            result = bot.send_message(user.telegram_id, message)
            
            if result:
                print(f"✅ Уведомление отправлено: {phone}")
                return True
            else:
                print(f"❌ Ошибка отправки уведомления: {phone}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления: {e}")
        return False

def send_booking_created_notification(booking):
    """Уведомление о создании заявки"""
    if not booking.phone:
        return False
    
    service_name = booking.service.title if booking.service else 'Не указана'
    event_date = booking.event_date.strftime('%d.%m.%Y') if booking.event_date else 'Не указана'
    
    message = f"""
🎉 <b>Новая заявка принята!</b>

<b>Заявка #{booking.id}</b>
🎪 Услуга: {service_name}
📅 Дата: {event_date}
👤 Имя: {booking.name}

✅ Мы получили вашу заявку и скоро свяжемся с вами!

📞 Вопросы: +7 (XXX) XXX-XX-XX
    """
    
    return send_booking_notification(booking.phone, message)

def send_booking_confirmed_notification(booking):
    """Уведомление о подтверждении заявки"""
    if not booking.phone:
        return False
    
    service_name = booking.service.title if booking.service else 'Не указана'
    event_date = booking.event_date.strftime('%d.%m.%Y') if booking.event_date else 'Не указана'
    event_time = booking.event_time.strftime('%H:%M') if booking.event_time else 'Не указано'
    
    message = f"""
✅ <b>Заявка подтверждена!</b>

<b>Заявка #{booking.id}</b>
🎪 Услуга: {service_name}
📅 Дата: {event_date}
🕐 Время: {event_time}
📍 Место: {booking.location or 'Будет уточнено'}

🎉 Ваш праздник состоится! Мы готовимся к волшебству!

📞 Контакт: +7 (XXX) XXX-XX-XX
    """
    
    return send_booking_notification(booking.phone, message)

def send_booking_cancelled_notification(booking):
    """Уведомление об отмене заявки"""
    if not booking.phone:
        return False
    
    message = f"""
😔 <b>Заявка отменена</b>

<b>Заявка #{booking.id}</b>
К сожалению, заявка была отменена.

💬 Если у вас есть вопросы, свяжитесь с нами:
📞 +7 (XXX) XXX-XX-XX

Мы поможем организовать ваш идеальный праздник! 🎪
    """
    
    return send_booking_notification(booking.phone, message)

def send_booking_completed_notification(booking):
    """Уведомление о завершении заявки"""
    if not booking.phone:
        return False
    
    message = f"""
🎉 <b>Праздник завершен!</b>

<b>Заявка #{booking.id}</b>
Спасибо, что выбрали Королевство Чудес!

Надеемся, праздник получился волшебным! ✨

🌟 Поделитесь впечатлениями - оставьте отзыв на сайте!

📞 Заказать еще один праздник: +7 (XXX) XXX-XX-XX
🌐 prazdnikvdom.kz
    """
    
    return send_booking_notification(booking.phone, message)

def main():
    """Главная функция"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            # Тест отправки уведомления
            if len(sys.argv) > 3:
                phone = sys.argv[2]
                message = " ".join(sys.argv[3:])
                result = send_booking_notification(phone, message)
                print(f"Результат: {'✅ Отправлено' if result else '❌ Ошибка'}")
            else:
                print("Использование: python simple_telegram_bot.py test +77051234567 'Тестовое сообщение'")
            return
        
        elif command == "info":
            # Информация о боте
            try:
                response = requests.get(f"{BASE_URL}/getMe", timeout=10)
                if response.json().get('ok'):
                    bot_info = response.json()['result']
                    print(f"🤖 Бот: @{bot_info['username']}")
                    print(f"   ID: {bot_info['id']}")
                    print(f"   Имя: {bot_info['first_name']}")
                else:
                    print("❌ Ошибка получения информации")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
            return
    
    # Запуск бота
    bot = SimpleTelegramBot()
    try:
        bot.start_listening()
    except KeyboardInterrupt:
        print("\n⏹️ Остановка...")

if __name__ == "__main__":
    main()