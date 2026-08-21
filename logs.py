# ============================================================
# LOGS.PY — ЛОГИ, СКАЗАТЬ, АВТОВЫДАЧА РОЛИ, СПИСОК БАНОВ
# ============================================================

import disnake
from disnake.ext import commands

from config import ALLOWED_VOICE_ROLES


# ============================================================
# НАСТРОЙКИ
# ============================================================

# Канал, в котором работает автоматическая выдача роли по ✅
APPROVAL_CHANNEL_ID = 1521982898968854688

# Роль, которую получает пользователь после одобрения
ROLE_TO_GIVE_ID = 1521855410468946011

# Старая роль, которая снимается после одобрения
ROLE_TO_REMOVE_ID = 1521855978394353664

# Роли, которым разрешено использовать модераторские функции
ALLOWED_MOD_ROLES = [
    1521855914951442433,
    1526250470849515688,
    1521855842964471918
]


# ============================================================
# COG
# ============================================================

class Logs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ========================================================
    # ПРОВЕРКА МОДЕРАТОРСКОЙ РОЛИ
    # ========================================================

    def has_mod_role(self, member: disnake.Member) -> bool:

        if not member:
            return False

        return any(
            role.id in ALLOWED_MOD_ROLES
            for role in member.roles
        )

    # ========================================================
    # КОМАНДА: СКАЗАТЬ
    # ========================================================

    @commands.slash_command(
        name="сказать",
        description="Отправляет сообщение от имени бота"
    )
    @commands.has_any_role(
        *ALLOWED_MOD_ROLES
    )
    async def say(
        self,
        inter: disnake.ApplicationCommandInteraction,
        текст: str
    ):

        await inter.channel.send(текст)

        await inter.response.send_message(
            "✅ Сообщение успешно отправлено!",
            ephemeral=True
        )

    # ========================================================
    # АВТОВЫДАЧА РОЛИ ПО ✅
    # ========================================================

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self,
        payload: disnake.RawReactionActionEvent
    ):

        # Проверяем канал
        if payload.channel_id != APPROVAL_CHANNEL_ID:
            return

        # Проверяем эмодзи
        if payload.emoji.name != "✅":
            return

        # Получаем сервер
        guild = self.bot.get_guild(payload.guild_id)

        if not guild:
            return

        # Получаем модератора
        moderator = payload.member

        if not moderator:
            try:
                moderator = await guild.fetch_member(
                    payload.user_id
                )
            except Exception:
                return

        # Бот не может быть модератором
        if moderator.bot:
            return

        # Проверяем права модератора
        if not self.has_mod_role(moderator):
            return

        # Получаем канал
        channel = guild.get_channel(
            payload.channel_id
        )

        if not channel:
            return

        if not isinstance(
            channel,
            disnake.TextChannel
        ):
            return

        try:

            # Получаем сообщение
            message = await channel.fetch_message(
                payload.message_id
            )

            # Получаем автора сообщения
            author = guild.get_member(
                message.author.id
            )

            if not author:
                try:
                    author = await guild.fetch_member(
                        message.author.id
                    )
                except Exception:
                    return

            # Не выдаём роль ботам
            if author.bot:
                return

            # ================================================
            # НОВАЯ РОЛЬ
            # ================================================

            role_to_give = guild.get_role(
                ROLE_TO_GIVE_ID
            )

            if role_to_give:

                if role_to_give not in author.roles:

                    await author.add_roles(
                        role_to_give,
                        reason=(
                            f"Одобрено модератором "
                            f"{moderator}"
                        )
                    )

            # ================================================
            # СТАРАЯ РОЛЬ
            # ================================================

            role_to_remove = guild.get_role(
                ROLE_TO_REMOVE_ID
            )

            if role_to_remove:

                if role_to_remove in author.roles:

                    await author.remove_roles(
                        role_to_remove,
                        reason=(
                            f"Снято после одобрения "
                            f"модератором {moderator}"
                        )
                    )

            print(
                f"[LOGS] Модератор {moderator} "
                f"одобрил пользователя {author}"
            )

        except disnake.NotFound:
            print(
                "[LOGS] Сообщение или пользователь "
                "не найден."
            )

        except disnake.Forbidden:
            print(
                "[LOGS] У бота недостаточно прав "
                "для выдачи/снятия роли."
            )

        except Exception as e:
            print(
                f"[LOGS] Ошибка выдачи/снятия роли: {e}"
            )

    # ========================================================
    # КОМАНДА: ЛОГ
    # ========================================================

    @commands.slash_command(
        name="лог",
        description="Создать лог пользователя"
    )
    @commands.has_any_role(
        *ALLOWED_MOD_ROLES
    )
    async def log_form(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        наказание: str = commands.Param(
            choices=[
                "Мут",
                "Бан",
                "ЧС",
                "Отпуск",
                "Испытательный срок"
            ]
        ),
        срок: str = commands.Param(
            description=(
                "Например: 1 день, "
                "3 часа, навсегда"
            )
        ),
        причина: str = commands.Param(
            description=(
                "Укажите пункт правил или причину"
            )
        ),
        от: str = commands.Param(
            default=None,
            description=(
                "Любой текст, например: "
                "С какого дня/числа"
            )
        ),
        до: str = commands.Param(
            default=None,
            description=(
                "Любой текст, например: "
                "До какого дня/числа"
            )
        )
    ):

        log_description = (
            f"**Пользователь:** {member.mention}\n"
            f"**Получает:** {наказание} "
            f"на **{срок}**\n"
            f"**Причина:** {причина}\n"
        )

        if от:
            log_description += (
                f"**От:** {от}\n"
            )

        if до:
            log_description += (
                f"**До:** {до}\n"
            )

        embed = disnake.Embed(
            title="📋 Лог пользователя",
            description=log_description,
            color=0x000001
        )

        embed.set_thumbnail(
            url=member.display_avatar.url
        )

        await ctx.channel.send(
            embed=embed
        )

        await ctx.response.send_message(
            "⚙️ Лог создан.",
            ephemeral=True
        )


# ============================================================
# SETUP
# ============================================================

def setup(bot):
    bot.add_cog(Logs(bot))
