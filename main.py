import disnake
from disnake.ext import commands, tasks
import sqlite3
import random
import json
import a2s
import sys
import asyncio
import aiohttp
import time
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta

from config import (
    AUTO_ROLE_ID,
    ALLOWED_MOD_ROLE_ID,
    ALLOWED_VOICE_ROLES,
    LOG_CHANNEL_ID,
    REMIND_CHANNEL_ID,
    TEMP_TEXT_CATEGORY_ID,
    TEMP_VOICE_CATEGORY_ID,
    ADMIN_ID,
    ALLOWED_GAME_CHANNEL_ID,
)


# НАСТРОЙКА WINDOWS
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

activity = disnake.Game(name="игру")

# Интенты
intents = disnake.Intents.default()
intents.members = True
intents.message_content = True

# Бот
bot = commands.InteractionBot(
    intents=intents,
    test_guilds=[1521854323905138759]
)


# База данных
def db_init():
    """Создает базу данных и таблицу для паролей."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_passwords (
            user_id INTEGER,
            title TEXT,
            password TEXT,
            vacation_info TEXT DEFAULT '-'
        )
    """)

    conn.commit()
    conn.close()


# Инициализация БД
db_init()


@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} успешно запущен!")
    print(f"🆔 ID: {bot.user.id}")
    print("📡 Slash-команды загружены.")


# Новый пользователь
@bot.event
async def on_member_join(member: disnake.Member):
    ROLE_ID = 1521855978394353664

    role = member.guild.get_role(ROLE_ID)

    if role is not None:
        try:
            await member.add_roles(role)

            print(
                f"[Авто-Роль]: Успешно выдана роль "
                f"{role.name} для {member.name}"
            )

        except disnake.Forbidden:
            print(
                "[Ошибка]: У бота нет прав для выдачи роли! "
                "Переместите роль бота ВЫШЕ роли новичка."
            )

        except Exception as e:
            print(f"[Ошибка авто-роли]: {e}")

    else:
        print(
            f"[Ошибка]: Роль с ID {ROLE_ID} "
            "не найдена на этом сервере."
        )


# Загрузка команд
bot.load_extension("moderation")
bot.load_extension("games")
bot.load_extension("passwords")
bot.load_extension("logs")
bot.load_extension("rules")



# =================================================================
# 7. МИКРО-ВЕБ-СЕРВЕР ДЛЯ ОБМАНА ХОСТИНГА RENDER
# =================================================================
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    bot.loop.create_task(asyncio.to_thread(server.serve_forever))

@bot.event
async def on_connect():
    run_web_server()


bot.run("MTUxNzI2Mjc1Mjk0OTczNTQ0NQ.G8VWyw.82N0IZHOC-sB6tXGipJT0qwCLeK7OdwTatGDcY")



