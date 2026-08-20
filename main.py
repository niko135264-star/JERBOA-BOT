import disnake
from disnake.ext import commands, tasks
from disnake.ext import tasks
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


# 1. НАСТРОЙКА WINDOWS
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

activity=disnake.Game(name="игру")

# Интенты для disnake
intents = disnake.Intents.default()
intents.members = True
intents.message_content = True

# Создание бота через disnake (ОСТАВЛЯЕМ ТОЛЬКО ОДНУ ИНИЦИАЛИЗАЦИЮ)
bot = commands.InteractionBot(intents=intents, test_guilds=[1521854323905138759])

# ID ролей
AUTO_ROLE_ID = 1521855978394353664
ALLOWED_MOD_ROLE_ID = 1521855842964471918

# Получить ключ можно бесплатно тут: https://steamcommunity.com
STEAM_API_KEY = "7143E9E381F9207D8698319C53C92B38" 
GMOD_APP_ID = 4000 # Официальный ID Garry's Mod в Steam

# ДВА РАЗРЕШЕННЫХ ID РОЛЕЙ ДЛЯ КОМАНДЫ АКТИВНОСТИ
ALLOWED_VOICE_ROLES = [1521855842964471918, 1521979923819004125]

# ID секретного канала, куда бот будет слать отчеты (логи)
LOG_CHANNEL_ID = 1532095199046537308 

# Настройки напоминалки
REMIND_CHANNEL_ID = 1539276527244541976  # ID канала, куда бот будет слать пинг
ADMIN_ID = 1484872373932130335            # Твой личный цифровой Discord ID для пинга

# ID категории, внутри которой бот будет создавать эти временные чаты
TEMP_TEXT_CATEGORY_ID = 1539312584669536327  

# ID категории, внутри которой бот будет создавать эти войсы
TEMP_VOICE_CATEGORY_ID = 1532095199046537308  

# Словари и вечная память для мини-игра и варнов
stats_minesweeper = {}     # Тут храним победы в Сапёре
stats_roulette = {}        # Тут храним победы в Рулетке
warns_strict = {}          # Тут храним строгие выговоры (0/3)
warns_light = {}           # Тут храним обычные преды (0/2)
stats_casino_wins = {}     # Тут храним обычные выигрыши в казино (нужно 5)
stats_casino_jackpots = {} # Тут храним джекпоты в казино (нужно 2)
cases_archive = {}         # ТУТ ДОБАВЛЯЕМ ПАМЯТЬ ДЛЯ АРХИВА ДЕЛ!
# Словарь в памяти для отслеживания созданных комнат {id_канала: id_создателя}
voice_channels_cache = {}

# Временная память бота для хранения удаленных сообщений (чтобы читать по кнопке)
deleted_messages_cache = {}

# 3. СОБЫТИЕ ЗАПУСКА
@bot.event
async def on_ready():
    print(f"=======================================")
    print(f"Бот {bot.user} успешно запущен!")
    print(f"=======================================")
    await bot.change_presence(activity=None)
    check_long_timers.start()


# Событие: Новый пользователь зашел на сервер
@bot.event
async def on_member_join(member: disnake.Member):
    # Указываем ID вашей роли из запроса
    ROLE_ID = 1521855978394353664
    
    # Получаем объект роли по её ID на сервере
    role = member.guild.get_role(ROLE_ID)
    
    if role is not None:
        try:
            # Автоматически выдаем роль новичку
            await member.add_roles(role)
            print(f"[Авто-Роль]: Успешно выдана роль {role.name} для {member.name}")
        except disnake.Forbidden:
            print(f"[Ошибка]: У бота нет прав для выдачи роли! Переместите роль бота ВЫШЕ роли новичка в настройках сервера.")
        except Exception as e:
            print(f"[Ошибка авто-роли]: {e}")
    else:
        print(f"[Ошибка]: Роль с ID {ROLE_ID} не найдена на этом сервере. Проверьте правильность ID!")

def db_init():
    """Создает файл базы данных и таблицу для паролей, если их нет"""
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

# ОБЯЗАТЕЛЬНО ПРОВЕРЬ, ЧТОБЫ ЭТА СТРОЧКА ВЫЗОВА БЫЛА ТУТ:
db_init()


# =================================================================
# 5. БЛОК СЛЕШ-КОМАНД МОДЕРАЦИИ И ИНФОРМАЦИИ
# =================================================================

