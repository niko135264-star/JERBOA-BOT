    # =========================================================
#                 PASSWORD SYSTEM
# =========================================================

import sqlite3
import disnake
from disnake.ext import commands


# =========================================================
#                 НАСТРОЙКИ
# =========================================================

DATABASE_NAME = "database.db"


# =========================================================
#                 ПОДКЛЮЧЕНИЕ К БД
# =========================================================

def get_db():
    """Создает подключение к базе данных."""
    return sqlite3.connect(DATABASE_NAME)


# =========================================================
#                 СОЗДАНИЕ ТАБЛИЦЫ
# =========================================================

def init_password_database():
    """Создает таблицу паролей, если её еще нет."""

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                password TEXT NOT NULL,
                vacation_info TEXT DEFAULT '-'
            )
        """)

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"[PASSWORD] Ошибка создания таблицы: {e}")


# =========================================================
#                 АВТОДОПОЛНЕНИЕ
# =========================================================

async def autocomp_passwords(
    ctx: disnake.ApplicationCommandInteraction,
    string: str
):
    """Показывает пользователю его сохраненные названия паролей."""

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT DISTINCT title
            FROM user_passwords
            WHERE user_id = ?
              AND title LIKE ?
            ORDER BY title
            LIMIT 25
            """,
            (
                ctx.author.id,
                f"{string}%"
            )
        )

        titles = [row[0] for row in cursor.fetchall()]

        conn.close()

        return titles

    except Exception as e:
        print(f"[PASSWORD AUTOCOMPLETE] Ошибка: {e}")
        return []


# =========================================================
#                 PASSWORD COG
# =========================================================

