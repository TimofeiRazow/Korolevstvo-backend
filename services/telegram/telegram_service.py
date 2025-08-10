import os
import logging
import asyncio
import json
from datetime import datetime
from flask import Flask, request, jsonify
from telegram import Bot
from telegram.ext import Application, CommandHandler
import threading
import time
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    API_PORT = int(os.getenv('TELEGRAM_PORT', 5001))
    API_HOST = os.getenv('TELEGRAM_HOST', '0.0.0.0')

app = Flask(__name__)

class TelegramNotificationService:
    def __init__(self):
        self.bot = None
        self.application = None
        self.is_running = False
        self.loop = None
        self.chat_ids = set()  # Простое хранение chat_id в памяти
        
    async def initialize_bot(self):
        """Инициализация Telegram бота"""
        try:
            if Config.TELEGRAM_BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
                logger.error("❌ Токен бота не установлен!")
                return False
                
            self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
            
            # Проверяем, что бот работает
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Бот подключен: @{bot_info.username} ({bot_info.first_name})")
            
            # Создаем приложение
            self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
            
            # Регистрируем только команду /start
            self.application.add_handler(CommandHandler("start", self.start_command))
            
            logger.info("✅ Обработчик команды /start зарегистрирован")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации бота: {e}")
            return False
    
    async def start_polling(self):
        """Запуск polling"""
        try:
            self.loop = asyncio.get_event_loop()
            
            logger.info("🔄 Инициализация бота...")
            success = await self.initialize_bot()
            
            if not success:
                logger.error("❌ Не удалось инициализировать бота")
                return
            
            self.is_running = True
            logger.info("🚀 Запуск бота в режиме polling...")
            
            # Инициализируем приложение
            await self.application.initialize()
            await self.application.start()
            
            # Запускаем polling
            await self.application.updater.start_polling(
                poll_interval=1.0,
                timeout=10,
                read_timeout=2,
                write_timeout=2,
                connect_timeout=2,
                pool_timeout=1
            )
            
            logger.info("✅ Бот успешно запущен")
            logger.info("📱 Теперь можете писать боту в Telegram!")
            
            # Держим бота активным
            while self.is_running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Получен сигнал остановки...")
        except Exception as e:
            logger.error(f"❌ Ошибка в polling: {e}")
        finally:
            await self.stop_polling()
    
    async def stop_polling(self):
        """Остановка polling"""
        try:
            self.is_running = False
            logger.info("🔄 Остановка бота...")
            
            if self.application:
                if self.application.updater and self.application.updater.running:
                    await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                
            logger.info("✅ Бот остановлен")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при остановке бота: {e}")
    
    def run_async_in_thread(self, coro):
        """Запуск корутины в event loop основного потока"""
        if self.loop and self.loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, self.loop)
            try:
                return future.result(timeout=10)
            except Exception as e:
                logger.error(f"❌ Ошибка выполнения async операции: {e}")
                return None
        else:
            logger.error("❌ Event loop не доступен")
            return None
    
    async def start_command(self, update, context):
        """Обработчик команды /start - отправляет chat_id пользователю"""
        try:
            user = update.effective_user
            chat_id = update.effective_chat.id
            
            # Добавляем chat_id в наш список
            self.chat_ids.add(chat_id)
            
            logger.info(f"📝 Получена команда /start от пользователя: {user.first_name} (@{user.username}) Chat ID: {chat_id}")
            
            welcome_text = f"""🎭 **Добро пожаловать!**

Привет, {user.first_name}! 👋

📋 **Ваш Chat ID для уведомлений:**
```
{chat_id}
```

💡 Сохраните этот ID и передайте администратору для настройки уведомлений.

🔔 Теперь вы будете получать уведомления на этот аккаунт."""
            
            await update.message.reply_text(welcome_text, parse_mode='Markdown')
            logger.info(f"✅ Chat ID {chat_id} отправлен пользователю {user.id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в start_command: {e}")
            try:
                await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
            except:
                pass
    
    async def send_notification(self, chat_id, booking):
        """Отправить уведомление в указанные чаты"""
        message_text = f"""
🎉 **НОВАЯ ЗАЯВКА НА БРОНИРОВАНИЕ**

👤 **Клиент:** {booking['name']}
📱 **Телефон:** {booking['phone']}
📧 **Email:** {booking['email'] or 'Не указан'}

📋 **Детали заявки:**
    **Дата мероприятия:** {datetime.strptime(booking['event_date'], '%Y-%m-%d').strftime('%d.%m.%Y') if booking['event_date'] else 'Не указана'}
    **Время:** {datetime.strptime(booking['event_time'], '%H:%M:%S').strftime('%H:%M') if booking['event_time'] else 'Не указано'}
    **Количество гостей:** {booking['guests_count'] or 'Не указано'}

💬 **Сообщение от клиента:**
    {booking['message'] or 'Сообщение не оставлено'}

⏰ **Время создания заявки:** 
    {datetime.now().strftime('%d.%m.%Y в %H:%M')}
"""

        try:
            if not self.bot:
                logger.error("❌ Бот не инициализирован")
                return False
            
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode='Markdown'
                )
                sent_count += 1
                logger.info(f"✅ Уведомление отправлено в чат {chat_id}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка отправки в чат {chat_id}: {e}")
            
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка в send_notification: {e}")
            return False

