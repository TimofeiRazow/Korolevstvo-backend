#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Простой скрипт для проверки шоу в базе данных (без зависимостей от других модулей)"""

import sqlite3
import os

def check_database():
    """Проверить содержимое базы данных напрямую через SQLite"""

    # Путь к базе данных
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'korolevstvo_chudes.db')

    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return

    print("=" * 70)
    print("PROVERKA BAZY DANNYKH NAPRYAMUYU (SQLite)")
    print("=" * 70)
    print(f"\nPut k BD: {db_path}")
    print(f"Razmer BD: {os.path.getsize(db_path) / 1024:.2f} KB")

    # Подключаемся к базе
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Проверяем существование таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shows'")
        table_exists = cursor.fetchone()

        if not table_exists:
            print("\n❌ Таблица 'shows' не существует!")
            print("\nВыполните миграции базы данных:")
            print("  flask db upgrade")
            return

        print("\n✅ Таблица 'shows' существует")

        # Получаем структуру таблицы
        cursor.execute("PRAGMA table_info(shows)")
        columns = cursor.fetchall()

        print(f"\n📋 Структура таблицы ({len(columns)} колонок):")
        print("-" * 70)
        for col in columns:
            print(f"  • {col[1]:20} {col[2]:15} {'NOT NULL' if col[3] else ''}")

        # Получаем количество записей
        cursor.execute("SELECT COUNT(*) FROM shows")
        total = cursor.fetchone()[0]

        print(f"\n📊 Всего записей в таблице: {total}")

        if total == 0:
            print("\n⚠️  База данных пустая!")
            print("Создайте шоу через админ-панель или импортируйте данные.")
            return

        # Получаем все шоу
        cursor.execute("""
            SELECT id, title, category, status, featured, created_at, views_count, bookings_count
            FROM shows
            ORDER BY created_at DESC
        """)
        shows = cursor.fetchall()

        print(f"\n✨ СПИСОК ШОУ ({len(shows)} записей):")
        print("=" * 70)

        for show in shows:
            show_id, title, category, status, featured, created_at, views, bookings = show
            print(f"\n┌─ ID: {show_id}")
            print(f"│  📌 Название: {title}")
            print(f"│  🏷️  Категория: {category}")
            print(f"│  🚦 Статус: {status}")
            print(f"│  ⭐ Featured: {'Да' if featured else 'Нет'}")
            print(f"│  👁️  Просмотры: {views or 0}")
            print(f"│  📅 Бронирования: {bookings or 0}")
            print(f"│  🕐 Создано: {created_at}")
            print(f"└{'─' * 68}")

        # Статистика по категориям
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM shows
            GROUP BY category
            ORDER BY count DESC
        """)
        categories = cursor.fetchall()

        print(f"\n📊 СТАТИСТИКА ПО КАТЕГОРИЯМ:")
        print("-" * 70)
        for cat, count in categories:
            print(f"  • {cat:15} {count:3} шт.")

        # Статистика по статусам
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM shows
            GROUP BY status
        """)
        statuses = cursor.fetchall()

        print(f"\n📊 СТАТИСТИКА ПО СТАТУСАМ:")
        print("-" * 70)
        for status, count in statuses:
            print(f"  • {status:15} {count:3} шт.")

        print("\n" + "=" * 70)
        print("✅ Проверка завершена успешно!")
        print("=" * 70)

    except sqlite3.Error as e:
        print(f"\n❌ Ошибка при работе с базой данных: {e}")

    finally:
        conn.close()

if __name__ == "__main__":
    check_database()
