# utils/telegram_integration.py - Обновленная версия

import requests
import logging


logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Класс для отправки уведомлений в Telegram сервис"""
    
    def __init__(self, telegram_service_url='http://localhost:5001'):
        self.telegram_service_url = telegram_service_url.rstrip('/')
        self.enabled = True
    
    def get_telegram_chat_id(self):
        """
        Получить Chat ID из настроек системы
        
        Returns:
            str: Chat ID или None если не настроен
        """
        try:
            from models import Settings
            chat_id = Settings.get_setting('telegram_chat_id')
            return chat_id if chat_id else None
        except Exception as e:
            logger.error(f"Ошибка получения telegram_chat_id из настроек: {e}")
            return None
    
    def send_booking_notification(self, booking_data):
        """
        Отправить уведомление о заявке в Telegram бота по Chat ID из настроек
        
        Args:
            booking_data: dict с данными заявки или объект Booking
        
        Returns:
            bool: True если уведомление отправлено успешно
        """
        try:
            # Получаем Chat ID из настроек
            chat_id = self.get_telegram_chat_id()
            if not chat_id:
                logger.warning("⚠️ Telegram Chat ID не настроен в системе")
                return False
            
            # Если передан объект модели, преобразуем в словарь
            if hasattr(booking_data, 'to_dict'):
                booking_dict = booking_data.to_dict()
            else:
                booking_dict = booking_data
            
            # Проверяем обязательные поля
            if not booking_dict.get('id') or not booking_dict.get('name'):
                logger.error("Недостаточно данных для отправки уведомления")
                return False
            
            # Добавляем Chat ID к данным запроса
            notification_data = {
                'chat_id': chat_id,
                'booking': booking_dict
            }
            
            # Отправляем POST запрос к Telegram сервису
            response = requests.post(
                f"{self.telegram_service_url}/send-notification",
                json=notification_data,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'sent':
                    logger.info(f"✅ Telegram уведомление отправлено в чат {chat_id} для заявки #{booking_dict.get('id')}")
                    return True
                else:
                    logger.warning(f"⚠️ Telegram уведомление не отправлено: {result.get('message')}")
                    return False
            else:
                logger.error(f"❌ Ошибка Telegram сервиса: {response.status_code} - {response.text}")
                return False
        
        except requests.exceptions.ConnectionError:
            logger.error("❌ Telegram сервис недоступен (ConnectionError)")
            return False
        
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout при отправке в Telegram сервис")
            return False
        
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка отправки Telegram уведомления: {e}")
            return False
    
    def check_service_health(self):
        """
        Проверить состояние Telegram сервиса
        
        Returns:
            dict: Информация о состоянии сервиса
        """
        try:
            response = requests.get(
                f"{self.telegram_service_url}/health",
                timeout=5
            )
            
            if response.status_code == 200:
                health_data = response.json()
                # Добавляем информацию о настроенном Chat ID
                chat_id = self.get_telegram_chat_id()
                health_data['chat_id_configured'] = bool(chat_id)
                health_data['chat_id'] = chat_id if chat_id else None
                return health_data
            else:
                return {
                    'status': 'unhealthy',
                    'error': f'HTTP {response.status_code}',
                    'chat_id_configured': False
                }
        
        except Exception as e:
            return {
                'status': 'unreachable',
                'error': str(e),
                'chat_id_configured': False
            }
    
    def validate_chat_id(self, chat_id):
        """
        Проверить валидность Chat ID через Telegram API
        
        Args:
            chat_id: Chat ID для проверки
        
        Returns:
            dict: Результат валидации
        """
        try:
            validation_data = {'chat_id': chat_id}
            
            response = requests.post(
                f"{self.telegram_service_url}/validate-chat",
                json=validation_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'valid': result.get('valid', False),
                    'message': result.get('message', ''),
                    'chat_info': result.get('chat_info', {})
                }
            else:
                return {
                    'valid': False,
                    'message': f'Ошибка сервиса: {response.status_code}',
                    'chat_info': {}
                }
        
        except Exception as e:
            logger.error(f"Ошибка валидации Chat ID: {e}")
            return {
                'valid': False,
                'message': str(e),
                'chat_info': {}
            }
    
    def get_telegram_admins(self):
        """
        Получить список Telegram администраторов
        
        Returns:
            list: Список администраторов или пустой список в случае ошибки
        """
        try:
            response = requests.get(
                f"{self.telegram_service_url}/admins",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('admins', [])
            else:
                logger.error(f"Ошибка получения администраторов: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Ошибка запроса администраторов: {e}")
            return []
    
    def activate_admin(self, admin_id):
        """
        Активировать Telegram администратора
        
        Args:
            admin_id: ID администратора
        
        Returns:
            bool: True если активация успешна
        """
        try:
            response = requests.post(
                f"{self.telegram_service_url}/admins/{admin_id}/activate",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Администратор {admin_id} активирован: {result.get('message')}")
                return True
            else:
                logger.error(f"Ошибка активации администратора: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Ошибка запроса активации: {e}")
            return False
    
    def deactivate_admin(self, admin_id):
        """
        Деактивировать Telegram администратора
        
        Args:
            admin_id: ID администратора
        
        Returns:
            bool: True если деактивация успешна
        """
        try:
            response = requests.post(
                f"{self.telegram_service_url}/admins/{admin_id}/deactivate",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Администратор {admin_id} деактивирован: {result.get('message')}")
                return True
            else:
                logger.error(f"Ошибка деактивации администратора: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Ошибка запроса деактивации: {e}")
            return False

# Глобальный экземпляр для использования в проекте
telegram_notifier = TelegramNotifier()

# Функция для использования в routes/bookings.py
def send_telegram_booking_notification(booking):
    """
    Удобная функция для отправки уведомления о заявке
    
    Args:
        booking: Объект Booking или словарь с данными заявки
    
    Returns:
        bool: True если уведомление отправлено
    """
    return telegram_notifier.send_booking_notification(booking)

# Функция проверки настроек
def is_telegram_notifications_enabled():
    """
    Проверить включены ли Telegram уведомления в настройках
    И настроен ли Chat ID
    
    Returns:
        bool: True если уведомления включены и Chat ID настроен
    """
    try:
        from models import Settings
        notifications_enabled = Settings.get_setting('telegram_notifications', False)
        chat_id_configured = bool(Settings.get_setting('telegram_chat_id'))
        return notifications_enabled and chat_id_configured
    except:
        return False

# Функция для проверки и валидации настроек
def validate_telegram_settings():
    """
    Проверить все настройки Telegram
    
    Returns:
        dict: Статус настроек и возможные проблемы
    """
    try:
        from models import Settings
        
        notifications_enabled = Settings.get_setting('telegram_notifications', False)
        print(notifications_enabled)
        chat_id = Settings.get_setting('telegram_chat_id')
        print(chat_id)
        
        result = {
            'notifications_enabled': notifications_enabled,
            'chat_id_configured': bool(chat_id),
            'chat_id': chat_id,
            'service_available': False,
            'issues': []
        }
        print(result)
        
        if not notifications_enabled:
            result['issues'].append('Telegram уведомления отключены в настройках')
        
        if not chat_id:
            result['issues'].append('Chat ID не настроен')
        
        result['ready'] = (
            notifications_enabled and 
            bool(chat_id) and 
            result['service_available']
        )
        
        return result
        
    except Exception as e:
        return {
            'notifications_enabled': False,
            'chat_id_configured': False,
            'chat_id': None,
            'service_available': False,
            'ready': False,
            'issues': [f'Ошибка проверки настроек: {str(e)}']
        }