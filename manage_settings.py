import sys
import json
from app import create_app
from models import db, Settings

def show_help():
    """Показать справку по командам"""
    help_text = """
Утилита управления настройками

Команды:
  list [category]           - Показать все настройки или настройки категории
  get <key>                - Получить значение настройки
  set <key> <value>        - Установить значение настройки
  delete <key>             - Удалить настройку
  export [file]            - Экспортировать настройки в JSON
  import <file>            - Импортировать настройки из JSON
  reset                    - Сбросить настройки к значениям по умолчанию
  backup <file>            - Создать резервную копию настроек

Категории:
  company, social, notifications, seo, integration

Примеры:
  python manage_settings.py list
  python manage_settings.py list company
  python manage_settings.py get company_name
  python manage_settings.py set company_name "Новое название"
  python manage_settings.py export settings_backup.json
"""
    print(help_text)

def list_settings(category=None):
    """Показать настройки"""
    if category:
        settings = Settings.get_settings_dict(category)
        if not settings:
            print(f"Настройки категории '{category}' не найдены")
            return
        print(f"\nНастройки категории '{category}':")
    else:
        settings = Settings.get_settings_dict()
        print("\nВсе настройки:")
    
    for key, value in settings.items():
        print(f"  {key}: {value}")
    print()

def get_setting(key):
    """Получить значение настройки"""
    value = Settings.get_setting(key)
    if value is not None:
        print(f"{key}: {value}")
    else:
        print(f"Настройка '{key}' не найдена")

def set_setting(key, value):
    """Установить значение настройки"""
    try:
        # Определяем тип значения
        value_type = 'string'
        if value.lower() in ('true', 'false'):
            value_type = 'boolean'
        elif value.replace('.', '').replace('-', '').isdigit():
            value_type = 'number'
        elif value.startswith('{') or value.startswith('['):
            value_type = 'json'
        
        Settings.update_setting(key, value, value_type)
        print(f"Настройка '{key}' установлена в '{value}'")
    except Exception as e:
        print(f"Ошибка при установке настройки: {e}")

def delete_setting(key):
    """Удалить настройку"""
    try:
        setting = Settings.query.filter(Settings.key == key).first()
        if setting:
            db.session.delete(setting)
            db.session.commit()
            print(f"Настройка '{key}' удалена")
        else:
            print(f"Настройка '{key}' не найдена")
    except Exception as e:
        print(f"Ошибка при удалении настройки: {e}")

def export_settings(filename=None):
    """Экспортировать настройки в JSON"""
    if not filename:
        filename = 'settings_export.json'
    
    try:
        settings = Settings.get_settings_dict()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        print(f"Настройки экспортированы в файл '{filename}'")
    except Exception as e:
        print(f"Ошибка при экспорте: {e}")

def import_settings(filename):
    """Импортировать настройки из JSON"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        for key, value in settings.items():
            # Определяем тип значения
            value_type = 'string'
            if isinstance(value, bool):
                value_type = 'boolean'
            elif isinstance(value, (int, float)):
                value_type = 'number'
            elif isinstance(value, (dict, list)):
                value_type = 'json'
                value = json.dumps(value, ensure_ascii=False)
            
            Settings.update_setting(key, str(value), value_type)
        
        print(f"Настройки импортированы из файла '{filename}'")
    except FileNotFoundError:
        print(f"Файл '{filename}' не найден")
    except json.JSONDecodeError:
        print(f"Ошибка в формате JSON файла '{filename}'")
    except Exception as e:
        print(f"Ошибка при импорте: {e}")

def reset_settings():
    """Сбросить настройки к значениям по умолчанию"""
    try:
        # Удаляем все существующие настройки
        Settings.query.delete()
        db.session.commit()
        
        # Инициализируем настройки по умолчанию
        Settings.init_default_settings()
        print("Настройки сброшены к значениям по умолчанию")
    except Exception as e:
        print(f"Ошибка при сбросе настроек: {e}")

def backup_settings(filename):
    """Создать резервную копию настроек"""
    try:
        settings_data = []
        all_settings = Settings.query.all()
        
        for setting in all_settings:
            settings_data.append({
                'key': setting.key,
                'value': setting.value,
                'value_type': setting.value_type,
                'category': setting.category,
                'description': setting.description
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(settings_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Резервная копия создана: '{filename}'")
    except Exception as e:
        print(f"Ошибка при создании резервной копии: {e}")

def main():
    """Основная функция CLI"""
    app = create_app()
    
    with app.app_context():
        if len(sys.argv) < 2:
            show_help()
            return
        
        command = sys.argv[1].lower()
        
        if command == 'help':
            show_help()
        elif command == 'list':
            category = sys.argv[2] if len(sys.argv) > 2 else None
            list_settings(category)
        elif command == 'get':
            if len(sys.argv) < 3:
                print("Укажите ключ настройки")
                return
            get_setting(sys.argv[2])
        elif command == 'set':
            if len(sys.argv) < 4:
                print("Укажите ключ и значение настройки")
                return
            set_setting(sys.argv[2], sys.argv[3])
        elif command == 'delete':
            if len(sys.argv) < 3:
                print("Укажите ключ настройки")
                return
            delete_setting(sys.argv[2])
        elif command == 'export':
            filename = sys.argv[2] if len(sys.argv) > 2 else None
            export_settings(filename)
        elif command == 'import':
            if len(sys.argv) < 3:
                print("Укажите файл для импорта")
                return
            import_settings(sys.argv[2])
        elif command == 'reset':
            confirmation = input("Вы уверены, что хотите сбросить все настройки? (y/N): ")
            if confirmation.lower() == 'y':
                reset_settings()
            else:
                print("Операция отменена")
        elif command == 'backup':
            if len(sys.argv) < 3:
                print("Укажите имя файла для резервной копии")
                return
            backup_settings(sys.argv[2])
        else:
            print(f"Неизвестная команда: {command}")
            show_help()

if __name__ == '__main__':
    main()