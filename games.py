# ================================================================
# GAMES.PY — ИГРОВОЙ МОДУЛЬ DISCORD-БОТА
# ================================================================

import asyncio
import random

import disnake
from disnake.ext import commands


# ================================================================
# СТАТИСТИКА
# ================================================================

stats_minesweeper = {}
stats_roulette = {}
stats_casino_wins = {}
stats_casino_jackpots = {}

# Архив дел / память
cases_archive = {}

# Кэш созданных голосовых комнат
voice_channels_cache = {}

# Игровой канал
ALLOWED_GAME_CHANNEL_ID = 1525848983203877116


# ================================================================
# RUSSIAN ROULETTE
# ================================================================

class RouletteView(disnake.ui.View):

    def __init__(self, players, ctx):
        super().__init__(timeout=120)

        self.ctx = ctx
        self.players = players.copy()

        self.player1 = self.players[0]
        self.player2 = (
            self.players[1]
            if len(self.players) > 1
            else self.players[0]
        )

        self.bullet = random.randint(1, 6)
        self.current_shot = 1

        self.current_turn_index = 0
        self.current_turn = self.players[0]

        self.spins_used = {
            player.id: 0
            for player in self.players
        }

        card_pool = [
            "vest",
            "scan",
            "skip"
        ]

        self.player_cards = {
            player.id: random.choice(card_pool)
            for player in self.players
        }

    # ============================================================
    # ОБНОВЛЕНИЕ КНОПОК
    # ============================================================

    def update_buttons(self):

        try:
            if not self.players:
                return

            current_id = self.current_turn.id

            spins_left = max(
                0,
                2 - self.spins_used.get(current_id, 0)
            )

            card = self.player_cards.get(current_id)

            if len(self.children) > 1:

                self.children[1].label = (
                    f"Прокрутить барабан 🔄 ({spins_left})"
                )

                self.children[1].disabled = (
                    spins_left <= 0
                )

            if len(self.children) > 2:

                if card == "vest":

                    self.children[2].label = (
                        "Карта: 🛡️ Бронежилет"
                    )

                    self.children[2].disabled = True

                elif card == "scan":

                    self.children[2].label = (
                        "Использовать карту: 👀 Осмотр"
                    )

                    self.children[2].disabled = False

                elif card == "skip":

                    self.children[2].label = (
                        "Использовать карту: 🔀 Перевод"
                    )

                    self.children[2].disabled = False

                else:

                    self.children[2].label = (
                        "Карта использована 🫙"
                    )

                    self.children[2].disabled = True

        except Exception as e:

            print(
                f"[ROULETTE] Ошибка update_buttons: {e}"
            )

    # ============================================================
    # СЛЕДУЮЩИЙ ИГРОК
    # ============================================================

    def next_turn(self):

        if not self.players:
            return

        self.current_turn_index = (
            self.current_turn_index + 1
        ) % len(self.players)

        self.current_turn = (
            self.players[self.current_turn_index]
        )

    # ============================================================
    # ВЫСТРЕЛ
    # ============================================================

    @disnake.ui.button(
        label="Спустить курок 💥",
        style=disnake.ButtonStyle.danger,
        row=0
    )
    async def shoot_button(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction
    ):

        if interaction.author != self.current_turn:

            if interaction.author in self.players:

                await interaction.send(
                    f"⏳ Сейчас ход игрока "
                    f"{self.current_turn.mention}!",
                    ephemeral=True
                )

            else:

                await interaction.send(
                    "❌ Ты не участник этой игры.",
                    ephemeral=True
                )

            return

        message = interaction.message

        # ========================================================
        # ОСЕЧКА
        # ========================================================

        if random.random() < 0.10:

            self.next_turn()
            self.update_buttons()

            embed = disnake.Embed(
                title="🔧 ОСЕЧКА!",
                description=(
                    f"💥 {interaction.author.mention} "
                    f"нажал на спуск, но произошла осечка!\n\n"
                    f"Счётчик выстрелов остался "
                    f"**{self.current_shot}/6**.\n\n"
                    f"👉 Следующий ход: "
                    f"{self.current_turn.mention}"
                ),
                color=disnake.Color.blurple()
            )

            await interaction.response.edit_message(
                embed=embed,
                view=self
            )

            return

        # ========================================================
        # ПОПАДАНИЕ
        # ========================================================

        if self.current_shot == self.bullet:

            dead_player = self.current_turn

            # ====================================================
            # БРОНЕЖИЛЕТ
            # ====================================================

            if self.player_cards.get(dead_player.id) == "vest":

                self.player_cards[dead_player.id] = "used"

                self.bullet = random.randint(1, 6)
                self.current_shot = 1

                self.next_turn()
                self.update_buttons()

                embed = disnake.Embed(
                    title="🛡️ СПАСЕНИЕ БРОНЕЖИЛЕТОМ!",
                    description=(
                        f"💥 **БАХ!** Пуля летела прямо в "
                        f"{dead_player.mention}, но бронежилет "
                        f"спас игрока!\n\n"
                        f"🔄 Барабан автоматически "
                        f"перезаряжен.\n\n"
                        f"👉 Следующий ход: "
                        f"{self.current_turn.mention}"
                    ),
                    color=disnake.Color.blue()
                )

                await interaction.response.edit_message(
                    embed=embed,
                    view=self
                )

                return

            # ====================================================
            # ИГРОК ВЫБЫВАЕТ
            # ====================================================

            self.players.remove(dead_player)

            if len(self.players) == 1:

                winner = self.players[0]

                stats_roulette[winner.id] = (
                    stats_roulette.get(winner.id, 0) + 1
                )

                embed = disnake.Embed(
                    title="💀 БАХ! Дуэль окончена!",
                    description=(
                        f"💥 {dead_player.mention} "
                        f"выбывает из игры!\n\n"
                        f"🏆 **Победитель:** "
                        f"{winner.mention}\n\n"
                        f"📊 Победа добавлена "
                        f"в статистику."
                    ),
                    color=disnake.Color.red()
                )

                for child in self.children:
                    child.disabled = True

                await interaction.response.edit_message(
                    embed=embed,
                    view=self
                )

                self.stop()

                async def delete_message():

                    await asyncio.sleep(10)

                    try:
                        await message.delete()
                    except Exception:
                        pass

                asyncio.create_task(
                    delete_message()
                )

                return

            # ====================================================
            # ИГРА ПРОДОЛЖАЕТСЯ
            # ====================================================

            self.bullet = random.randint(1, 6)
            self.current_shot = 1

            if self.current_turn_index >= len(self.players):
                self.current_turn_index = 0

            self.current_turn = (
                self.players[self.current_turn_index]
            )

            self.update_buttons()

            embed = disnake.Embed(
                title="💀 КРОВЬ НА СТЕНАХ!",
                description=(
                    f"💥 **БАХ!** "
                    f"{dead_player.mention} "
                    f"выбывает!\n\n"
                    f"🔄 Барабан перезаряжен.\n\n"
                    f"👉 Следующий ход: "
                    f"{self.current_turn.mention}"
                ),
                color=disnake.Color.dark_red()
            )

            await interaction.response.edit_message(
                embed=embed,
                view=self
            )

            return

        # ========================================================
        # ХОЛОСТОЙ
        # ========================================================

        self.current_shot += 1

        if self.current_shot > 6:

            self.bullet = random.randint(1, 6)
            self.current_shot = 1

        self.next_turn()
        self.update_buttons()

        phrases = [

            f"*Клик!* Камора пуста. "
            f"{interaction.author.mention} выжил! 🎯",

            f"*Щёлк!* Пронесло! "
            f"Револьвер передаётся дальше...",

            f"*Клац!* Барабан щёлкнул. "
            f"Сегодня удача на твоей стороне! 😎"
        ]

        embed = disnake.Embed(
            title="😰 Дуэль продолжается!",
            description=(
                f"{random.choice(phrases)}\n\n"
                f"📊 Следующий выстрел: "
                f"**{self.current_shot}/6**\n\n"
                f"👉 Следующим стреляет: "
                f"{self.current_turn.mention}"
            ),
            color=disnake.Color.orange()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    # ============================================================
    # ПРОКРУТКА
    # ============================================================

    @disnake.ui.button(
        label="Прокрутить барабан 🔄",
        style=disnake.ButtonStyle.success,
        row=1
    )
    async def spin_button(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction
    ):

        if interaction.author != self.current_turn:

            await interaction.send(
                "⏳ Сейчас не твой ход!",
                ephemeral=True
            )

            return

        user_id = interaction.author.id

        if self.spins_used.get(user_id, 0) >= 2:

            await interaction.send(
                "❌ Ты уже использовал 2 прокрутки!",
                ephemeral=True
            )

            return

        self.spins_used[user_id] += 1

        self.bullet = random.randint(1, 6)
        self.current_shot = 1

        self.next_turn()
        self.update_buttons()

        embed = disnake.Embed(
            title="🌀 БАРАБАН РАСКРУЧЕН!",
            description=(
                f"🎲 {interaction.author.mention} "
                f"перекрутил барабан.\n\n"
                f"📊 Новый выстрел: **1/6**\n\n"
                f"👉 Ход передаётся: "
                f"{self.current_turn.mention}"
            ),
            color=disnake.Color.green()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    # ============================================================
    # КАРТА
    # ============================================================

    @disnake.ui.button(
        label="Использовать карту 🃏",
        style=disnake.ButtonStyle.secondary,
        row=2
    )
    async def card_button(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction
    ):

        if interaction.author != self.current_turn:

            await interaction.send(
                "⏳ Сейчас не твой ход!",
                ephemeral=True
            )

            return

        user_id = interaction.author.id
        card = self.player_cards.get(user_id)

        if card == "scan":

            self.player_cards[user_id] = "used"

            self.update_buttons()

            await interaction.response.edit_message(
                view=self
            )

            await interaction.send(
                f"👀 **Осмотр барабана**\n\n"
                f"Патрон находится в каморе "
                f"**№{self.bullet}**.\n"
                f"Текущий выстрел: "
                f"**{self.current_shot}/6**.",
                ephemeral=True
            )

        elif card == "skip":

            self.player_cards[user_id] = "used"

            old_player = self.current_turn

            self.next_turn()
            self.update_buttons()

            embed = disnake.Embed(
                title="🔀 ПЕРЕВОД СТРЕЛ!",
                description=(
                    f"🃏 {old_player.mention} "
                    f"использует карту **Перевод**!\n\n"
                    f"👉 Следующий игрок: "
                    f"{self.current_turn.mention}"
                ),
                color=disnake.Color.purple()
            )

            await interaction.response.edit_message(
                embed=embed,
                view=self
            )

        else:

            await interaction.send(
                "❌ У тебя нет доступной карты.",
                ephemeral=True
            )

    # ============================================================
    # ИНФО
    # ============================================================

    @disnake.ui.button(
        label="ℹ️ Инфо",
        style=disnake.ButtonStyle.secondary,
        row=3
    )
    async def info_button(
        self,
        button: disnake.ui.Button,
        interaction: disnake.MessageInteraction
    ):

        if (
            interaction.guild
            and interaction.author == interaction.guild.owner
        ):

            await interaction.send(
                f"🤫 **Секрет Создателя**\n\n"
                f"🔴 Патрон: камора №**{self.bullet}**\n"
                f"🎯 Текущий выстрел: "
                f"**{self.current_shot}/6**",
                ephemeral=True
            )

            return

        card = self.player_cards.get(
            interaction.author.id
        )

        card_names = {
            "vest":
                "🛡️ Бронежилет — спасает автоматически",

            "scan":
                "👀 Осмотр — показывает положение пули",

            "skip":
                "🔀 Перевод — передаёт ход",

            "used":
                "🫙 Карта уже использована"
        }

        await interaction.send(
            "ℹ️ **Русская рулетка**\n\n"
            "У тебя 2 прокрутки за игру.\n\n"
            f"🃏 Твоя карта: "
            f"**{card_names.get(card, 'Нет карты')}**",
            ephemeral=True
        )


# ================================================================
# MINESWEEPER
# ================================================================

class MinesweeperButton(disnake.ui.Button):

    def __init__(self, x, y, is_mine):

        super().__init__(
            label="❓",
            style=disnake.ButtonStyle.secondary,
            row=x
        )

        self.x = x
        self.y = y
        self.is_mine = is_mine

    async def callback(
        self,
        interaction: disnake.MessageInteraction
    ):

        if interaction.author != self.view.author:

            await interaction.send(
                "❌ Это не твоё минное поле!",
                ephemeral=True
            )

            return

        await interaction.response.defer()

        if self.is_mine:

            self.label = "💥"
            self.style = disnake.ButtonStyle.danger

            for child in self.view.children:

                child.disabled = True

                if hasattr(child, "is_mine"):

                    if child.is_mine:

                        child.label = "💣"
                        child.style = (
                            disnake.ButtonStyle.danger
                        )

            embed = disnake.Embed(
                title="💣 БУУУМ!",
                description=(
                    f"{interaction.author.mention} "
                    f"подорвался на клетке "
                    f"**[{self.x + 1}, {self.y + 1}]**!"
                ),
                color=disnake.Color.red()
            )

            await interaction.edit_original_response(
                embed=embed,
                view=self.view
            )

            self.view.stop()

            async def delete_game():

                await asyncio.sleep(10)

                try:
                    await self.view.ctx.delete_original_response()
                except Exception:
                    pass

            asyncio.create_task(
                delete_game()
            )

            return

        self.label = "✅"
        self.style = disnake.ButtonStyle.success
        self.disabled = True

        unopened = 0

        for child in self.view.children:

            if (
                hasattr(child, "is_mine")
                and not child.is_mine
                and child.label == "❓"
            ):
                unopened += 1

        if unopened == 0:

            for child in self.view.children:

                child.disabled = True

                if (
                    hasattr(child, "is_mine")
                    and child.is_mine
                ):

                    child.label = "💣"

            user_id = interaction.author.id

            stats_minesweeper[user_id] = (
                stats_minesweeper.get(user_id, 0) + 1
            )

            embed = disnake.Embed(
                title="🏆 ПОБЕДА!",
                description=(
                    f"{interaction.author.mention} "
                    f"разминировал всё поле!\n\n"
                    f"🎉 **+1 победа в статистику!**"
                ),
                color=disnake.Color.green()
            )

            await interaction.edit_original_response(
                embed=embed,
                view=self.view
            )

            self.view.stop()

        else:

            embed = disnake.Embed(
                title="🚩 Сапёр 3×3",
                description=(
                    f"✅ Клетка безопасна!\n\n"
                    f"Осталось открыть: **{unopened}** "
                    f"безопасных клеток."
                ),
                color=disnake.Color.blue()
            )

            await interaction.edit_original_response(
                embed=embed,
                view=self.view
            )


class MinesweeperCheatButton(disnake.ui.Button):

    def __init__(self):

        super().__init__(
            label="ℹ️ Инфо",
            style=disnake.ButtonStyle.secondary,
            row=4
        )

    async def callback(
        self,
        interaction: disnake.MessageInteraction
    ):

        if (
            interaction.guild
            and interaction.author == interaction.guild.owner
        ):

            rows = []

            for x in range(3):

                row = []

                for y in range(3):

                    mine = any(
                        hasattr(child, "is_mine")
                        and child.x == x
                        and child.y == y
                        and child.is_mine
                        for child in self.view.children
                    )

                    row.append(
                        "💣" if mine else "🟩"
                    )

                rows.append(" ".join(row))

            await interaction.send(
                "🤫 **Секретная карта мин:**\n\n"
                + "\n".join(rows),
                ephemeral=True
            )

        else:

            await interaction.send(
                "ℹ️ Это Сапёр 3×3. Удачи!",
                ephemeral=True
            )


class MinesweeperView(disnake.ui.View):

    def __init__(self, author, ctx):

        super().__init__(timeout=120)

        self.author = author
        self.ctx = ctx

        positions = [
            (x, y)
            for x in range(3)
            for y in range(3)
        ]

        mines = random.sample(
            positions,
            2
        )

        for x in range(3):

            for y in range(3):

                self.add_item(
                    MinesweeperButton(
                        x,
                        y,
                        (x, y) in mines
                    )
                )

        self.add_item(
            MinesweeperCheatButton()
        )


# ================================================================
# BUCKSHOT ROULETTE
# ================================================================

class BuckshotView(disnake.ui.View):

    def __init__(self, players, ctx):

        super().__init__(timeout=180)

        self.ctx = ctx
        self.players = players.copy()

        self.current_turn_index = 0
        self.current_turn = self.players[0]

        self.lives = {
            player.id: 3
            for player in self.players
        }

        self.generate_shotgun()

    # ============================================================
    # НОВАЯ ОБОЙМА
    # ============================================================

    def generate_shotgun(self):

        total_ammo = random.randint(3, 6)

        self.live_ammo = random.randint(
            1,
            total_ammo - 1
        )

        self.blank_ammo = (
            total_ammo - self.live_ammo
        )

        self.magazine = (
            [1] * self.live_ammo
            + [0] * self.blank_ammo
        )

        random.shuffle(self.magazine)

    # ============================================================
    # СЛЕДУЮЩИЙ ИГРОК
    # ============================================================

    def next_turn(self):

        if not self.players:
            return

        self.current_turn_index = (
            self.current_turn_index + 1
        ) % len(self.players)

        self.current_turn = (
            self.players[self.current_turn_index]
        )

    # ============================================================
    # ЖИЗНИ
    # ============================================================

    def get_status_str(self):

        result = []

        for player in self.players:

            hp = "❤️" * max(
                0,
                self.lives.get(player.id, 0)
            )

            result.append(
                f"{player.mention}: {hp}"
            )

        return "\n".join(result)

    # ============================================================
    # ПЕРЕЗАРЯДКА
    # ============================================================

    async def check_magazine_empty(
        self,
        interaction
    ):

        if self.magazine:
            return

        self.generate_shotgun()

        embed = disnake.Embed(
            title="🔄 ДРОБОВИК ПЕРЕЗАРЯЖЕН!",
            description=(
                f"Патроны закончились.\n\n"
                f"🔴 Боевых: **{self.live_ammo}**\n"
                f"🔵 Холостых: **{self.blank_ammo}**\n\n"
                f"📊 **Жизни:**\n"
                f"{self.get_status_str()}\n\n"
                f"👉 Ход: "
                f"{self.current_turn.mention}"
            ),
            color=disnake.Color.blue()
        )

        await interaction.message.edit(
            embed=embed,
            view=self
        )

    # ============================================================
    # ОБРАБОТКА ВЫСТРЕЛА
    # ============================================================

    async def handle_shot(
        self,
        interaction,
        target
    ):

        if interaction.author != self.current_turn:

            await interaction.send(
                f"⏳ Сейчас ход "
                f"{self.current_turn.mention}!",
                ephemeral=True
            )

            return

        if target not in self.players:

            await interaction.send(
                "❌ Этот игрок уже выбыл!",
                ephemeral=True
            )

            return

        shooter = self.current_turn

        if not self.magazine:
            self.generate_shotgun()

        is_live = self.magazine.pop(0)

        # ========================================================
        # БОЕВОЙ ПАТРОН
        # ========================================================

        if is_live == 1:

            self.live_ammo -= 1

            self.lives[target.id] -= 1

            if self.lives[target.id] <= 0:

                self.players.remove(target)

                death_msg = (
                    f"💀 **{target.mention} выбыл!** "
                    f"Все жизни потеряны."
                )

            else:

                death_msg = (
                    f"💥 {target.mention} получает "
                    f"ранение и теряет 1 жизнь!"
                )

            # ====================================================
            # КОНЕЦ ИГРЫ
            # ====================================================

            if len(self.players) == 1:

                winner = self.players[0]

                embed = disnake.Embed(
                    title="🏆 ИГРА ОКОНЧЕНА!",
                    description=(
                        f"{death_msg}\n\n"
                        f"👑 **Победитель:** "
                        f"{winner.mention}\n\n"
                        f"Он остался последним "
                        f"выжившим!"
                    ),
                    color=disnake.Color.green()
                )

                for child in self.children:
                    child.disabled = True

                await interaction.response.edit_message(
                    embed=embed,
                    view=self
                )

                self.stop()

                async def delete_game():

                    await asyncio.sleep(15)

                    try:
                        await interaction.message.delete()
                    except Exception:
                        pass

                asyncio.create_task(
                    delete_game()
                )

                return

            # ====================================================
            # ПРОДОЛЖЕНИЕ
            # ====================================================

            if self.current_turn_index >= len(self.players):
                self.current_turn_index = 0

            self.current_turn = (
                self.players[self.current_turn_index]
            )

            self.next_turn()

            embed = disnake.Embed(
                title="⚡ БОЕВОЙ ПАТРОН!",
                description=(
                    f"🔫 {shooter.mention} "
                    f"выстрелил в "
                    f"{target.mention}.\n\n"
                    f"{death_msg}\n\n"
                    f"📦 Осталось:\n"
                    f"🔴 Боевых: **{self.live_ammo}**\n"
                    f"🔵 Холостых: **{self.blank_ammo}**\n\n"
                    f"📊 **Состояние:**\n"
                    f"{self.get_status_str()}\n\n"
                    f"👉 Следующий ход: "
                    f"{self.current_turn.mention}"
                ),
                color=disnake.Color.red()
            )

            await interaction.response.edit_message(
                embed=embed,
                view=self
            )

            await self.check_magazine_empty(
                interaction
            )

        # ========================================================
        # ХОЛОСТОЙ
        # ========================================================

        else:

            self.blank_ammo -= 1

            keep_turn = (
                target == shooter
            )

            if not keep_turn:
                self.next_turn()

            if keep_turn:

                turn_text = (
                    "🔥 Холостой при выстреле "
                    "в себя — ход сохраняется!"
                )

            else:

                turn_text = (
                    "⏳ Ход передаётся дальше."
                )

            embed = disnake.Embed(
                title="💨 ХОЛОСТОЙ ПАТРОН!",
                description=(
                    f"*Щёлк!* {shooter.mention} "
                    f"выстрелил в "
                    f"{'себя' if target == shooter else target.mention}.\n\n"
                    f"{turn_text}\n\n"
                    f"📦 Осталось:\n"
                    f"🔴 Боевых: **{self.live_ammo}**\n"
                    f"🔵 Холостых: **{self.blank_ammo}**\n\n"
                    f"📊 **Состояние:**\n"
                    f"{self.get_status_str()}\n\n"
                    f"👉 Следующий ход: "
                    f"{self.current_turn.mention}"
                ),
                color=disnake.Color.light_gray()
            )

            await interaction.response.edit_message(
                embed=embed,
                view=self
            )

            await self.check_magazine_empty(
                interaction
            )

    # ============================================================
    # СТРЕЛЯТЬ В СЕБЯ
    # ============================================================

    @disnake.ui.button(
        label="Выстрелить в себя 👤",
        style=disnake.ButtonStyle.blurple,
        row=0
    )
    async def shoot_self(
        self,
        button,
        interaction
    ):

        await self.handle_shot(
            interaction,
            self.current_turn
        )

    # ============================================================
    # СТРЕЛЯТЬ В СОПЕРНИКА
    # ============================================================

    @disnake.ui.button(
        label="Выстрелить в соперника 🔫",
        style=disnake.ButtonStyle.danger,
        row=0
    )
    async def shoot_other(
        self,
        button,
        interaction
    ):

        if interaction.author != self.current_turn:

            await interaction.send(
                "⏳ Сейчас не твой ход!",
                ephemeral=True
            )

            return

        if len(self.players) < 2:

            await interaction.send(
                "❌ Некому стрелять!",
                ephemeral=True
            )

            return

        shooter_index = self.players.index(
            self.current_turn
        )

        target_index = (
            shooter_index + 1
        ) % len(self.players)

        target = self.players[target_index]

        await self.handle_shot(
            interaction,
            target
        )


# ================================================================
# GAMES COG
# ================================================================

class Games(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ============================================================
    # РУССКАЯ РУЛЕТКА
    # ============================================================

    @commands.slash_command(
        name="русская_рулетка",
        description="Вызвать участников на русскую рулетку"
    )
    async def russian_roulette(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        соперник: disnake.Member,
        соперник_2: disnake.Member = None,
        соперник_3: disnake.Member = None
    ):

        if ctx.channel.id != ALLOWED_GAME_CHANNEL_ID:

            await ctx.send(
                f"❌ Играть можно только в "
                f"<#{ALLOWED_GAME_CHANNEL_ID}>!",
                ephemeral=True
            )

            return

        raw_players = [
            ctx.author,
            соперник,
            соперник_2,
            соперник_3
        ]

        players = []

        for player in raw_players:

            if (
                player is not None
                and player not in players
            ):
                players.append(player)

        if len(players) < 2:

            await ctx.send(
                "❌ Нужно минимум 2 игрока!",
                ephemeral=True
            )

            return

        if any(
            player.bot
            for player in players
        ):

            await ctx.send(
                "❌ Боты не могут участвовать!",
                ephemeral=True
            )

            return

        players_text = ", ".join(
            player.mention
            for player in players
        )

        embed = disnake.Embed(
            title="⚔️ ВЫЗОВ НА ДУЭЛЬ!",
            description=(
                f"👥 Участники:\n"
                f"{players_text}\n\n"
                f"🔫 6 камор.\n"
                f"🔴 1 боевой патрон.\n"
                f"🃏 Каждый игрок получает "
                f"секретную карту.\n\n"
                f"👉 Первый ход: "
                f"{ctx.author.mention}"
            ),
            color=disnake.Color.dark_gray()
        )

        view = RouletteView(
            players,
            ctx
        )

        view.update_buttons()

        await ctx.send(
            embed=embed,
            view=view
        )

    # ============================================================
    # САПЁР
    # ============================================================

    @commands.slash_command(
        name="сапер",
        description="Сыграть в сапёра"
    )
    async def minesweeper(
        self,
        ctx: disnake.ApplicationCommandInteraction
    ):

        if ctx.channel.id != ALLOWED_GAME_CHANNEL_ID:

            await ctx.send(
                f"❌ Играть можно только в "
                f"<#{ALLOWED_GAME_CHANNEL_ID}>!",
                ephemeral=True
            )

            return

        embed = disnake.Embed(
            title="🚩 Интерактивный Сапёр",
            description=(
                "Минное поле **3×3**.\n\n"
                "💣 На поле спрятано 2 мины.\n"
                "✅ Нужно открыть все "
                "7 безопасных клеток."
            ),
            color=disnake.Color.blue()
        )

        view = MinesweeperView(
            ctx.author,
            ctx
        )

        await ctx.send(
            embed=embed,
            view=view
        )

    # ============================================================
    # КАЗИНО
    # ============================================================

    @commands.slash_command(
        name="казино",
        description="Испытать удачу в казино"
    )
    async def play_slots(
        self,
        ctx: disnake.ApplicationCommandInteraction
    ):

        slots = [
            "🍎",
            "🍋",
            "🍇",
            "🍒",
            "💎",
            "👑",
            "🍀"
        ]

        result = [
            random.choice(slots),
            random.choice(slots),
            random.choice(slots)
        ]

        slot1, slot2, slot3 = result

        user_id = ctx.author.id

        # ========================================================
        # ДЖЕКПОТ
        # ========================================================

        if slot1 == slot2 == slot3:

            stats_casino_jackpots[user_id] = (
                stats_casino_jackpots.get(user_id, 0) + 1
            )

            total = stats_casino_jackpots[user_id]

            embed = disnake.Embed(
                title="🎰 ДЖЕКПОТ! 🎉",
                description=(
                    f"{ctx.author.mention} "
                    f"выбил невероятную комбинацию!\n\n"
                    f"🎰 **[ {slot1} | {slot2} | {slot3} ]**\n\n"
                    f"🔥 **+1 ДЖЕКПОТ!**\n\n"
                    f"Всего джекпотов: **{total}**"
                ),
                color=disnake.Color.gold()
            )

            await ctx.send(
                embed=embed
            )

            return

        # ========================================================
        # ОБЫЧНАЯ ПОБЕДА
        # ========================================================

        if (
            slot1 == slot2
            or slot2 == slot3
            or slot1 == slot3
        ):

            stats_casino_wins[user_id] = (
                stats_casino_wins.get(user_id, 0) + 1
            )

            total = stats_casino_wins[user_id]

            embed = disnake.Embed(
                title="🎰 ПОБЕДА!",
                description=(
                    f"{ctx.author.mention} "
                    f"крутит барабаны!\n\n"
                    f"🎰 **[ {slot1} | {slot2} | {slot3} ]**\n\n"
                    f"✨ Два символа совпали!\n\n"
                    f"🏆 Обычных выигрышей: **{total}**"
                ),
                color=disnake.Color.green()
            )

            await ctx.send(
                embed=embed
            )

            return

        # ========================================================
        # ПРОИГРЫШ
        # ========================================================

        embed = disnake.Embed(
            title="🎰 НЕ ПОВЕЗЛО",
            description=(
                f"{ctx.author.mention}, "
                f"попробуй ещё раз!\n\n"
                f"🎰 **[ {slot1} | {slot2} | {slot3} ]**\n\n"
                f"❌ Все символы разные."
            ),
            color=disnake.Color.dark_gray()
        )

        message = await ctx.send(
            embed=embed
        )

        async def delete_losing_message():

            await asyncio.sleep(10)

            try:
                await message.delete()
            except Exception:
                pass

        asyncio.create_task(
            delete_losing_message()
        )

    # ============================================================
    # BUCKSHOT ROULETTE
    # ============================================================

    @commands.slash_command(
        name="бакшот",
        description="Запустить Buckshot Roulette"
    )
    async def buckshot_game(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        соперник_1: disnake.Member,
        соперник_2: disnake.Member = None,
        соперник_3: disnake.Member = None
    ):

        if ctx.channel.id != ALLOWED_GAME_CHANNEL_ID:

            await ctx.send(
                f"❌ Играть можно только в "
                f"<#{ALLOWED_GAME_CHANNEL_ID}>!",
                ephemeral=True
            )

            return

        raw_players = [
            ctx.author,
            соперник_1,
            соперник_2,
            соперник_3
        ]

        players = []

        for player in raw_players:

            if (
                player is not None
                and player not in players
            ):
                players.append(player)

        if len(players) < 2:

            await ctx.send(
                "❌ Нужно минимум 2 игрока!",
                ephemeral=True
            )

            return

        if any(
            player.bot
            for player in players
        ):

            await ctx.send(
                "❌ Боты не могут участвовать!",
                ephemeral=True
            )

            return

        view = BuckshotView(
            players,
            ctx
        )

        players_text = ", ".join(
            player.mention
            for player in players
        )

        embed = disnake.Embed(
            title="🩸 BUCKSHOT ROULETTE",
            description=(
                f"👥 **Участники:**\n"
                f"{players_text}\n\n"
                f"🔫 На столе дробовик.\n\n"
                f"🔴 Боевых патронов: "
                f"**{view.live_ammo}**\n"
                f"🔵 Холостых патронов: "
                f"**{view.blank_ammo}**\n\n"
                f"❤️ У каждого игрока по "
                f"**3 жизни**.\n\n"
                f"⚠️ Если выстрелить в себя "
                f"холостым патроном — ход сохраняется.\n\n"
                f"👉 Первый ход: "
                f"{ctx.author.mention}"
            ),
            color=disnake.Color.dark_red()
        )

        await ctx.send(
            embed=embed,
            view=view
        )


# ================================================================
# SETUP
# ================================================================

def setup(bot):
    bot.add_cog(
        Games(bot)
    )