# Команда 1: КИК (Красивая карточка)
@bot.slash_command(name="кик", description="Выгнать пользователя с сервера (Причина обязательна)")
@commands.has_any_role(1526250470849515688, 1521855914951442433, 1521855842964471918)
async def kick(ctx: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str):
    await member.kick(reason=reason)
    
    embed = disnake.Embed(
        title="👢 Изгнание участника",
        description=f"Пользователь {member.mention} был успешно кикнут с сервера.",
        color=disnake.Color.orange()
    )
    embed.add_field(name="Модератор:", value=ctx.author.mention, inline=True)
    embed.add_field(name="Причина:", value=reason, inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    
    await ctx.send(embed=embed)


# Команда 2: БАН (Красивая карточка по пингу)
@bot.slash_command(name="бан", description="Забанить пользователя на сервере (Причина обязательна)")
@commands.has_any_role(1526250470849515688, 1521855842964471918)
async def ban(ctx: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str):
    await member.ban(reason=reason)
    
    embed = disnake.Embed(
        title="🔒 Блокировка участника",
        description=f"Пользователь {member.mention} был навсегда забанен.",
        color=disnake.Color.red()
    )
    embed.add_field(name="Модератор:", value=ctx.author.mention, inline=True)
    embed.add_field(name="Причина:", value=reason, inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    
    await ctx.send(embed=embed)


# Команда 2.5: БАН ПО ЮЗЕР ИД (Только для Старшей Администрации)
@bot.slash_command(name="бан_ид", description="Забанить пользователя по его цифровому Discord ID (Только для Старшей Администрации)")
async def ban_by_id(ctx: disnake.ApplicationCommandInteraction, user_id: str, reason: str):
    mod_role = ctx.author.get_role(ALLOWED_MOD_ROLE_ID)
    if not mod_role:
        embed_no_perms = disnake.Embed(
            description="❌ У вас нет специальной роли для использования этой команды!",
            color=disnake.Color.red()
        )
        await ctx.send(embed=embed_no_perms, ephemeral=True)
        return

    try:
        numeric_id = int(user_id)
        user = await bot.get_or_fetch_user(numeric_id)
        
        if user:
            await ctx.guild.ban(user, reason=reason)
            
            embed = disnake.Embed(
                title="🔒 Блокировка по ID",
                description=f"Пользователь **{user.name}** (ID: {user.id}) был успешно забанен.",
                color=disnake.Color.red()
            )
            embed.add_field(name="Модератор:", value=ctx.author.mention, inline=True)
            embed.add_field(name="Причина:", value=reason, inline=True)
            if user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
                
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Не удалось найти пользователя с таким ID в базе Discord.", ephemeral=True)
            
    except ValueError:
        await ctx.send("❌ Ошибка: Введённый ID должен состоять только из цифр!", ephemeral=True)
    except disnake.NotFound:
        await ctx.send("❌ Пользователь с таким ID не существует.", ephemeral=True)
    except Exception as e:
        await ctx.send(f"❌ Произошла ошибка при попытке бана: {e}", ephemeral=True)


# Команда 3: РАЗБАН ПО ID (С исправленным перебором)
@bot.slash_command(name="разбан", description="Разбанить пользователя по его цифровому Discord ID")
async def unban(ctx: disnake.ApplicationCommandInteraction, user_id: str):
    mod_role = ctx.author.get_role(ALLOWED_MOD_ROLE_ID)
    if not mod_role:
        embed_no_perms = disnake.Embed(
            description="❌ У вас нет специальной роли для использования этой команды!",
            color=disnake.Color.red()
        )
        await ctx.send(embed=embed_no_perms, ephemeral=True)
        return

    try:
        numeric_id = int(user_id)
        
        async for ban_entry in ctx.guild.bans():
            user = ban_entry.user
            if numeric_id == user.id:
                await ctx.guild.unban(user)
                
                embed = disnake.Embed(
                    title="🔓 Снятие блокировки по ID",
                    description=f"Пользователь **{user.name}** (ID: {user.id}) был успешно разбанен.",
                    color=disnake.Color.green()
                )
                embed.add_field(name="Модератор:", value=ctx.author.mention, inline=True)
                if user.avatar:
                    embed.set_thumbnail(url=user.avatar.url)
                    
                await ctx.send(embed=embed)
                return
                
        await ctx.send("❌ Этот пользователь не найден в списке банов вашего сервера.", ephemeral=True)
            
    except ValueError:
        await ctx.send("❌ Ошибка: Введённый ID должен состоять только из цифр!", ephemeral=True)
    except Exception as e:
        await ctx.send(f"❌ Произошла ошибка при попытке разбана: {e}", ephemeral=True)


# Команда 4: ВЫДАТЬ РОЛЬ (Красивая карточка)
@bot.slash_command(name="выдать_роль", description="Выдать роль пользователю")
@commands.has_any_role(1526250470849515688, 1521855914951442433, 1521855842964471918)
async def addrole(ctx: disnake.ApplicationCommandInteraction, member: disnake.Member, role: disnake.Role):
    if role in member.roles:
        embed = disnake.Embed(description=f"⚠️ У {member.mention} уже есть роль {role.mention}!", color=disnake.Color.gold())
        await ctx.send(embed=embed, ephemeral=True)
    else:
        await member.add_roles(role)
        embed = disnake.Embed(
            title="💼 Выдача роли",
            description=f"Пользователю успешно присвоена новая роль.",
            color=disnake.Color.blue()
        )
        embed.add_field(name="Кому:", value=member.mention, inline=True)
        embed.add_field(name="Роль:", value=role.mention, inline=True)
        await ctx.send(embed=embed)


# Команда 5: УДАЛИТЬ РОЛЬ (Красивая карточка)
@bot.slash_command(name="убрать_роль", description="Забрать роль у пользователя")
@commands.has_any_role(1526250470849515688, 1521855914951442433,1521855842964471918)
async def removerole(ctx: disnake.ApplicationCommandInteraction, member: disnake.Member, role: disnake.Role):
    if role not in member.roles:
        embed = disnake.Embed(description=f"⚠️ У {member.mention} нет роли {role.mention}!", color=disnake.Color.gold())
        await ctx.send(embed=embed, ephemeral=True)
    else:
        await member.remove_roles(role)
        embed = disnake.Embed(
            title="❌ Снятие роли",
            description=f"У пользователя успешно забрана роль.",
            color=disnake.Color.dark_gray()
        )
        embed.add_field(name="У кого:", value=member.mention, inline=True)
        embed.add_field(name="Роль:", value=role.mention, inline=True)
        await ctx.send(embed=embed)


    
# Команда: БАН-МУТ (обычным сплошным текстом, без карточки и надписи автора)
@bot.slash_command(
    name="бан-мут", description="Заполнить форму наказания для пользователя обычным текстом"
)
@commands.has_any_role(1526250470849515688, 1521855914951442433, 1521855842964471918)
async def ban_mut_form(
    ctx: disnake.ApplicationCommandInteraction,
    member: disnake.User,
    наказание: str = commands.Param(choices=["Мут", "Бан", "ЧС", "Кик из банды",]),
    срок: str = commands.Param(description="Например: 1 день, 3 часа, навсегда"),
    причина: str = commands.Param(description="Укажите пункт правил или причину"),
):

    # Формируем сплошной текст (символ \n переносит строки, чтобы текст не слипался)
    rules_text = (
        f"**Пользователь:** {member.mention}\n"
        f"**Получает:** {наказание} на **{срок}**\n"
        f"**Причина:** {причина}\n"
        f"-# Выдал модератор: `{ctx.author.name}`"
    )

   # 1. Отправляем форму текстом в канал и сразу закрываем слэш-команду для Discord
    await ctx.channel.send(content=rules_text)
    await ctx.response.send_message("✅ Успешно отправлено!", ephemeral=True)

# КОМАНДА: МАССОВАЯ ОЧИСТКА ЧАТА ОТ ФЛУДА (ИСПРАВЛЕННАЯ)
@bot.slash_command(name="очистить", description="Удалить указанное количество сообщений из чата")
async def clear_messages(
    ctx: disnake.ApplicationCommandInteraction, 
    количество: int = commands.Param(description="Сколько сообщений удалить (например: 10, 50, 100)")
):
    # Проверяем права модератора по списку твоих разрешенных ролей
    has_permission = any(ctx.author.get_role(role_id) for role_id in ALLOWED_VOICE_ROLES)
    if not has_permission:
        await ctx.send("❌ У вас нет специальной роли для использования этой команды!", ephemeral=True)
        return

    # Защита от дурака
    if количество < 1 or количество > 100:
        await ctx.send("❌ Можно удалить от 1 до 100 сообщений за раз!", ephemeral=True)
        return

    # Сначала говорим Дискорду, что бот выполняет тяжелую задачу (это убирает баги с правами)
    await ctx.response.defer(ephemeral=True)

    try:
        # Запускаем очистку сообщений в текущем канале
        deleted = await ctx.channel.purge(limit=количество)
        
        # Отправляем подтверждение, которое видишь ТОЛЬКО ТЫ (оно не засоряет чат)
        await ctx.edit_original_response(content=f"🗑️ Успешно удалено сообщений: **{len(deleted)}**.")
        
    except disnake.Forbidden:
        # Если даже после этого вылезет ошибка, бот сам честно напишет в админ-панель
        await ctx.edit_original_response(
            content="❌ Критическая ошибка Дискорда! Бот не может очистить чат.\n"
                    "**Как исправить:** Зайдите в настройки этого канала -> Права доступа -> "
                    "Добавьте роль `Raccoonclaw Mafia Bot` лично и включите ей зелёную галочку "
                    "напротив пункта 'Управлять сообщениями' и 'Читать историю сообщений'!"
        )
    except Exception as e:
        await ctx.edit_original_response(content=f"❌ Техническая ошибка при очистке: {e}")

#ВРЕМ РОЛЬ 7
@bot.slash_command(name="врем_роль", description="Выдать пользователю роль на определенное время")
@commands.has_any_role(1526250470849515688, 1521855914951442433, 1521855842964471918)
async def temp_role(
    ctx: disnake.ApplicationCommandInteraction,
    member: disnake.Member,
    role: disnake.Role,
    время: int = commands.Param(description="Укажите число времени (например: 10, 5, 2)"),
    тип: str = commands.Param(choices=["Секунды", "Минуты", "Часы", "Дни"])
):
    # Удобный подсчет времени через словарь
    time_multipliers = {"Секунды": 1, "Минуты": 60, "Часы": 3600, "Дни": 86400}
    seconds = время * time_multipliers[тип]
    end_timestamp = int(time.time() + seconds)

    # Проверка на наличие роли
    if role in member.roles:
        embed = disnake.Embed(description=f"⚠️ У {member.mention} уже есть роль {role.mention}!", color=disnake.Color.gold())
        return await ctx.send(embed=embed, ephemeral=True)

    try:
        # Выдаем роль
        await member.add_roles(role, reason="Выдача временной роли (начало срока)")
        
        embed_start = disnake.Embed(
            title="⏱️ Выдана временная роль",
            description="Пользователю успешно выдана роль на заданный срок.",
            color=disnake.Color.purple()
        )
        embed_start.add_field(name="Кому:", value=member.mention, inline=True)
        embed_start.add_field(name="Роль:", value=role.mention, inline=True)
        # Показывает точное время окончания часового пояса каждого участника
        embed_start.add_field(name="Истекает:", value=f"<t:{end_timestamp}:F> (<t:{end_timestamp}:R>)", inline=False)
        await ctx.send(embed=embed_start)

        # Ожидание окончания срока роли
        await asyncio.sleep(seconds)

        # Получаем актуальный статус участника на сервере
        member_now = ctx.guild.get_member(member.id)
        if member_now and role in member_now.roles:
            await member_now.remove_roles(role, reason="Временная роль (истек срок)")
            
            embed_end = disnake.Embed(
                title="⏳ Время роли истекло",
                description=f"У пользователя {member_now.mention} была автоматически забрана временная роль {role.mention}.\n\n"
                            f"*🗑️ Это сообщение удалится через 10 секунд.*",
                color=0x2b2d31
            )
            # Отправляем обычное сообщение в канал, так как ctx к этому моменту уже «мертв»
            await ctx.channel.send(embed=embed_end, delete_after=10)

    except disnake.Forbidden:
        await ctx.send("❌ Ошибка: У бота нет прав (роль бота должна быть выше выдаваемой роли)!", ephemeral=True)
    except Exception as e:
        await ctx.send(f"❌ Критическая ошибка: {e}", ephemeral=True)


#ЗАМЕНИТЬ РОЛЬ НА ВРЕМЯ 7.1
@bot.slash_command(name="заменить_роль_время", description="Временно заменить одну роль на другую с авто-возвратом через время")
@commands.has_any_role(1526250470849515688, 1521855914951442433, 1521855842964471918)
async def replace_role_temp(
    ctx: disnake.ApplicationCommandInteraction,
    участник: disnake.Member,
    забрать_роль: disnake.Role,
    выдать_роль: disnake.Role,
    время: int = commands.Param(description="Число времени (например: 10, 5, 2)"),
    тип: str = commands.Param(choices=["Секунды", "Минуты", "Часы", "Дни"])
):
    # Словарь множителей времени
    time_multipliers = {"Секунды": 1, "Минуты": 60, "Часы": 3600, "Дни": 86400}
    seconds = время * time_multipliers[тип]
    end_timestamp = int(time.time() + seconds)

    # Проверки безопасности ролей
    if забрать_роль not in участник.roles:
        return await ctx.send(f"❌ У {участник.mention} нет роли {забрать_роль.mention}!", ephemeral=True)
    if выдать_роль in участник.roles:
        return await ctx.send(f"⚠️ У {участник.mention} уже есть роль {выдать_роль.mention}!", ephemeral=True)

    try:
        # Выполнение замены
        await участник.remove_roles(забрать_роль, reason="Временная замена роли (начало срока)")
        await участник.add_roles(выдать_роль, reason="Временная замена роли (начало срока)")

        embed_start = disnake.Embed(
            title="🔄 Временная замена роли",
            description="Роли участника успешно изменены.",
            color=disnake.Color.purple()
        )
        embed_start.add_field(name="Кому:", value=участник.mention, inline=False)
        embed_start.add_field(name="🗑️ Временно забрано:", value=забрать_роль.mention, inline=True)
        embed_start.add_field(name="💼 Временно выдано:", value=выдать_роль.mention, inline=True)
        # Динамический таймер Discord (показывает сколько осталось, например "через 2 часа")
        embed_start.add_field(name="⏱️ Истекает:", value=f"<t:{end_timestamp}:F> (<t:{end_timestamp}:R>)", inline=False)
        
        await ctx.send(embed=embed_start)

        # Ожидание окончания срока
        await asyncio.sleep(seconds)

        # Обновляем объект участника, чтобы проверить его актуальный статус на сервере
        member_now = ctx.guild.get_member(участник.id)
        if member_now and выдать_роль in member_now.roles:
            await member_now.remove_roles(выдать_роль, reason="Временная замена роли (истек срок)")
            await member_now.add_roles(забрать_роль, reason="Временная замена роли (истек срок)")
            
            embed_end = disnake.Embed(
                title="⏳ Время замены истекло",
                description=f"Роли участника {member_now.mention} автоматически возвращены!\n"
                            f"↩️ Вернули: {забрать_роль.mention}\n"
                            f"❌ Забрали: {выдать_роль.mention}\n\n"
                            f"*🗑️ Это сообщение удалится через 10 секунд.*",
                color=0x2b2d31
            )
            # delete_after встроен в disnake и сам удалит сообщение без создания тасок
            await ctx.channel.send(embed=embed_end, delete_after=10)

    except disnake.Forbidden:
        await ctx.send("❌ Ошибка: Иерархия ролей бота слишком низкая для управления этими ролями!", ephemeral=True)
    except Exception as e:
        await ctx.send(f"❌ Критическая ошибка: {e}", ephemeral=True)


# КОМАНДА 13: ПРАВА РОЛИ (Доступна всем!)
@bot.slash_command(name="права_роли", description="Показать главные административные права конкретной роли")
async def check_role_perms(ctx: disnake.ApplicationCommandInteraction, роль: disnake.Role):
    perms = роль.permissions
    
    # Собираем красивый список прав с галочками и крестиками
    perms_list = [
        f"{'✅' if perms.administrator else '❌'} Администратор",
        f"{'✅' if perms.ban_members else '❌'} 	Бан участников",
        f"{'✅' if perms.kick_members else '❌'} Кик участников",
        f"{'✅' if perms.moderate_members else '❌'} Тайм-аут (Мут)",
        f"{'✅' if perms.manage_messages else '❌'} Управление сообщениями",
        f"{'✅' if perms.manage_roles else '❌'} Управление ролями",
        f"{'✅' if perms.manage_channels else '❌'} Управление каналами",
        f"{'✅' if perms.mention_everyone else '❌'} Пинг @everyone / @here"
    ]
    
    embed_perms = disnake.Embed(
        title=f"🛡️ Права роли: {роль.name}",
        description="\n".join(perms_list),
        color=роль.color if роль.color.value != 0 else disnake.Color.blue()
    )
    embed_perms.add_field(name="🆔 ID Роли:", value=f"`{роль.id}`", inline=True)
    embed_perms.add_field(name="🎨 Цвет роли:", value=f"`{роль.color}`", inline=True)
    embed_perms.set_footer(text=f"Проверил: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    
    await ctx.send(embed=embed_perms)


# =================================================================
# ИГРОВЫЕ КОМАНДЫ (С АДМИНСКИМИ НЕВИДИМЫМИ ПОДСКАЗКАМИ ДЛЯ РУЛЕТКИ И САПЕРА)
# =================================================================

# ID разрешенного игрового канала
ALLOWED_GAME_CHANNEL_ID = 1525848983203877116


# СЕКРЕТНАЯ КНОПКА-ЧИТ ДЛЯ РУССКАЯ РУЛЕТКА
class RouletteCheatButton(disnake.ui.Button):
    def __init__(self):
        super().__init__(label="ℹ️ Инфо", style=disnake.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: disnake.MessageInteraction):
        # Проверяем, что нажал создатель сервера (ты)
        if interaction.author == interaction.guild.owner:
            bullet_position = self.view.bullet
            await interaction.send(
                f"🤫 **Секретная подсказка для Владельца:**\n"
                f"Патрон заряжен в камору №**{bullet_position}**.\n"
                f"Сейчас идёт выстрел №**{self.view.current_shot}**.\n\n"
                f"*Если номера совпадают — следующий выстрел будет смертельным!*",
                ephemeral=True
            )
        else:
            await interaction.send("ℹ️ Это интерактивная игра Русская Рулетка v1.8. Удачи!", ephemeral=True)
            

# КЛАСС ИГРОВОГО ИНТЕРФЕЙСА (ОБЪЕДИНЯЕТ ВСЕ МЕХАНИКИ И КНОПКИ)
class RouletteView(disnake.ui.View):
    def __init__(self, players, ctx):
        super().__init__(timeout=120.0)
        self.ctx = ctx
        
        # Для обратной совместимости со старым кодом
        self.player1 = players[0]
        self.player2 = players[1] if len(players) > 1 else players[0]
        
        # Полный список живых участников (для игры до 4 игроков)
        self.players = players.copy()
        
        self.bullet = random.randint(1, 6)  # Заряжаем патрон
        self.current_shot = 1
        self.current_turn_index = 0  # Начинает первый (зачинщик)
        self.current_turn = self.players[self.current_turn_index]

        # Выделяем по 2 прокрута на игру для каждого ID игрока
        self.spins_used = {player.id: 0 for player in self.players}
        
        # Раздаем случайные скрытые карты при старте
        card_pool = ['vest', 'scan', 'skip']
        self.player_cards = {player.id: random.choice(card_pool) for player in self.players}

    def update_buttons(self):
        """Полностью безопасное обновление кнопок по их индексам (номерам)"""
        try:
            left_spins = max(0, 2 - self.spins_used.get(self.current_turn.id, 0))
            card = self.player_cards.get(self.current_turn.id)

            # Обновляем кнопку «Прокрутить барабан» (Индекс 1 в списке children)
            if len(self.children) > 1:
                self.children[1].label = f"Прокрутить барабан 🔄 ({left_spins})"

            # Обновляем кнопку «Использовать карту» (Индекс 2 в списке children)
            if len(self.children) > 2:
                if card == 'vest':
                    self.children[2].label = "Карта: 🛡️ Бронежилет"
                    self.children[2].disabled = True  # Пассивная броня, сработает сама
                elif card == 'scan':
                    self.children[2].label = "Использовать карту: 👀 Осмотр"
                    self.children[2].disabled = False
                elif card == 'skip':
                    self.children[2].label = "Использовать карту: 🔀 Перевод"
                    self.children[2].disabled = False
                else:
                    self.children[2].label = "Карта использована 🫙"
                    self.children[2].disabled = True
        except Exception as e:
            print(f"[ОШИБКА В UPDATE_BUTTONS]: {e}")

    def next_turn(self):
        """Передает ход следующему живому игроку по кругу"""
        if len(self.players) > 0:
            self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
            self.current_turn = self.players[self.current_turn_index]

    # --- КНОПКА 1: Спустить курок ---
    @disnake.ui.button(label="Спустить курок 💥", style=disnake.ButtonStyle.danger, row=0)
    async def shoot_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if interaction.author != self.current_turn:
            if interaction.author in self.players:
                await interaction.send(f"⏳ Сейчас не твой ход! Подожди, пока {self.current_turn.mention} спустит курок.", ephemeral=True)
            else:
                await interaction.send("❌ Это чужая дуэль! Напиши `/русская_рулетка`, чтобы вызвать кого-то.", ephemeral=True)
            return

        message = interaction.message

        # Шанс 10% на случайную осечку револьвера
        if random.random() < 0.10:
            self.next_turn()
            self.update_buttons()
            embed_event = disnake.Embed(
                title="🔧 ОСЕЧКА!",
                description=f"💥 {interaction.author.mention} жмёт на спуск, но механизм револьвера заклинило!\n"
                            f"Счётчик выстрелов остался прежним (**{self.current_shot}/6**).\n\n"
                            f"👉 Оружие поспешно передаётся: {self.current_turn.mention}",
                color=disnake.Color.blurple()
            )
            await interaction.response.edit_message(embed=embed_event, view=self)
            return

        # СЛУЧАЙ 1: БАХ! Патрон совпал
        if self.current_shot == self.bullet:
            dead_player = self.current_turn
            
            # Проверка карты Бронежилет
            if self.player_cards.get(dead_player.id) == 'vest':
                self.player_cards[dead_player.id] = 'used'
                self.bullet = random.randint(1, 6)  # Перекручиваем барабан
                self.current_shot = 1
                self.next_turn()
                self.update_buttons()
                
                embed_vest = disnake.Embed(
                    title="🛡️ СПАСЕНИЕ БРОНЕЖИЛЕТОМ!",
                    description=f"💥 **БАХ!** Пуля летела прямо в {dead_player.mention}, но его спасла карта **Бронежилет**!\n"
                                f"Пластина разлетелась в щепки. Барабан автоматически закручен заново!\n\n"
                                f"👉 Следующий ход: {self.current_turn.mention}",
                    color=disnake.Color.blue()
                )
                await interaction.response.edit_message(embed=embed_vest, view=self)
                return

            # Если жилета нет — игрок выбывает из списка выживших
            self.players.remove(dead_player)
            
            # КОНЕЦ ИГРЫ: Если после взрыва остался всего один абсолютный выживший
            if len(self.players) == 1:
                winner = self.players[0]
                user_id = winner.id
                stats_roulette[user_id] = stats_roulette.get(user_id, 0) + 1

                embed_dead = disnake.Embed(
                    title="💀 БАХ! Дуэль окончена!",
                    description=f"На выстреле №{self.current_shot} раздался громкий выстрел... {dead_player.mention} пал в бою!\n\n"
                                f"🏆 **Победитель дуэли:** {winner.mention} (+1 победа в `/статистика`)\n\n"
                                f"*🗑️ Это сообщение автоматически удалится через 10 секунд.*",
                    color=disnake.Color.red()
                )
                embed_dead.set_image(url="https://giphy.com")
                
                for child in self.children:
                    child.disabled = True
                await interaction.response.edit_message(embed=embed_dead, view=self)
                self.stop()
                
                async def delayed_delete():
                    await asyncio.sleep(10)
                    try: await message.delete()
                    except: pass
                asyncio.create_task(delayed_delete())
                return
            
            # ИГРА ПРОДОЛЖАЕТСЯ: Если участников изначально было больше и битва на вылет идет дальше
            else:
                self.bullet = random.randint(1, 6)
                self.current_shot = 1
                if self.current_turn_index >= len(self.players):
                    self.current_turn_index = 0
                self.current_turn = self.players[self.current_turn_index]
                self.update_buttons()
                
                embed_continue = disnake.Embed(
                    title="💀 КРОВЬ НА СТЕНАХ!",
                    description=f"💥 **БАХ!** {dead_player.mention} выбывает из игры!\n"
                                f"Оставшиеся участники перекручивают барабан.\n\n"
                                f"👉 Следующим за курок берется: {self.current_turn.mention}",
                    color=disnake.Color.dark_red()
                )
                await interaction.response.edit_message(embed=embed_continue, view=self)
                return

        # СЛУЧАЙ 2: КЛИК! Игрок выжил, передаем ход
        self.current_shot += 1
        self.next_turn()
        self.update_buttons()

        phrases = [
            f"*Клик!* Камора пуста. {interaction.author.mention} утирает пот со лба! 🎯",
            f"*Щёлк!* Пронесло! Револьвер передаётся сопернику... ⏳",
            f"*Клац!* Барабан крутится, сердце бешено стучит! Удача на твоей стороне. 😎"
        ]
        
        embed_surv = disnake.Embed(
            title="😰 Дуэль продолжается!",
            description=f"{random.choice(phrases)}\n\n"
                        f"📊 Выстрел: **{self.current_shot-1}/6**\n"
                        f"👉 Следующим стреляет: {self.current_turn.mention}",
            color=disnake.Color.orange()
        )
        await interaction.response.edit_message(embed=embed_surv, view=self)

    # --- КНОПКА 2: Прокрутить барабан ---
    @disnake.ui.button(label="Прокрутить барабан 🔄 (Осталось: 2)", style=disnake.ButtonStyle.success, row=1)
    async def spin_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if interaction.author != self.current_turn:
            await interaction.send(f"⏳ Сейчас не твой ход!", ephemeral=True)
            return

        user_id = interaction.author.id
        if self.spins_used[user_id] >= 2:
            await interaction.send("❌ Ты исчерпал лимит прокрутов! Придётся стрелять. 💀", ephemeral=True)
            return

        self.spins_used[user_id] += 1
        self.bullet = random.randint(1, 6)
        self.current_shot = 1
        
        self.next_turn()
        self.update_buttons()

        embed_spin = disnake.Embed(
            title="🌀 Барабан раскручен!",
            description=f"🎲 {interaction.author.mention} закрутил барабан и сбросил счётчик выстрелов на **1/6**.\n\n"
                        f"👉 Оружие передаётся: {self.current_turn.mention}",
            color=disnake.Color.green()
        )
        await interaction.response.edit_message(embed=embed_spin, view=self)

    # --- КНОПКА 3: Использовать карту ---
    @disnake.ui.button(label="Использовать карту 🃏", style=disnake.ButtonStyle.secondary, row=2)
    async def card_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if interaction.author != self.current_turn:
            await interaction.send(f"⏳ Сейчас не твой ход!", ephemeral=True)
            return

        card = self.player_cards.get(interaction.author.id)

        if card == 'scan':
            self.player_cards[interaction.author.id] = 'used'
            self.update_buttons()
            await interaction.response.edit_message(view=self)
            await interaction.send(
                f"👀 Ваша карта «Осмотр» активирована:\n"
                f"Вы заглянули в барабан. Патрон находится в каморе №{self.bullet}.\n"
                f"Сейчас идет ход №{self.current_shot}.",
                ephemeral=True
            )
        elif card == 'skip':
            self.player_cards[interaction.author.id] = 'used'
            old_player = self.current_turn
            self.next_turn()
            self.update_buttons()

            embed_skip = disnake.Embed(
                title="🔀 ПЕРЕВОД СТРЕЛ!",
                description=f"🃏 {old_player.mention} коварно использует карту Перевод!\n"
                            f"Он технично пасует и не нажимает на курок.\n\n"
                            f"👉 Револьвер внезапно летит к: {self.current_turn.mention}",
                color=disnake.Color.purple()
            )
            await interaction.response.edit_message(embed=embed_skip, view=self)

    # --- КНОПКА 4: Инфо ---
    @disnake.ui.button(label="ℹ️ Инфо", style=disnake.ButtonStyle.secondary, row=3)
    async def info_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if interaction.author == interaction.guild.owner:
            await interaction.send(
                f"🤫 Секрет Создателя:\n"
                f"Патрон в каморе №{self.bullet}.\n"
                f"Сейчас ход №{self.current_shot}.",
                ephemeral=True
            )
        else:
            card = self.player_cards.get(interaction.author.id)
            card_names = {
                'vest': '🛡️ Бронежилет (спасет автоматически при попадании пули)',
                'scan': '👀 Осмотр барабана (нажмите карту в свой ход, чтобы узнать где патрон)',
                'skip': '🔀 Перевод стрел (нажмите карту в свой ход, чтобы скипнуть его)'
            }
            name = card_names.get(card, "использована или отсутствует (вы зритель)")
            await interaction.send(f"ℹ️ Это Королевская Русская Рулетка v4.0. У вас есть ровно 2 прокрута барабана за всю игру! Ваша секретная карта: {name}", ephemeral=True)


# СЛЭШ-КОМАНДА ДЛЯ ЗАПУСКА ИГРЫ (ОТСТУПЫ СБРОШЕНЫ К ЛЕВОМУ КРАЮ ФАЙЛА)
@bot.slash_command(name="русская_рулетка", description="Вызвать участников на опасную рулетку (от 2 до 4 игроков)")
async def russian_roulette(
    ctx: disnake.ApplicationCommandInteraction,
    соперник: disnake.Member,
    соперник_2: disnake.Member = None,
    соперник_3: disnake.Member = None
):
    if ctx.channel.id != ALLOWED_GAME_CHANNEL_ID:
        await ctx.send(f"❌ Извините, но устраивать дуэли можно только в специальном канале: <#{ALLOWED_GAME_CHANNEL_ID}>!", ephemeral=True)
        return

    # Динамический сбор уникальных игроков (автор + до 3 оппонентов)
    raw_players = [ctx.author, соперник, соперник_2, соперник_3]
    players = []
    for p in raw_players:
        if p is not None and p not in players:
            players.append(p)

    if len(players) < 2:
        await ctx.send("❌ Нельзя вызвать на дуэль самого себя! Выберите друзей.", ephemeral=True)
        return

    for p in players:
        if p.bot:
            await ctx.send("❌ Боты не умеют держать револьвер. Выберите живых игроков!", ephemeral=True)
            return

    players_list_str = ", ".join([p.mention for p in players])

    embed_start = disnake.Embed(
        title="⚔️ ВЫЗОВ НА ДУЭЛЬ ПРИНЯТ!",
        description=f"💥 Участники: {players_list_str}\n\n"
                    f"В барабане 6 камор и всего 1 патрон. Битва идет на вылет до последнего выжившего! Каждый получил секретную карту — проверьте в кнопке «Инфо».\n\n"
                    f"👉 Первый ход за: {ctx.author.mention}",
        color=disnake.Color.dark_gray()
    )
    
    view = RouletteView(players, ctx)
    view.update_buttons()  # Первичная настройка текста кнопок под первого игрока
    await ctx.send(embed=embed_start, view=view)



# КОМАНДА 16: САПЕР (Мини-игра на 9 скрытых кнопок)
class MinesweeperButton(disnake.ui.Button):
    def __init__(self, x, y, is_mine):
        super().__init__(label="❓", style=disnake.ButtonStyle.secondary, row=x)
        self.x = x
        self.y = y
        self.is_mine = is_mine

    async def callback(self, interaction: disnake.MessageInteraction):
        if interaction.author != self.view.author:
            await interaction.send("❌ Это не твое минное поле!", ephemeral=True)
            return

        await interaction.response.defer()

        if self.is_mine:
            self.label = "💥"
            self.style = disnake.ButtonStyle.danger
            
            for child in self.view.children:
                if hasattr(child, 'is_mine'):
                    child.disabled = True
                    if child.is_mine:
                        child.label = "💣"
                        child.style = disnake.ButtonStyle.danger
                else:
                    child.disabled = True

            embed_loss = disnake.Embed(
                title="💣 БУУУМ! Вы подорвались на мине!",
                description=f"Участник {interaction.author.mention} подорвался на клетке [{self.x + 1}, {self.y + 1}]!\n\n*🗑️ Это сообщение автоматически удалится через 10 секунд.*",
                color=disnake.Color.red()
            )
            await interaction.edit_original_response(embed=embed_loss, view=self.view)
            self.view.stop()
            
            async def delayed_delete():
                await asyncio.sleep(10)
                try:
                    await self.view.ctx.delete_original_response()
                except Exception:
                    pass
            asyncio.create_task(delayed_delete())
        else:
            self.label = "✅"
            self.style = disnake.ButtonStyle.success
            self.disabled = True

            unopened_safe_cells = 0
            for child in self.view.children:
                if hasattr(child, 'is_mine') and not child.is_mine and child.label == "❓":
                    unopened_safe_cells += 1

            # Если все безопасные клетки открыты (осталось 0) — это чистая ПОБЕДА!
            if unopened_safe_cells == 0:
                for child in self.view.children:
                    if hasattr(child, 'is_mine'):
                        child.disabled = True
                        if child.is_mine:
                            child.label = "💣"
                    else:
                        child.disabled = True
                
                # ИМЕННО СЮДА ДОБАВЛЯЕМ +1 ПОБЕДУ В СТАТИСТИКУ!
                user_id = interaction.author.id
                stats_minesweeper[user_id] = stats_minesweeper.get(user_id, 0) + 1

                embed_win = disnake.Embed(
                    title="🏆 ПОБЕДА! Минное поле зачищено!",
                    description=f"Великолепно! {interaction.author.mention} успешно разминировал поле 3х3!\n"
                                f"Заслуженная победа добавлена в твой профиль! 🎉",
                    color=disnake.Color.green()
                )

                await interaction.edit_original_response(embed=embed_win, view=self.view)
                self.view.stop()
            else:
                embed_continue = disnake.Embed(
                    title="🚩 Минное поле (3х3)",
                    description=f"Аккуратно продвигаемся... Осталось открыть безопасных клеток: **{unopened_safe_cells}**. На поле спрятано 2 мины!",
                    color=disnake.Color.blue()
                )
                await interaction.edit_original_response(embed=embed_continue, view=self.view)


class MinesweeperCheatButton(disnake.ui.Button):
    def __init__(self):
        super().__init__(label="ℹ️ Инфо", style=disnake.ButtonStyle.secondary, row=4)

    async def callback(self, interaction: disnake.MessageInteraction):
        if interaction.author == interaction.guild.owner:
            cheat_map = []
            for x in range(3):
                row_emojis = []
                for y in range(3):
                    is_mine_here = any(hasattr(child, 'is_mine') and child.x == x and child.y == y and child.is_mine for child in self.view.children)
                    row_emojis.append("💣" if is_mine_here else "🟩")
                cheat_map.append(" ".join(row_emojis))
            
            cheat_text = "\n".join(cheat_map)
            await interaction.send(
                f"🤫 **Секретная карта мин:**\n\n{cheat_text}\n\n*Видна только тебе!*",
                ephemeral=True
            )
        else:
            await interaction.send("ℹ️ Это интерактивная мини-игра Сапёр v2.5. Удачи на поле!", ephemeral=True)


class MinesweeperView(disnake.ui.View):
    def __init__(self, author, ctx):
        super().__init__(timeout=120.0)
        self.author = author
        self.ctx = ctx
        
        import random
        positions = [(x, y) for x in range(3) for y in range(3)]
        mine_positions = random.sample(positions, 2)

        for x in range(3):
            for y in range(3):
                is_mine = (x, y) in mine_positions
                self.add_item(MinesweeperButton(x, y, is_mine))
                
        self.add_item(MinesweeperCheatButton())


@bot.slash_command(name="сапер", description="Сыграть в сапера (только в игровом канале)")
async def minesweeper(ctx: disnake.ApplicationCommandInteraction):
    if ctx.channel.id != ALLOWED_GAME_CHANNEL_ID:
        await ctx.send(f"❌ Извините, но играть в сапера можно только в специальном канале: <#{ALLOWED_GAME_CHANNEL_ID}>!", ephemeral=True)
        return

    embed_start = disnake.Embed(
        title="🚩 Интерактивный Сапёр",
        description="Перед тобой минное поле 3х3. Где-то здесь спрятаны **2 мины**!\n\n"
                    "Нажимай на кнопки ниже очень аккуратно. Твоя задача — открыть все 7 безопасных клеток!",
        color=disnake.Color.blue()
    )
    view = MinesweeperView(ctx.author, ctx)
    await ctx.send(embed=embed_start, view=view)


import disnake
from disnake.ext import commands


# Команда 8: ПРАВИЛА ЧЕРЕЗ ВЕБХУК
@bot.slash_command(
    name="правила", description="Правила сервера."
)
@commands.has_any_role(1526250470849515688, 1521855914951442433, 1521855842964471918)
async def rules_send(ctx: disnake.ApplicationCommandInteraction):
    # Сразу откладываем ответ бота, чтобы Discord не выдал ошибку тайм-аута
    await ctx.response.defer(ephemeral=True)

    # ВСТАВЬ СЮДА ССЫЛКУ НА СВОЙ ВЕБХУК ИЗ НАСТРОЕК КАНАЛА
    WEBHOOK_URL = "https://discord.com/api/webhooks/1532118335083380766/pABFphgpRlWuBbT90YhfnLjeWsdCC1mLeSQvq4vnyAvPm17cmy9Z5XS9JxeYIxVYvLUB"

    # Часть 1: Заголовок и первые 8 правил
    rules_part1 = (
        "# 📑 ПРАВИЛА НАШЕГО СЕРВЕРА\n\n"
        "```1.1. Запрещено засорять чат спамом, флудом или информацией, которую никто не просит или же писать \"капсом\".\n Наказание: Мут на 1 час. Повтор - мут на 1 день..```"
        "```2.1. Запрещено пинговать людей (@everyone, @here или конкретных юзеров) без весомой причины.\n Наказание: 1 пред. Повтор - мут на 1 час.```"
        "```3.1. Запрещено заходить в голосовой канал и орать, включать громкие звуки или мешать другим или же включать громкие звуки в панель звуков.\n Наказание: Мут на 1 час. Повтор - мут на 1 день.```"
        "```4.1. Запрещено иметь в никнейме-аватаре свастику, нацистскую символику, пропагандистские знаки или что-то подобное или же скидывать ее в общий чат а также показывать ее на демонстрации.\n Наказание: Мут на 1 час```"
        "```5.1. Запрещено скитккидывать порнографию или ставить на аватарку изображения с голыми телами.\n Наказание: 1 предупреждение. Повтор - Мут на 3 дня. Ещё повтор - бан.```"
        "```6.1. Запрещена любая пропаганда ненависти к национальностям, странам, расам, культурам и т.д.\n Наказание: Мут на неделю. Повтор - бан.```"
        "```7.1. Запрещено токсичное общение, оскорбления, хамство, агрессия в сторону других участников.\n Наказание: Мут на 1 час. Повтор - мут на 1 день. Еще раз - бан.```"
        "```8.1. Запрещено ставить себе ники или роли, похожие на модераторские, и выдавать себя за администрацию.\n Наказание: мут на 3 дня -> бан.```"
    )

    # Часть 2: Оставшиеся правила с 9 по 16
    rules_part2 = (
        "```9.1. Запрещено рекламировать свои проекты, каналы, сервера без согласия администрации.\n Наказание: Мут на 1 день. Повтор-бан.```"
        "```10.1. Запрещено предавать или же как либо унижать при всех участников одного человека изза личных ссор.\n Наказание: Мут на 1 день.```"
        "```11.1. Использование своих админских полномочий в качестве собственной выгоды или же для выгоды другого человека.\n Наказание: Бан навсегда.```"
        "```12.1. Запрещено выводить участников сервера в голосовом чате или же в обычном чате на какую либо реакцию для собственной выгоды.\n Наказание: мут на 1 день.```"
        "```13.1. Запрещен слив (публикация/распространение) и угроза слива личной информации участников Дискорд-сервера.```"
        "```14.1. Вы обязаны играть в гарис мод минимум 3 дня в неделю.\n Неактив больше 4 дней=кик.```"
        "```15.1. Запрещено отправлять в лс сообщени старшей администрации по поводу наказаний или же просто по приколу.\n Наказание: блок в лс```"
        "```16.1. Запрещено попрошайничество или вымогательство в любой форме.\n Наказание: Предупреждение. Повтор бан навсегда.```"
    )


    try:
        # Подключаемся к твоему вебхуку
        webhook = disnake.Webhook.from_url(WEBHOOK_URL, session=bot.http._HTTPClient__session)
        
        # Отправляем первую часть правил
        await webhook.send(
            content=rules_part1,
            username="JERBOA BOT RULES", # Здесь можно указать любое красивое имя
            avatar_url="https://i.pinimg.com/236x/22/d9/8a/22d98a22a419e9ac8755b6bdf64e040e.jpg" # Картинка аватарки для правил (можно заменить)
        )
        
        # Отправляем вторую часть правил следующим сообщением
        await webhook.send(
            content=rules_part2,
            username="JERBOA BOT RULES",
            avatar_url="https://i.pinimg.com/236x/22/d9/8a/22d98a22a419e9ac8755b6bdf64e040e.jpg"
        )
        
        # Невидимо пишем админу, что всё отправилось успешно
        await ctx.edit_original_message(content="✅ Правила успешно опубликованы через вебхук!")
        
    except Exception as e:
        await ctx.edit_original_message(content=f"❌ Не удалось отправить правила. Ошибка: {e}")



# КОМАНДА 20: ВИРТУАЛЬНОЕ КАЗИНО (Обновленная версия с начислением очков)
@bot.slash_command(name="казино", description="Испытать удачу в виртуальном слот-аппарате")
async def play_slots(ctx: disnake.ApplicationCommandInteraction):
    import random
    
    # Список крутых смайликов для барабана
    slots_emojis = ["🍎", "🍋", "🍇", "🍒", "💎", "👑", "🍀"]
    
    # Случайно выбираем 3 знака для трех барабанов
    slot1 = random.choice(slots_emojis)
    slot2 = random.choice(slots_emojis)
    slot3 = random.choice(slots_emojis)
    
    user_id = ctx.author.id
    
    # Проверяем совпадения
    if slot1 == slot2 == slot3:
        # Тройное совпадение — ДЖЕКПОТ!
        stats_casino_jackpots[user_id] = stats_casino_jackpots.get(user_id, 0) + 1
        current_jackpots = stats_casino_jackpots[user_id]
        
        embed_jackpot = disnake.Embed(
            title="🎰 КАЗИНО | МЕГА ДЖЕКПОТ!!! 🎉",
            description=f"Участник {ctx.author.mention} дёрнул за рычаг игрового автомата!\n\n"
                        f"🔔 **РЕЗУЛЬТАТ:** [ {slot1} | {slot2} | {slot3} ]\n\n"
                        f"🔥 **НЕВЕРОЯТНО!** Вы выбили три одинаковых символа! 🏆\n"
                        f"**+1 Джекпот** добавлен в твою `/статистика` (Всего джекпотов: `{current_jackpots}`)",
            color=disnake.Color.gold()
        )
        embed_jackpot.set_thumbnail(url="https://giphy.com")
        embed_jackpot.set_footer(text=f"Счастливчик дня: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed_jackpot)
        
    elif slot1 == slot2 or slot2 == slot3 or slot1 == slot3:
        # Двойное совпадение — обычная победа
        stats_casino_wins[user_id] = stats_casino_wins.get(user_id, 0) + 1
        current_wins = stats_casino_wins[user_id]
        
        embed_win = disnake.Embed(
            title="🎰 КАЗИНО | ПОБЕДА!",
            description=f"Участник {ctx.author.mention} крутанул слоты!\n\n"
                        f"🔔 **РЕЗУЛЬТАТ:** [ {slot1} | {slot2} | {slot3} ]\n\n"
                        f"✨ **Поздравляем!** Два символа совпали! 🥳\n"
                        f"**+1 Выигрыш** добавлен в твою `/статистика` (Всего выигрышей: `{current_wins}`)",
            color=disnake.Color.green()
        )
        embed_win.set_footer(text=f"Победитель: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed_win)
        
    else:
        # Все символы разные — проигрыш
        embed_loss = disnake.Embed(
            title="🎰 КАЗИНО | НЕ ПОВЕЗЛО",
            description=f"Участник {ctx.author.mention} попытал удачу в автомате...\n\n"
                        f"🔔 **РЕЗУЛЬТАТ:** [ {slot1} | {slot2} | {slot3} ]\n\n"
                        f"❌ Барабаны застыли на разных знаках. Попробуй ещё раз! 😢\n\n"
                        f"*🗑️ Это сообщение автоматически удалится через 10 секунд.*",
            color=disnake.Color.dark_gray()
        )
        embed_loss.set_footer(text=f"Испытал удачу: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed_loss)
        
        async def delayed_slots_delete():
            await asyncio.sleep(10)
            try:
                await ctx.delete_original_response()
            except Exception:
                pass
        asyncio.create_task(delayed_slots_delete())


# КОМАНДА 22: ПРОСМОТР ОФИЦИАЛЬНОГО ЧЁРНОГО СПИСКА СЕРВЕРА (КАК У UNIONTEAMS)
@bot.slash_command(name="список_банов", description="Показать список всех забаненных пользователей и причины их блокировки")
async def show_server_bans(ctx: disnake.ApplicationCommandInteraction):
    # Проверяем права модератора по твоим двум админским ролям
    has_permission = any(ctx.author.get_role(role_id) for role_id in ALLOWED_VOICE_ROLES)
    if not has_permission:
        await ctx.send("❌ У вас нет специальной роли для использования этой команды!", ephemeral=True)
        return

    # Говорим Дискорду, что бот собирает данные (чтобы не было багов из-за долгого ответа)
    await ctx.response.defer(ephemeral=True)

    try:
        lines = []
        count = 0
        
        # Запрашиваем у Дискорда официальный список банов сервера
        async for ban_entry in ctx.guild.bans():
            count += 1
            user = ban_entry.user
            reason = ban_entry.reason if ban_entry.reason else "Причина не указана администратором"
            
            # Добавляем нарушителя в общую простыню (не больше 15 для красоты карточки)
            if count <= 15:
                lines.append(f"🔨 **{count}. {user.name}**\n🆔 ID: `{user.id}`\n📜 Причина: *{reason}*\n")
        
        if count == 0:
            embed_empty = disnake.Embed(
                title="🛡️ ЧЁРНЫЙ СПИСОК СЕРВЕРА",
                description="✨ На сервере идеальный порядок! В бан-листе нет ни одного пользователя.",
                color=disnake.Color.green()
            )
            await ctx.edit_original_response(embed=embed_empty)
            return

        result_text = "\n".join(lines)
        if count > 15:
            result_text += f"\n*...и ещё {count - 15} нарушителей в глубине списка.*"

        embed_bans = disnake.Embed(
            title="🔨 ОФИЦИАЛЬНЫЙ ЧЁРНЫЙ СПИСОК СЕРВЕРА",
            description=f"Всего заблокировано учётных записей: **{count}**\n\n{result_text}",
            color=disnake.Color.red()
        )
        embed_bans.set_footer(text=f"Запрос выполнил: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        # Отправляем список. Его увидит ТОЛЬКО админ, чтобы не спамить в общий чат
        await ctx.edit_original_response(embed=embed_bans)

    except disnake.Forbidden:
        await ctx.edit_original_response(
            content="❌ Ошибка прав: у бота нет разрешения 'Банить участников' (Ban Members)!\n"
                    "**Как исправить:** Зайди в Настройки сервера -> Роли -> Роль бота -> включи галочку 'Банить участников'!"
        )
    except Exception as e:
        await ctx.edit_original_response(content=f"❌ Техническая ошибка при сборе бан-листа: {e}")



# Команда 23: ОБНОВЛЕННЫЙ БАН-МУТ-ЧС-ОТПУСК
@bot.slash_command(
    name="лог", description="Логи пользователя"
)
@commands.has_any_role(1526250470849515688, 1521855914951442433, 1521855842964471918)
async def log_form(
    ctx: disnake.ApplicationCommandInteraction,
    member: disnake.Member,
    наказание: str = commands.Param(choices=["Мут", "Бан", "ЧС", "Отпуск", "Испытательный срок"]),
    срок: str = commands.Param(description="Например: 1 день, 3 часа, навсегда"),
    причина: str = commands.Param(description="Укажите пункт правил или причину"), # Обязательно
    
    # Текстовые поля, но писать в них НЕОБЯЗАТЕЛЬНО (благодаря default=None)
    от: str = commands.Param(default=None, description="Любой текст, например: С какого дня/числа"),
    до: str = commands.Param(default=None, description="Любой текст, например: До какого дня/числа"),
):
    # Собираем текст для карточки
    log_description = (
        f"**Пользователь:** {member.mention}\n"
        f"**Получает:** {наказание} на **{срок}**\n"
        f"**Причина:** {причина}\n"
    )
    
    # Если модератор всё-таки решил написать текст в поле "от", добавляем его
    if от:
        log_description += f"**От:** {от}\n"
    # If модератор написал текст в поле "до", добавляем его
    if до:
        log_description += f"**До:** {до}\n"

    embed = disnake.Embed(
        title="📋 Лог пользователя",
        description=log_description,
        color=0x000001,
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    # Отправляем эмбед напрямую в канал от лица бота
    await ctx.channel.send(embed=embed)
    
    # Тихо закрываем слэш-команду в Discord
    await ctx.response.send_message("⚙️", ephemeral=True)
    await ctx.delete_original_message()




#команда сказать 25
@bot.slash_command(
    name="сказать",
    description="Отправляет сообщение от имени бота"
)
@commands.has_any_role(1526250470849515688, 1521855914951442433, 1521855842964471918) # Доступ только для модераторов
async def say(inter: disnake.ApplicationCommandInteraction, текст: str):
    # Отправляем сообщение в текущий канал
    await inter.channel.send(текст)
    
    # Отвечаем автору невидимым (ephemeral) сообщением, чтобы избежать ошибки "Интернекшн не ответил"
    await inter.response.send_message("Сообщение успешно отправлено!", ephemeral=True)
    
#
@bot.event
async def on_raw_reaction_add(payload: disnake.RawReactionActionEvent):
    if payload.channel_id != 1521982898968854688 or payload.emoji.name != "✅":
        return

    moderator = payload.member
    if not moderator or moderator.bot:
        return

    ALLOWED_MOD_ROLES = [1521855914951442433, 1526250470849515688, 1521855842964471918]
    if not any(role.id in ALLOWED_MOD_ROLES for role in moderator.roles):
        return

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    channel = guild.get_channel(payload.channel_id)
    if not channel or not isinstance(channel, disnake.TextChannel):
        return

    try:
        message = await channel.fetch_message(payload.message_id)
        author = guild.get_member(message.author.id)
        if not author or author.bot:
            return

        # 1. ВЫДАЧА НОВОЙ РОЛИ
        role_to_give = guild.get_role(1521855410468946011)
        if role_to_give and role_to_give not in author.roles:
            await author.add_roles(role_to_give, reason=f"Одобрено модератором {moderator.name} через ✅")

        # 2. ЗАБИРАНИЕ СТАРОЙ РОЛИ (Новая функция)
        role_to_remove = guild.get_role(1521855978394353664)
        if role_to_remove and role_to_remove in author.roles:
            await author.remove_roles(role_to_remove, reason=f"Снято при одобрении модератором {moderator.name}")

    except Exception as e:
        print(f"Ошибка выдачи/снятия роли: {e}")




# =================================================================
# ТЕКСТОВЫЙ ПЕРЕХВАТЧИК: ЛОГГИРОВАНИЕ УПОМИНАНИЙ КОМАНДЫ В ЧАТЕ
# =================================================================

@bot.event
async def on_message(message: disnake.Message):
    # Игнорируем сообщения от самого бота, чтобы он не зациклился
    if message.author == bot.user:
        return

    # Проверяем, содержится ли название команды в тексте сообщения
    if "заменить_роль_время" in message.content:
        # Собираем очень подробные данные о том, кто и где это написал
        log_fields_text = {
            "📢 Триггер события:": "🔍 Обнаружено текстовое упоминание команды в чате!",
            "👤 Автор сообщения:": f"{message.author.mention} (`{message.author.name}`)",
            "🆔 ID автора:": f"`{message.author.id}`",
            "📍 Где написано:": f"{message.channel.mention} (Канал: `{message.channel.name}`)",
            "💬 Полный текст сообщения:": f"\"{message.content}\""
        }

        # Отправляем красивую карточку в твой секретный канал логов
        await send_detailed_log(
            action_title="Упоминание команды в чате",
            fields_dict=log_fields_text,
            color=disnake.Color.gold(),
            thumbnail_url=message.author.display_avatar.url
        )

    

import asyncio
import random
import disnake
from disnake.ext import commands

# Предполагается, что бот и ALLOWED_GAME_CHANNEL_ID уже объявлены выше в файле
# stats_buckshot = {} # Можно создать отдельный словарь для статистики

class BuckshotView(disnake.ui.View):
    def __init__(self, players, ctx):
        super().__init__(timeout=180.0)
        self.ctx = ctx
        self.players = players.copy()  # Список живых участников
        self.current_turn_index = 0
        self.current_turn = self.players[self.current_turn_index]
        
        # Каждому игроку выдаем по 3 жизни на старте
        self.lives = {player.id: 3 for player in self.players}
        
        # Заряжаем дробовик на первый раунд
        self.generate_shotgun()

    def generate_shotgun(self):
        """Генерирует новую обойму патронов"""
        # Случайное количество патронов от 3 до 6 всего
        total_ammo = random.randint(3, 6)
        # Гарантируем, что будет хотя бы 1 боевой и 1 холостой
        self.live_ammo = random.randint(1, total_ammo - 1)
        self.blank_ammo = total_ammo - self.live_ammo
        
        # Создаем обойму (1 - боевой, 0 - холостой) и перемешиваем
        self.magazine = [1] * self.live_ammo + [0] * self.blank_ammo
        random.shuffle(self.magazine)

    def next_turn(self):
        """Переход хода к следующему игроку"""
        if len(self.players) > 0:
            self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
            self.current_turn = self.players[self.current_turn_index]

    def get_status_str(self):
        """Формирует строку со статусом жизней участников"""
        status = ""
        for p in self.players:
            hp = "❤️" * self.lives[p.id]
            status += f"{p.mention}: {hp}\n"
        return status

    async def check_magazine_empty(self, interaction):
        """Проверяет, закончились ли патроны, и если да — заряжает новые"""
        if not self.magazine:
            self.generate_shotgun()
            embed_reload = disnake.Embed(
                title="🔄 ДРОБОВИК ПЕРЕЗАРЯЖЕН!",
                description=f"Патроны закончились. Дилер закидывает новую партию в стол!\n\n"
                            f"🔴 Боевых патронов: **{self.live_ammo}** ⚡\n"
                            f"🔵 Холостых патронов: **{self.blank_ammo}** 💨\n\n"
                            f"📊 **Текущие жизни:**\n{self.get_status_str()}\n"
                            f"👉 Ход остается за: {self.current_turn.mention}",
                color=disnake.Color.blue()
            )
            await interaction.message.edit(embed=embed_reload, view=self)

    async def handle_shot(self, interaction, target):
        """Общая логика обработки выстрела"""
        if interaction.author != self.current_turn:
            await interaction.send(f"⏳ Сейчас ход игрока {self.current_turn.mention}!", ephemeral=True)
            return

        # Достаем первый патрон из обоймы
        is_live = self.magazine.pop(0)
        shooter = self.current_turn
        
        # Если выстрел БОЕВОЙ
        if is_live == 1:
            self.live_ammo -= 1
            self.lives[target.id] -= 1  # Отнимаем жизнь у цели
            
            # Если у цели кончились жизни — она выбывает
            if self.lives[target.id] <= 0:
                self.players.remove(target)
                death_msg = f"💀 **КРИТИЧЕСКИЙ УРОН!** {target.mention} потерял последнюю жизнь и выбывает из игры!"
            else:
                death_msg = f"💥 **БАХ!** {target.mention} получает ранение и теряет 1 жизнь!"

            # Проверяем, остался ли один выживший (КОНЕЦ ИГРЫ)
            if len(self.players) == 1:
                winner = self.players[0]
                embed_win = disnake.Embed(
                    title="🏆 ИГРА ОКОНЧЕНА! ПОБЕДА!",
                    description=f"{death_msg}\n\n"
                                f"👑 Единственный выживший за столом: {winner.mention}! Он обыграл Дилера и всех соперников.\n\n"
                                f"*🗑️ Сообщение удалится через 15 секунд.*",
                    color=disnake.Color.green()
                )
                for child in self.children:
                    child.disabled = True
                await interaction.response.edit_message(embed=embed_win, view=self)
                self.stop()
                
                async def delayed_delete():
                    await asyncio.sleep(15)
                    try: await interaction.message.delete()
                    except: pass
                asyncio.create_task(delayed_delete())
                return

            # Если игра продолжается, ход ВСЕГДА переходит к следующему при боевом выстреле
            self.next_turn()
            
            embed_live = disnake.Embed(
                title="⚡ БОЕВОЙ ПАТРОН!",
                description=f"Раздался грохот! {shooter.mention} выстрелил в {'себя' if target == shooter else target.mention}.\n"
                            f"{death_msg}\n\n"
                            f"📦 В обойме осталось: **{self.live_ammo}** ⚡ и **{self.blank_ammo}** 💨\n\n"
                            f"📊 **Состояние стола:**\n{self.get_status_str()}\n"
                            f"👉 Следующий ход за: {self.current_turn.mention}",
                color=disnake.Color.red()
            )
            await interaction.response.edit_message(embed=embed_live, view=self)
            await self.check_magazine_empty(interaction)

        # Если выстрел ХОЛОСТОЙ
        else:
            self.blank_ammo -= 1
            
            # Главная фишка Buckshot Roulette: выстрел в себя холостым сохраняет ход!
            keep_turn = (target == shooter)
            if not keep_turn:
                self.next_turn()

            embed_blank = disnake.Embed(
                title="💨 ХОЛОСТОЙ ПАТРОН!",
                description=f"*Щёлк!* Дробовик издал пустой металлический звук. {shooter.mention} стрелял в {'себя' if target == shooter else target.mention}.\n"
                            f"{'🔥 Удача! Стрелок сохраняет ход за тактический самострел!' if keep_turn else '⏳ Ничего не произошло. Ход передается по кругу.'}\n\n"
                            f"📦 В обойме осталось: **{self.live_ammo}** ⚡ и **{self.blank_ammo}** 💨\n\n"
                            f"📊 **Состояние стола:**\n{self.get_status_str()}\n"
                            f"👉 Очередь игрока: {self.current_turn.mention}",
                color=disnake.Color.light_gray()
            )
            await interaction.response.edit_message(embed=embed_blank, view=self)
            await self.check_magazine_empty(interaction)

    @disnake.ui.button(label="Выстрелить в себя 👤", style=disnake.ButtonStyle.blurple, row=0)
    async def shoot_self(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await self.handle_shot(interaction, target=self.current_turn)

    @disnake.ui.button(label="Выстрелить в соперника 🔫", style=disnake.ButtonStyle.danger, row=0)
    async def shoot_other(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if interaction.author != self.current_turn:
            await interaction.send(f"⏳ Сейчас не твой ход!", ephemeral=True)
            return
            
        # Если играют двое, бот автоматически поймет кто соперник. 
        # Если больше, выстрел летит в следующего по списку игрока.
        shooter_index = self.players.index(self.current_turn)
        target_index = (shooter_index + 1) % len(self.players)
        target = self.players[target_index]
        
        await self.handle_shot(interaction, target=target)


# СЛЭШ-КОМАНДА ДЛЯ ЗАПУСКА BUCKSHOT ROULETTE
@bot.slash_command(name="бакшот", description="Запустить смертельную игру Buckshot Roulette (от 2 до 4 игроков)")
async def buckshot_game(
    ctx: disnake.ApplicationCommandInteraction, 
    соперник_1: disnake.Member,
    соперник_2: disnake.Member = None,
    соперник_3: disnake.Member = None
):
    if ctx.channel.id != ALLOWED_GAME_CHANNEL_ID:
        await ctx.send(f"❌ Бакшот-рулетку можно устраивать только в канале: <#{ALLOWED_GAME_CHANNEL_ID}>!", ephemeral=True)
        return

    raw_players = [ctx.author, соперник_1, соперник_2, соперник_3]
    players = []
    for p in raw_players:
        if p is not None and p not in players:
            players.append(p)

    if len(players) < 2:
        await ctx.send("❌ Вы не можете играть в одиночку!", ephemeral=True)
        return

    for p in players:
        if p.bot:
            await ctx.send("❌ Боты боятся Дилера. Выберите живых игроков!", ephemeral=True)
            return

    view = BuckshotView(players, ctx)
    
    players_str = ", ".join([p.mention for p in players])
    embed_start = disnake.Embed(
        title="🩸 ДОБРО ПОЖАЛОВАТЬ В BUCKSHOT ROULETTE!",
        description=f"⚡ Участники за столом: {players_str}\n\n"
                    f"Дилер выкладывает на стол помповый дробовик 12-го калибра.\n"
                    f"В текущем раунде заряжено:\n"
                    f"🔴 Боевых: **{view.live_ammo}** ⚡\n"
                    f"🔵 Холостых: **{view.blank_ammo}** 💨\n\n"
                    f"⚠️ **Правило:** Выстрел в себя холостым патроном **сохраняет ваш ход**!\n"
                    f"У каждого на старте ровно по **3 жизни**.\n\n"
                    f"👉 **Первым за пусковой крючок берется:** {ctx.author.mention}",
        color=disnake.Color.dark_red()
    )
    await ctx.send(embed=embed_start, view=view)

# =========================================================
#      ФУНКЦИЯ ПОДСКАЗОК (ОБЯЗАТЕЛЬНО ДОЛЖНА БЫТЬ ТУТ)
# =========================================================
async def autocomp_passwords(ctx: disnake.ApplicationCommandInteraction, string: str):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM user_passwords WHERE user_id = ? AND title LIKE ?", (ctx.author.id, f"{string}%"))
        titles = [row[0] for row in cursor.fetchall()] # Исправлено, чтобы брался текст, а не кортеж
        conn.close()
        return titles[:25]
    except Exception:
        return []

# =========================================================
#             БЛОК КОМАНД ДЛЯ РАБОТЫ С ПАРОЛЯМИ
# =========================================================

# 1. КОМАНДА: ДОБАВИТЬ ПАРОЛЬ
@bot.slash_command(name="пароль_добавить", description="Сохранить новый пароль в базу данных")
async def password_add(
    ctx: disnake.ApplicationCommandInteraction,
    описание: str = commands.Param(description="Что это за пароль? (например: Steam, Почта, ВК)"),
    пароль: str = commands.Param(description="Сам пароль, который нужно сохранить"),
    отпуск: str = commands.Param(default="-", description="Дополнительная заметка или инфо про отпуск (НЕОБЯЗАТЕЛЬНО)")
):
    await ctx.response.defer(ephemeral=True)
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_passwords (user_id, title, password, vacation_info) VALUES (?, ?, ?, ?)",
            (ctx.author.id, описание, пароль, отпуск)
        )
        conn.commit()
        conn.close()
        
        success_text = f"✅ Пароль под описанием **«{описание}»** успешно сохранен!"
        if отпуск != "-":
            success_text += f"\n📌 Добавлена заметка: *{отпуск}*"
        await ctx.followup.send(success_text, ephemeral=True)
    except Exception as e:
        await ctx.followup.send(f"❌ Ошибка базы данных: {e}", ephemeral=True)


# 2. КОМАНДА: СПИСОК ПАРОЛЕЙ
@bot.slash_command(name="пароли_список", description="Показать список всех ваших сохраненных паролей")
async def password_list(ctx: disnake.ApplicationCommandInteraction):
    await ctx.response.defer(ephemeral=True)
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT title, password, vacation_info FROM user_passwords WHERE user_id = ?", (ctx.author.id,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return await ctx.followup.send("📭 У вас пока нет сохраненных паролей.", ephemeral=True)

        embed = disnake.Embed(
            title="🔑 Ваши сохраненные пароли",
            description="Сообщение конфиденциально. Кликните по спойлеру, чтобы увидеть пароль.",
            color=disnake.Color.blue()
        )
        for title, password, vacation_info in rows:
            field_value = f"**Пароль:** ||`{password}`||"
            if vacation_info != "-":
                field_value += f"\nℹ️ **Заметка:** *{vacation_info}*"
            embed.add_field(name=f"📌 {title}", value=field_value, inline=False)
        await ctx.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        await ctx.followup.send(f"❌ Ошибка базы данных: {e}", ephemeral=True)


# 3. КОМАНДА: УДАЛИТЬ ПАРОЛЬ
@bot.slash_command(name="пароль_удалить", description="Удалить сохраненный пароль из базы данных")
async def password_delete(
    ctx: disnake.ApplicationCommandInteraction,
    описание: str = commands.Param(description="Выберите название пароля для удаления", autocomplete=autocomp_passwords)
):
    await ctx.response.defer(ephemeral=True)
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM user_passwords WHERE user_id = ? AND title = ?", (ctx.author.id, описание))
        if not cursor.fetchone():
            conn.close()
            return await ctx.followup.send(f"⚠️ Пароль с описанием **«{описание}»** не найден!", ephemeral=True)
        
        cursor.execute("DELETE FROM user_passwords WHERE user_id = ? AND title = ?", (ctx.author.id, описание))
        conn.commit()
        conn.close()
        await ctx.followup.send(f"🗑️ Пароль под описанием **«{описание}»** успешно удален!", ephemeral=True)
    except Exception as e:
        await ctx.followup.send(f"❌ Ошибка базы данных: {e}", ephemeral=True)


# 4. КОМАНДА: ПОИСК ПАРОЛЯ
@bot.slash_command(name="пароль_найти", description="Найти пароль в базе данных по ключевому слову")
async def password_search(
    ctx: disnake.ApplicationCommandInteraction,
    запрос: str = commands.Param(description="Введите слово для поиска (например: Steam, отпуск, 123)")
):
    await ctx.response.defer(ephemeral=True)
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        search_pattern = f"%{запрос}%"
        cursor.execute(
            "SELECT title, password, vacation_info FROM user_passwords WHERE user_id = ? AND (title LIKE ? OR vacation_info LIKE ?)",
            (ctx.author.id, search_pattern, search_pattern)
        )
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return await ctx.followup.send(f"🔍 По запросу **«{запрос}»** ничего не найдено.", ephemeral=True)
        
        embed = disnake.Embed(
            title=f"🔍 Результаты поиска по запросу: «{запрос}»",
            description=f"Найдено совпадений: **{len(rows)}**.",
            color=disnake.Color.green()
        )
        for title, password, vacation_info in rows:
            field_value = f"**Пароль:** ||`{password}`||"
            if vacation_info != "-":
                field_value += f"\nℹ️ **Заметка:** *{vacation_info}*"
            embed.add_field(name=f"📌 {title}", value=field_value, inline=False)
        await ctx.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        await ctx.followup.send(f"❌ Ошибка базы данных: {e}", ephemeral=True)




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

bot.run("MTUxNzI2Mjc1Mjk0OTczNTQ0NQ.GgxjLw.KlBhCYS_fehOVsZnSzI19Tmwz2YAAMCBGlOfP4")