# Глобальный экземпляр сервиса
notification_service = TelegramNotificationService()

# Flask API маршруты
@app.route('/send-notification', methods=['POST'])
def send_notification():
    """API для отправки уведомлений"""
    try:
        data = request.get_json()
        print(data)
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
        
        # Получаем список chat_id для отправки
        chat_id = data.get('chat_id', [])
        booking = data.get('booking', dict())
        
        if not chat_id:
            return jsonify({'error': 'Нет получателей для отправки'}), 400
        
        if not booking:
            return jsonify({'error': 'Заявка не может быть пустой'}), 400
        
        # Отправляем уведомление
        if notification_service.bot and notification_service.is_running:
            result = notification_service.run_async_in_thread(
                notification_service.send_notification(chat_id, booking)
            )
            
            if result:
                return jsonify({
                    'status': 'sent',
                    'message': 'Уведомление отправлено'
                })
            else:
                return jsonify({
                    'status': 'not_sent',
                    'message': 'Уведомление не отправлено'
                })
        else:
            return jsonify({
                'status': 'not_sent',
                'message': 'Бот не инициализирован или не запущен'
            })
    
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-chat-ids', methods=['GET'])
def get_chat_ids():
    """Получить список всех известных chat_id"""
    try:
        return jsonify({
            'chat_ids': list(notification_service.chat_ids),
            'count': len(notification_service.chat_ids)
        })
    except Exception as e:
        logger.error(f"❌ Ошибка получения chat_ids: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья сервиса"""
    try:
        bot_status = notification_service.bot is not None
        polling_status = notification_service.is_running
        
        return jsonify({
            'status': 'healthy',
            'bot': 'initialized' if bot_status else 'not_initialized',
            'polling': 'running' if polling_status else 'stopped',
            'known_chats': len(notification_service.chat_ids),
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/bot-info', methods=['GET'])
def bot_info():
    """Получить информацию о боте"""
    try:
        if notification_service.bot and notification_service.is_running:
            bot_data = notification_service.run_async_in_thread(
                notification_service.bot.get_me()
            )
            
            if bot_data:
                return jsonify({
                    'bot_id': bot_data.id,
                    'username': bot_data.username,
                    'first_name': bot_data.first_name,
                    'status': 'active'
                })
            else:
                return jsonify({'error': 'Не удалось получить информацию о боте'}), 500
        else:
            return jsonify({'error': 'Бот не инициализирован или не запущен'}), 404
    
    except Exception as e:
        logger.error(f"❌ Ошибка в bot_info: {e}")
        return jsonify({'error': str(e)}), 500

def run_flask_api():
    """Запуск Flask API в отдельном потоке"""
    try:
        logger.info(f"🌐 Запуск Flask API на http://{Config.API_HOST}:{Config.API_PORT}")
        app.run(
            host=Config.API_HOST,
            port=Config.API_PORT,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        logger.error(f"❌ Ошибка Flask API: {e}")

def main():
    """Главная функция запуска сервиса"""
    
    # Проверяем наличие токена бота
    if Config.TELEGRAM_BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("❌ Не задан токен Telegram бота!")
        logger.error("Установите переменную окружения TELEGRAM_BOT_TOKEN")
        return
    
    logger.info("🚀 Запуск упрощенного Telegram сервиса уведомлений")
    
    # Запускаем Flask API в отдельном потоке
    flask_thread = threading.Thread(target=run_flask_api, daemon=True)
    flask_thread.start()
    
    # Небольшая задержка для запуска Flask
    time.sleep(2)
    logger.info("✅ Flask API запущен")
    
    # Запускаем бота в основном потоке
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(notification_service.start_polling())
        
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки...")
    except Exception as e:
        logger.error(f"❌ Ошибка в main: {e}")
    finally:
        try:
            if notification_service.is_running:
                loop.run_until_complete(notification_service.stop_polling())
            loop.close()
        except Exception as e:
            logger.error(f"❌ Ошибка при завершении: {e}")

if __name__ == '__main__':
    main()
