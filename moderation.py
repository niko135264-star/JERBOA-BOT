import disnake
from disnake.ext import commands
import asyncio
import time

from config import (
    ALLOWED_MOD_ROLE_ID,
    ALLOWED_VOICE_ROLES,
)


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =========================================================
    # КОМАНДА 1: КИК
    # =========================================================

    @commands.slash_command(
        name="кик",
        description="Выгнать пользователя с сервера (Причина обязательна)"
    )
    @commands.has_any_role(
        1526250470849515688,
        1526250470849515688,
        1521855842964471918
    )
    async def kick(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        reason: str
    ):
        await member.kick(reason=reason)

        embed = disnake.Embed(
            title="👢 Изгнание участника",
            description=(
                f"Пользователь {member.mention} "
                f"был успешно кикнут с сервера."
            ),
            color=disnake.Color.orange()
        )

        embed.add_field(
            name="Модератор:",
            value=ctx.author.mention,
            inline=True
        )

        embed.add_field(
            name="Причина:",
            value=reason,
            inline=True
        )

        embed.set_thumbnail(
            url=member.display_avatar.url
        )

        await ctx.send(embed=embed)

    # =========================================================
    # КОМАНДА 2: БАН
    # =========================================================

    @commands.slash_command(
        name="бан",
        description="Забанить пользователя на сервере (Причина обязательна)"
    )
    @commands.has_any_role(
        1526250470849515688,
        1526250470849515688,
        1521855842964471918
    )
    async def ban(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        reason: str
    ):
        await member.ban(reason=reason)

        embed = disnake.Embed(
            title="🔒 Блокировка участника",
            description=(
                f"Пользователь {member.mention} "
                f"был навсегда забанен."
            ),
            color=disnake.Color.red()
        )

        embed.add_field(
            name="Модератор:",
            value=ctx.author.mention,
            inline=True
        )

        embed.add_field(
            name="Причина:",
            value=reason,
            inline=True
        )

        embed.set_thumbnail(
            url=member.display_avatar.url
        )

        await ctx.send(embed=embed)

    # =========================================================
    # КОМАНДА 2.5: БАН ПО ID
    # =========================================================

    @commands.slash_command(
        name="бан_ид",
        description=(
            "Забанить пользователя по его цифровому Discord ID "
            "(Только для Старшей Администрации)"
        )
    )
    async def ban_by_id(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        user_id: str,
        reason: str
    ):
        mod_role = ctx.author.get_role(ALLOWED_MOD_ROLE_ID)

        if not mod_role:
            embed_no_perms = disnake.Embed(
                description=(
                    "❌ У вас нет специальной роли "
                    "для использования этой команды!"
                ),
                color=disnake.Color.red()
            )

            await ctx.send(
                embed=embed_no_perms,
                ephemeral=True
            )

            return

        try:
            numeric_id = int(user_id)

            user = await self.bot.get_or_fetch_user(numeric_id)

            if user:

                await ctx.guild.ban(
                    user,
                    reason=reason
                )

                embed = disnake.Embed(
                    title="🔒 Блокировка по ID",
                    description=(
                        f"Пользователь **{user.name}** "
                        f"(ID: {user.id}) был успешно забанен."
                    ),
                    color=disnake.Color.red()
                )

                embed.add_field(
                    name="Модератор:",
                    value=ctx.author.mention,
                    inline=True
                )

                embed.add_field(
                    name="Причина:",
                    value=reason,
                    inline=True
                )

                if user.avatar:
                    embed.set_thumbnail(
                        url=user.avatar.url
                    )

                await ctx.send(embed=embed)

            else:
                await ctx.send(
                    "❌ Не удалось найти пользователя "
                    "с таким ID в базе Discord.",
                    ephemeral=True
                )

        except ValueError:
            await ctx.send(
                "❌ Ошибка: Введённый ID должен "
                "состоять только из цифр!",
                ephemeral=True
            )

        except disnake.NotFound:
            await ctx.send(
                "❌ Пользователь с таким ID не существует.",
                ephemeral=True
            )

        except Exception as e:
            await ctx.send(
                f"❌ Произошла ошибка при попытке бана: {e}",
                ephemeral=True
            )

    # =========================================================
    # КОМАНДА 3: РАЗБАН ПО ID
    # =========================================================

    @commands.slash_command(
        name="разбан",
        description="Разбанить пользователя по его цифровому Discord ID"
    )
    async def unban(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        user_id: str
    ):
        mod_role = ctx.author.get_role(ALLOWED_MOD_ROLE_ID)

        if not mod_role:
            embed_no_perms = disnake.Embed(
                description=(
                    "❌ У вас нет специальной роли "
                    "для использования этой команды!"
                ),
                color=disnake.Color.red()
            )

            await ctx.send(
                embed=embed_no_perms,
                ephemeral=True
            )

            return

        try:
            numeric_id = int(user_id)

            async for ban_entry in ctx.guild.bans():

                user = ban_entry.user

                if numeric_id == user.id:

                    await ctx.guild.unban(user)

                    embed = disnake.Embed(
                        title="🔓 Снятие блокировки по ID",
                        description=(
                            f"Пользователь **{user.name}** "
                            f"(ID: {user.id}) был успешно разбанен."
                        ),
                        color=disnake.Color.green()
                    )

                    embed.add_field(
                        name="Модератор:",
                        value=ctx.author.mention,
                        inline=True
                    )

                    if user.avatar:
                        embed.set_thumbnail(
                            url=user.avatar.url
                        )

                    await ctx.send(embed=embed)

                    return

            await ctx.send(
                "❌ Этот пользователь не найден "
                "в списке банов вашего сервера.",
                ephemeral=True
            )

        except ValueError:
            await ctx.send(
                "❌ Ошибка: Введённый ID должен "
                "состоять только из цифр!",
                ephemeral=True
            )

        except Exception as e:
            await ctx.send(
                f"❌ Произошла ошибка при попытке разбана: {e}",
                ephemeral=True
            )

    # =========================================================
    # КОМАНДА 4: ВЫДАТЬ РОЛЬ
    # =========================================================

    @commands.slash_command(
        name="выдать_роль",
        description="Выдать роль пользователю"
    )
    @commands.has_any_role(
        1526250470849515688,
        1526250470849515688,
        1521855842964471918
    )
    async def addrole(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        role: disnake.Role
    ):
        if role in member.roles:

            embed = disnake.Embed(
                description=(
                    f"⚠️ У {member.mention} уже есть "
                    f"роль {role.mention}!"
                ),
                color=disnake.Color.gold()
            )

            await ctx.send(
                embed=embed,
                ephemeral=True
            )

        else:

            await member.add_roles(role)

            embed = disnake.Embed(
                title="💼 Выдача роли",
                description=(
                    "Пользователю успешно присвоена новая роль."
                ),
                color=disnake.Color.blue()
            )

            embed.add_field(
                name="Кому:",
                value=member.mention,
                inline=True
            )

            embed.add_field(
                name="Роль:",
                value=role.mention,
                inline=True
            )

            await ctx.send(embed=embed)

    # =========================================================
    # КОМАНДА 5: УБРАТЬ РОЛЬ
    # =========================================================

    @commands.slash_command(
        name="убрать_роль",
        description="Забрать роль у пользователя"
    )
    @commands.has_any_role(
        1526250470849515688,
        1526250470849515688,
        1521855842964471918
    )
    async def removerole(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        role: disnake.Role
    ):
        if role not in member.roles:

            embed = disnake.Embed(
                description=(
                    f"⚠️ У {member.mention} нет "
                    f"роли {role.mention}!"
                ),
                color=disnake.Color.gold()
            )

            await ctx.send(
                embed=embed,
                ephemeral=True
            )

        else:

            await member.remove_roles(role)

            embed = disnake.Embed(
                title="❌ Снятие роли",
                description=(
                    "У пользователя успешно забрана роль."
                ),
                color=disnake.Color.dark_gray()
            )

            embed.add_field(
                name="У кого:",
                value=member.mention,
                inline=True
            )

            embed.add_field(
                name="Роль:",
                value=role.mention,
                inline=True
            )

            await ctx.send(embed=embed)

    # =========================================================
    # КОМАНДА: БАН-МУТ
    # =========================================================

    @commands.slash_command(
        name="бан-мут",
        description=(
            "Заполнить форму наказания "
            "для пользователя обычным текстом"
        )
    )
    @commands.has_any_role(
        1526250470849515688,
        1526250470849515688,
        1521855842964471918
    )
    async def ban_mut_form(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        member: disnake.User,
        наказание: str = commands.Param(
            choices=[
                "Мут",
                "Бан",
                "ЧС",
                "Кик из банды"
            ]
        ),
        срок: str = commands.Param(
            description="Например: 1 день, 3 часа, навсегда"
        ),
        причина: str = commands.Param(
            description="Укажите пункт правил или причину"
        )
    ):

        rules_text = (
            f"**Пользователь:** {member.mention}\n"
            f"**Получает:** {наказание} на **{срок}**\n"
            f"**Причина:** {причина}\n"
            f"-# Выдал модератор: `{ctx.author.name}`"
        )

        await ctx.channel.send(
            content=rules_text
        )

        await ctx.response.send_message(
            "✅ Успешно отправлено!",
            ephemeral=True
        )

    # =========================================================
    # КОМАНДА: ОЧИСТИТЬ
    # =========================================================

    @commands.slash_command(
        name="очистить",
        description="Удалить указанное количество сообщений из чата"
    )
    async def clear_messages(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        количество: int = commands.Param(
            description="Сколько сообщений удалить (например: 10, 50, 100)"
        )
    ):

        has_permission = any(
            ctx.author.get_role(role_id)
            for role_id in ALLOWED_VOICE_ROLES
        )

        if not has_permission:

            await ctx.send(
                "❌ У вас нет специальной роли "
                "для использования этой команды!",
                ephemeral=True
            )

            return

        if количество < 1 or количество > 100:

            await ctx.send(
                "❌ Можно удалить от 1 до 100 сообщений за раз!",
                ephemeral=True
            )

            return

        await ctx.response.defer(
            ephemeral=True
        )

        try:

            deleted = await ctx.channel.purge(
                limit=количество
            )

            await ctx.edit_original_response(
                content=(
                    f"🗑️ Успешно удалено сообщений: "
                    f"**{len(deleted)}**."
                )
            )

        except disnake.Forbidden:

            await ctx.edit_original_response(
                content=(
                    "❌ Критическая ошибка Дискорда! "
                    "Бот не может очистить чат.\n"
                    "**Как исправить:** Зайдите в настройки "
                    "этого канала -> Права доступа -> "
                    "Добавьте роль бота и включите "
                    "'Управлять сообщениями' и "
                    "'Читать историю сообщений'!"
                )
            )

        except Exception as e:

            await ctx.edit_original_response(
                content=f"❌ Техническая ошибка при очистке: {e}"
            )

    # =========================================================
    # КОМАНДА: ВРЕМЕННАЯ РОЛЬ
    # =========================================================

    @commands.slash_command(
        name="врем_роль",
        description="Выдать пользователю роль на определенное время"
    )
    @commands.has_any_role(
        1526250470849515688,
        1526250470849515688,
        1521855842964471918
    )
    async def temp_role(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        role: disnake.Role,
        время: int = commands.Param(
            description="Укажите число времени (например: 10, 5, 2)"
        ),
        тип: str = commands.Param(
            choices=[
                "Секунды",
                "Минуты",
                "Часы",
                "Дни"
            ]
        )
    ):

        time_multipliers = {
            "Секунды": 1,
            "Минуты": 60,
            "Часы": 3600,
            "Дни": 86400
        }

        seconds = время * time_multipliers[тип]

        end_timestamp = int(
            time.time() + seconds
        )

        if role in member.roles:

            embed = disnake.Embed(
                description=(
                    f"⚠️ У {member.mention} уже есть "
                    f"роль {role.mention}!"
                ),
                color=disnake.Color.gold()
            )

            return await ctx.send(
                embed=embed,
                ephemeral=True
            )

        try:

            await member.add_roles(
                role,
                reason="Выдача временной роли (начало срока)"
            )

            embed_start = disnake.Embed(
                title="⏱️ Выдана временная роль",
                description=(
                    "Пользователю успешно выдана роль "
                    "на заданный срок."
                ),
                color=disnake.Color.purple()
            )

            embed_start.add_field(
                name="Кому:",
                value=member.mention,
                inline=True
            )

            embed_start.add_field(
                name="Роль:",
                value=role.mention,
                inline=True
            )

            embed_start.add_field(
                name="Истекает:",
                value=(
                    f"<t:{end_timestamp}:F> "
                    f"(<t:{end_timestamp}:R>)"
                ),
                inline=False
            )

            await ctx.send(
                embed=embed_start
            )

            await asyncio.sleep(seconds)

            member_now = ctx.guild.get_member(
                member.id
            )

            if member_now and role in member_now.roles:

                await member_now.remove_roles(
                    role,
                    reason="Временная роль (истек срок)"
                )

                embed_end = disnake.Embed(
                    title="⏳ Время роли истекло",
                    description=(
                        f"У пользователя {member_now.mention} "
                        f"была автоматически забрана "
                        f"временная роль {role.mention}.\n\n"
                        f"*🗑️ Это сообщение удалится через 10 секунд.*"
                    ),
                    color=0x2B2D31
                )

                await ctx.channel.send(
                    embed=embed_end,
                    delete_after=10
                )

        except disnake.Forbidden:

            await ctx.send(
                "❌ Ошибка: У бота нет прав "
                "(роль бота должна быть выше выдаваемой роли)!",
                ephemeral=True
            )

        except Exception as e:

            await ctx.send(
                f"❌ Критическая ошибка: {e}",
                ephemeral=True
            )

    # =========================================================
    # КОМАНДА: ЗАМЕНИТЬ РОЛЬ НА ВРЕМЯ
    # =========================================================

    @commands.slash_command(
        name="заменить_роль_время",
        description=(
            "Временно заменить одну роль на другую "
            "с авто-возвратом через время"
        )
    )
    @commands.has_any_role(
        1526250470849515688,
        1526250470849515688,
        1521855842964471918
    )
    async def replace_role_temp(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        участник: disnake.Member,
        забрать_роль: disnake.Role,
        выдать_роль: disnake.Role,
        время: int = commands.Param(
            description="Число времени (например: 10, 5, 2)"
        ),
        тип: str = commands.Param(
            choices=[
                "Секунды",
                "Минуты",
                "Часы",
                "Дни"
            ]
        )
    ):

        time_multipliers = {
            "Секунды": 1,
            "Минуты": 60,
            "Часы": 3600,
            "Дни": 86400
        }

        seconds = время * time_multipliers[тип]

        end_timestamp = int(
            time.time() + seconds
        )

        if забрать_роль not in участник.roles:

            return await ctx.send(
                f"❌ У {участник.mention} нет "
                f"роли {забрать_роль.mention}!",
                ephemeral=True
            )

        if выдать_роль in участник.roles:

            return await ctx.send(
                f"⚠️ У {участник.mention} уже есть "
                f"роль {выдать_роль.mention}!",
                ephemeral=True
            )

        try:

            await участник.remove_roles(
                забрать_роль,
                reason="Временная замена роли (начало срока)"
            )

            await участник.add_roles(
                выдать_роль,
                reason="Временная замена роли (начало срока)"
            )

            embed_start = disnake.Embed(
                title="🔄 Временная замена роли",
                description="Роли участника успешно изменены.",
                color=disnake.Color.purple()
            )

            embed_start.add_field(
                name="Кому:",
                value=участник.mention,
                inline=False
            )

            embed_start.add_field(
                name="🗑️ Временно забрано:",
                value=забрать_роль.mention,
                inline=True
            )

            embed_start.add_field(
                name="💼 Временно выдано:",
                value=выдать_роль.mention,
                inline=True
            )

            embed_start.add_field(
                name="⏱️ Истекает:",
                value=(
                    f"<t:{end_timestamp}:F> "
                    f"(<t:{end_timestamp}:R>)"
                ),
                inline=False
            )

            await ctx.send(
                embed=embed_start
            )

            await asyncio.sleep(seconds)

            member_now = ctx.guild.get_member(
                участник.id
            )

            if member_now and выдать_роль in member_now.roles:

                await member_now.remove_roles(
                    выдать_роль,
                    reason="Временная замена роли (истек срок)"
                )

                await member_now.add_roles(
                    забрать_роль,
                    reason="Временная замена роли (истек срок)"
                )

                embed_end = disnake.Embed(
                    title="⏳ Время замены истекло",
                    description=(
                        f"Роли участника {member_now.mention} "
                        f"автоматически возвращены!\n"
                        f"↩️ Вернули: {забрать_роль.mention}\n"
                        f"❌ Забрали: {выдать_роль.mention}\n\n"
                        f"*🗑️ Это сообщение удалится через 10 секунд.*"
                    ),
                    color=0x2B2D31
                )

                await ctx.channel.send(
                    embed=embed_end,
                    delete_after=10
                )

        except disnake.Forbidden:

            await ctx.send(
                "❌ Ошибка: Иерархия ролей бота слишком "
                "низкая для управления этими ролями!",
                ephemeral=True
            )

        except Exception as e:

            await ctx.send(
                f"❌ Критическая ошибка: {e}",
                ephemeral=True
            )

    # =========================================================
    # КОМАНДА: ПРАВА РОЛИ
    # =========================================================

    @commands.slash_command(
        name="права_роли",
        description="Показать главные административные права конкретной роли"
    )
    async def check_role_perms(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        роль: disnake.Role
    ):

        perms = роль.permissions

        perms_list = [
            f"{'✅' if perms.administrator else '❌'} Администратор",
            f"{'✅' if perms.ban_members else '❌'} Бан участников",
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
            color=(
                роль.color
                if роль.color.value != 0
                else disnake.Color.blue()
            )
        )

        embed_perms.add_field(
            name="🆔 ID Роли:",
            value=f"`{роль.id}`",
            inline=True
        )

        embed_perms.add_field(
            name="🎨 Цвет роли:",
            value=f"`{роль.color}`",
            inline=True
        )

        embed_perms.set_footer(
            text=f"Проверил: {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url
        )

        await ctx.send(
            embed=embed_perms
        )

    # =========================================================
    # КОМАНДА: СПИСОК БАНОВ
    # =========================================================

    @commands.slash_command(
        name="список_банов",
        description=(
            "Показать список всех забаненных пользователей "
            "и причины их блокировки"
        )
    )
    async def show_server_bans(
        self,
        ctx: disnake.ApplicationCommandInteraction
    ):

        has_permission = any(
            ctx.author.get_role(role_id)
            for role_id in ALLOWED_VOICE_ROLES
        )

        if not has_permission:

            await ctx.send(
                "❌ У вас нет специальной роли "
                "для использования этой команды!",
                ephemeral=True
            )

            return

        await ctx.response.defer(
            ephemeral=True
        )

        try:

            lines = []
            count = 0

            async for ban_entry in ctx.guild.bans():

                count += 1

                user = ban_entry.user

                reason = (
                    ban_entry.reason
                    if ban_entry.reason
                    else "Причина не указана администратором"
                )

                if count <= 15:

                    lines.append(
                        f"🔨 **{count}. {user.name}**\n"
                        f"🆔 ID: `{user.id}`\n"
                        f"📜 Причина: *{reason}*\n"
                    )

            if count == 0:

                embed_empty = disnake.Embed(
                    title="🛡️ ЧЁРНЫЙ СПИСОК СЕРВЕРА",
                    description=(
                        "✨ На сервере идеальный порядок! "
                        "В бан-листе нет ни одного пользователя."
                    ),
                    color=disnake.Color.green()
                )

                await ctx.edit_original_response(
                    embed=embed_empty
                )

                return

            result_text = "\n".join(lines)

            if count > 15:

                result_text += (
                    f"\n*...и ещё {count - 15} "
                    f"нарушителей в глубине списка.*"
                )

            embed_bans = disnake.Embed(
                title="🔨 ОФИЦИАЛЬНЫЙ ЧЁРНЫЙ СПИСОК СЕРВЕРА",
                description=(
                    f"Всего заблокировано учётных записей: "
                    f"**{count}**\n\n{result_text}"
                ),
                color=disnake.Color.red()
            )

            embed_bans.set_footer(
                text=f"Запрос выполнил: {ctx.author.name}",
                icon_url=ctx.author.display_avatar.url
            )

            await ctx.edit_original_response(
                embed=embed_bans
            )

        except disnake.Forbidden:

            await ctx.edit_original_response(
                content=(
                    "❌ Ошибка прав: у бота нет разрешения "
                    "'Банить участников' (Ban Members)!"
                )
            )

        except Exception as e:

            await ctx.edit_original_response(
                content=(
                    f"❌ Техническая ошибка при "
                    f"сборе бан-листа: {e}"
                )
            )


# =============================================================
# ПОДКЛЮЧЕНИЕ COG К БОТУ
# =============================================================

def setup(bot):
    bot.add_cog(
        Moderation(bot)
    )