class Passwords(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    # =====================================================
    #                 ДОБАВИТЬ ПАРОЛЬ
    # =====================================================

    @commands.slash_command(
        name="пароль_добавить",
        description="Сохранить новый пароль в базу данных"
    )
    async def password_add(
        self,
        ctx: disnake.ApplicationCommandInteraction,

        описание: str = commands.Param(
            description="Что это за пароль? Например: Steam, Почта, VK"
        ),

        пароль: str = commands.Param(
            description="Сам пароль, который нужно сохранить"
        ),

        заметка: str = commands.Param(
            default="-",
            description="Дополнительная заметка (необязательно)"
        )
    ):

        await ctx.response.defer(ephemeral=True)

        try:

            # Защита от слишком длинных данных
            if len(описание) > 100:

                return await ctx.followup.send(
                    "❌ Описание слишком длинное! Максимум 100 символов.",
                    ephemeral=True
                )

            if len(пароль) > 500:

                return await ctx.followup.send(
                    "❌ Пароль слишком длинный! Максимум 500 символов.",
                    ephemeral=True
                )

            if len(заметка) > 500:

                return await ctx.followup.send(
                    "❌ Заметка слишком длинная! Максимум 500 символов.",
                    ephemeral=True
                )

            conn = get_db()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO user_passwords
                (user_id, title, password, vacation_info)
                VALUES (?, ?, ?, ?)
                """,
                (
                    ctx.author.id,
                    описание,
                    пароль,
                    заметка
                )
            )

            conn.commit()
            conn.close()

            text = (
                f"✅ Пароль под описанием "
                f"**«{описание}»** успешно сохранён!"
            )

            if заметка != "-":
                text += f"\n📌 Заметка: *{заметка}*"

            await ctx.followup.send(
                text,
                ephemeral=True
            )

        except Exception as e:

            print(f"[PASSWORD ADD] Ошибка: {e}")

            await ctx.followup.send(
                f"❌ Ошибка базы данных: `{e}`",
                ephemeral=True
            )


    # =====================================================
    #                 СПИСОК ПАРОЛЕЙ
    # =====================================================

    @commands.slash_command(
        name="пароли_список",
        description="Показать список всех ваших сохраненных паролей"
    )
    async def password_list(
        self,
        ctx: disnake.ApplicationCommandInteraction
    ):

        await ctx.response.defer(ephemeral=True)

        try:

            conn = get_db()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT title, password, vacation_info
                FROM user_passwords
                WHERE user_id = ?
                ORDER BY title
                """,
                (ctx.author.id,)
            )

            rows = cursor.fetchall()

            conn.close()

            if not rows:

                return await ctx.followup.send(
                    "📭 У вас пока нет сохранённых паролей.",
                    ephemeral=True
                )

            embed = disnake.Embed(
                title="🔑 Ваши сохранённые пароли",
                description=(
                    "🔒 Сообщение конфиденциально.\n"
                    "Нажмите на спойлер, чтобы увидеть пароль."
                ),
                color=disnake.Color.blue()
            )

            for title, password, note in rows:

                field_value = (
                    f"**Пароль:** ||`{password}`||"
                )

                if note and note != "-":

                    field_value += (
                        f"\nℹ️ **Заметка:** *{note}*"
                    )

                # Discord ограничивает значение field 1024 символами
                if len(field_value) > 1024:

                    field_value = (
                        field_value[:1000]
                        + "\n⚠️ Данные слишком длинные."
                    )

                embed.add_field(
                    name=f"📌 {title}"[:256],
                    value=field_value,
                    inline=False
                )

            await ctx.followup.send(
                embed=embed,
                ephemeral=True
            )

        except Exception as e:

            print(f"[PASSWORD LIST] Ошибка: {e}")

            await ctx.followup.send(
                f"❌ Ошибка базы данных: `{e}`",
                ephemeral=True
            )


    # =====================================================
    #                 УДАЛИТЬ ПАРОЛЬ
    # =====================================================

    @commands.slash_command(
        name="пароль_удалить",
        description="Удалить сохраненный пароль"
    )
    async def password_delete(
        self,
        ctx: disnake.ApplicationCommandInteraction,

        описание: str = commands.Param(
            description="Выберите название пароля для удаления",
            autocomplete=autocomp_passwords
        )
    ):

        await ctx.response.defer(ephemeral=True)

        try:

            conn = get_db()
            cursor = conn.cursor()

            # Проверяем наличие
            cursor.execute(
                """
                SELECT id
                FROM user_passwords
                WHERE user_id = ?
                  AND title = ?
                LIMIT 1
                """,
                (
                    ctx.author.id,
                    описание
                )
            )

            row = cursor.fetchone()

            if not row:

                conn.close()

                return await ctx.followup.send(
                    f"⚠️ Пароль с описанием "
                    f"**«{описание}»** не найден!",
                    ephemeral=True
                )

            # Удаляем
            cursor.execute(
                """
                DELETE FROM user_passwords
                WHERE user_id = ?
                  AND title = ?
                """,
                (
                    ctx.author.id,
                    описание
                )
            )

            deleted = cursor.rowcount

            conn.commit()
            conn.close()

            await ctx.followup.send(
                f"🗑️ Удалено записей: **{deleted}**\n"
                f"Пароль **«{описание}»** успешно удалён.",
                ephemeral=True
            )

        except Exception as e:

            print(f"[PASSWORD DELETE] Ошибка: {e}")

            await ctx.followup.send(
                f"❌ Ошибка базы данных: `{e}`",
                ephemeral=True
            )


    # =====================================================
    #                 ПОИСК ПАРОЛЯ
    # =====================================================

    @commands.slash_command(
        name="пароль_найти",
        description="Найти пароль по названию или заметке"
    )
    async def password_search(
        self,
        ctx: disnake.ApplicationCommandInteraction,

        запрос: str = commands.Param(
            description="Введите слово для поиска"
        )
    ):

        await ctx.response.defer(ephemeral=True)

        try:

            conn = get_db()
            cursor = conn.cursor()

            search_pattern = f"%{запрос}%"

            cursor.execute(
                """
                SELECT title, password, vacation_info
                FROM user_passwords
                WHERE user_id = ?
                  AND (
                        title LIKE ?
                        OR vacation_info LIKE ?
                      )
                ORDER BY title
                """,
                (
                    ctx.author.id,
                    search_pattern,
                    search_pattern
                )
            )

            rows = cursor.fetchall()

            conn.close()

            if not rows:

                return await ctx.followup.send(
                    f"🔍 По запросу **«{запрос}»** "
                    f"ничего не найдено.",
                    ephemeral=True
                )

            embed = disnake.Embed(
                title=f"🔍 Поиск: «{запрос}»",
                description=(
                    f"Найдено совпадений: **{len(rows)}**"
                ),
                color=disnake.Color.green()
            )

            for title, password, note in rows:

                field_value = (
                    f"**Пароль:** ||`{password}`||"
                )

                if note and note != "-":

                    field_value += (
                        f"\nℹ️ **Заметка:** *{note}*"
                    )

                if len(field_value) > 1024:

                    field_value = (
                        field_value[:1000]
                        + "\n⚠️ Данные слишком длинные."
                    )

                embed.add_field(
                    name=f"📌 {title}"[:256],
                    value=field_value,
                    inline=False
                )

            await ctx.followup.send(
                embed=embed,
                ephemeral=True
            )

        except Exception as e:

            print(f"[PASSWORD SEARCH] Ошибка: {e}")

            await ctx.followup.send(
                f"❌ Ошибка базы данных: `{e}`",
                ephemeral=True
            )


# =========================================================
#                 ИНИЦИАЛИЗАЦИЯ БД
# =========================================================

init_password_database()


# =========================================================
#                 SETUP ДЛЯ DISNAKE
# =========================================================

def setup(bot):
    bot.add_cog(Passwords(bot))
