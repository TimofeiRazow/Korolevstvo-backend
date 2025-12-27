#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Скрипт для проверки шоу в базе данных"""

from app import create_app
from models import db, Show

def check_shows():
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("ПРОВЕРКА ШОУ В БАЗЕ ДАННЫХ")
        print("=" * 60)

        # Путь к базе данных
        print(f"\n📁 База данных: {app.config['SQLALCHEMY_DATABASE_URI']}")

        # Количество шоу
        total = Show.query.count()
        print(f"\n📊 Всего шоу в базе: {total}")

        # Список всех шоу
        shows = Show.query.all()

        if shows:
            print("\n✨ СПИСОК ШОУ:")
            print("-" * 60)
            for show in shows:
                print(f"\nID: {show.id}")
                print(f"  Название: {show.title}")
                print(f"  Категория: {show.category}")
                print(f"  Статус: {show.status}")
                print(f"  Создано: {show.created_at}")
                print(f"  Featured: {show.featured}")
        else:
            print("\n❌ Шоу не найдены!")
            print("\nВозможные причины:")
            print("  1. База данных пустая")
            print("  2. Используется другая база данных")
            print("  3. Таблица не создана (нужна миграция)")

        print("\n" + "=" * 60)

if __name__ == "__main__":
    check_shows()
