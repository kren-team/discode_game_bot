from __future__ import annotations

import asyncio
import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from src.data.words import get_random_word, is_valid_word
from src.games.wordle_game import (
    GamePhase,
    Player,
    PlayerState,
    WordleGame,
)

log = logging.getLogger(__name__)

RECRUITMENT_TIMEOUT = 60  # seconds


# ---------------------------------------------------------------------------
# Embed builders
# ---------------------------------------------------------------------------


def build_recruitment_embed(
    game: WordleGame,
    host: discord.Member | discord.User,
) -> discord.Embed:
    """Build the embed shown during the recruitment phase."""
    embed = discord.Embed(
        title="✋ Wordle 参加者募集中！",
        description=(
            "5文字の英単語を当てるゲームです！\n"
            "「参加する ✋」ボタンを押して参加しよう！\n"
            f"ホストが「ゲームを始める ▶」を押すか、{RECRUITMENT_TIMEOUT}秒後に自動スタートします。"
        ),
        color=discord.Color.blue(),
    )
    embed.add_field(name="ホスト", value=host.display_name, inline=True)

    player_list = (
        "\n".join(f"• {p.display_name}" for p in game.players.values())
        if game.players
        else "（まだいません）"
    )
    embed.add_field(name=f"参加者 ({len(game.players)}人)", value=player_list, inline=False)
    return embed


def build_game_embed(game: WordleGame) -> discord.Embed:
    """Build the in-progress game status embed."""
    embed = discord.Embed(
        title="🟩 Wordle 進行中",
        description="5文字の英単語を当てよう！ 最大5回まで推測できます",
        color=discord.Color.green(),
    )

    for player in game.players.values():
        status_label = _player_status_label(player)
        guess_count = f"{player.guess_count}/{game.MAX_GUESSES}"
        field_name = f"👤 {player.display_name} ({guess_count}){status_label}"

        if player.guesses:
            lines = [result.to_display() for result in player.guesses]
            field_value = "\n".join(lines)
        else:
            field_value = "（まだ推測なし）"

        embed.add_field(name=field_name, value=field_value, inline=False)

    embed.set_footer(text="推測: /guess <単語>")
    return embed


def build_end_embed(game: WordleGame) -> discord.Embed:
    """Build the game-over summary embed."""
    embed = discord.Embed(
        title="🏆 ゲーム終了！",
        description=f"答えは **{game.word}** でした！",
        color=discord.Color.gold(),
    )

    scoreboard = game.get_scoreboard()
    result_lines: list[str] = []

    for rank, player in enumerate(scoreboard, start=1):
        if player.state == PlayerState.WON:
            medal = _rank_medal(rank)
            result_lines.append(
                f"{medal} **{player.display_name}**: {player.guess_count}ターンで正解！"
            )
        elif player.state == PlayerState.LOST:
            result_lines.append(f"💀 **{player.display_name}**: 5回全て不正解")
        else:
            result_lines.append(f"⏳ **{player.display_name}**: 未完了")

    embed.add_field(
        name="結果",
        value="\n".join(result_lines) if result_lines else "（結果なし）",
        inline=False,
    )
    return embed


def _player_status_label(player: Player) -> str:
    if player.state == PlayerState.WON:
        return "  ✅ 正解！"
    if player.state == PlayerState.LOST:
        return "  💀 失敗"
    return ""


def _rank_medal(rank: int) -> str:
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    return medals.get(rank, f"#{rank}")


# ---------------------------------------------------------------------------
# UI Views
# ---------------------------------------------------------------------------


class JoinView(discord.ui.View):
    """
    Buttons shown during recruitment phase:
    - 参加する ✋  (primary)  — any user can click to join
    - ゲームを始める ▶  (success) — host only, force-starts the game
    """

    def __init__(self, cog: WordleCog, channel_id: int) -> None:
        super().__init__(timeout=None)
        self.cog = cog
        self.channel_id = channel_id

    @discord.ui.button(label="参加する ✋", style=discord.ButtonStyle.primary, custom_id="wordle_join")
    async def join_button(  # type: ignore[override]
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ) -> None:
        game = self.cog.active_games.get(self.channel_id)
        if game is None or game.phase != GamePhase.RECRUITING:
            await interaction.response.send_message(
                "現在参加受付中のゲームはありません。", ephemeral=True
            )
            return

        added = game.add_player(
            user_id=interaction.user.id,
            display_name=interaction.user.display_name,
        )

        if not added:
            await interaction.response.send_message(
                "すでに参加しています！", ephemeral=True
            )
            return

        # Update the recruitment embed
        host = interaction.guild.get_member(game.host_id) if interaction.guild else None
        embed = build_recruitment_embed(game, host or interaction.user)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="ゲームを始める ▶",
        style=discord.ButtonStyle.success,
        custom_id="wordle_start",
    )
    async def start_button(  # type: ignore[override]
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ) -> None:
        game = self.cog.active_games.get(self.channel_id)
        if game is None or game.phase != GamePhase.RECRUITING:
            await interaction.response.send_message(
                "ゲームは既に開始されているか、存在しません。", ephemeral=True
            )
            return

        if interaction.user.id != game.host_id:
            await interaction.response.send_message(
                "ゲームを始められるのはホストだけです！", ephemeral=True
            )
            return

        if not game.players:
            await interaction.response.send_message(
                "参加者が0人です。少なくとも1人が参加してからスタートしてください。",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        await self.cog.start_game(self.channel_id, interaction)


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class WordleCog(commands.Cog):
    """Discord cog for the multiplayer Wordle game."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # channel_id -> WordleGame
        self.active_games: dict[int, WordleGame] = {}
        # channel_id -> asyncio.Task (recruitment timeout)
        self._recruit_tasks: dict[int, asyncio.Task] = {}
        # channel_id -> discord.Message (the game status embed message)
        self._game_messages: dict[int, discord.Message] = {}
        # channel_id -> discord.Message (the recruitment message)
        self._recruit_messages: dict[int, discord.Message] = {}

    # ------------------------------------------------------------------
    # Slash commands
    # ------------------------------------------------------------------

    @app_commands.command(name="wordle", description="Wordleゲームを開始します")
    async def wordle_command(self, interaction: discord.Interaction) -> None:
        channel_id = interaction.channel_id
        assert channel_id is not None

        if channel_id in self.active_games:
            await interaction.response.send_message(
                "このチャンネルでは既にゲームが進行中です！", ephemeral=True
            )
            return

        game = WordleGame(
            host_id=interaction.user.id,
            channel_id=channel_id,
        )
        self.active_games[channel_id] = game

        embed = build_recruitment_embed(game, interaction.user)
        view = JoinView(cog=self, channel_id=channel_id)

        await interaction.response.send_message(embed=embed, view=view)
        recruit_message = await interaction.original_response()
        self._recruit_messages[channel_id] = recruit_message

        # Schedule automatic game start after RECRUITMENT_TIMEOUT seconds
        task = asyncio.create_task(
            self._auto_start(channel_id),
            name=f"wordle_recruit_{channel_id}",
        )
        self._recruit_tasks[channel_id] = task

    @app_commands.command(name="stop", description="進行中のWordleゲームを中断します（ホストのみ）")
    async def stop_command(self, interaction: discord.Interaction) -> None:
        channel_id = interaction.channel_id
        assert channel_id is not None

        game = self.active_games.get(channel_id)
        if game is None:
            await interaction.response.send_message(
                "このチャンネルではゲームが進行中ではありません。", ephemeral=True
            )
            return

        if interaction.user.id != game.host_id:
            await interaction.response.send_message(
                "ゲームを中断できるのはホストだけです！", ephemeral=True
            )
            return

        was_playing = game.phase == GamePhase.PLAYING
        answer = game.word if was_playing else None
        self._cleanup_game(channel_id)

        if was_playing:
            await interaction.response.send_message(
                f"🛑 **{interaction.user.display_name}** がゲームを中断しました。\n答えは **{answer}** でした。"
            )
        else:
            await interaction.response.send_message(
                f"🛑 **{interaction.user.display_name}** が参加者募集をキャンセルしました。"
            )

    @app_commands.command(name="guess", description="Wordleで単語を推測します")
    @app_commands.describe(word="推測する5文字の英単語")
    async def guess_command(
        self, interaction: discord.Interaction, word: str
    ) -> None:
        channel_id = interaction.channel_id
        assert channel_id is not None

        game = self.active_games.get(channel_id)

        # --- Phase guards ---
        if game is None:
            await interaction.response.send_message(
                "このチャンネルではゲームが進行中ではありません。`/wordle` でゲームを始めましょう！",
                ephemeral=True,
            )
            return

        if game.phase == GamePhase.RECRUITING:
            await interaction.response.send_message(
                "まだ参加者募集中です。ホストがゲームを開始するまでお待ちください。",
                ephemeral=True,
            )
            return

        if game.phase == GamePhase.ENDED:
            await interaction.response.send_message(
                "ゲームは既に終了しています。", ephemeral=True
            )
            return

        # --- Player guard ---
        if not game.has_player(interaction.user.id):
            await interaction.response.send_message(
                "あなたはこのゲームに参加していません。", ephemeral=True
            )
            return

        player = game.players[interaction.user.id]
        if not player.is_active():
            if player.state == PlayerState.WON:
                await interaction.response.send_message(
                    "あなたはすでに正解しています！他のプレイヤーを応援しましょう！",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "あなたはすでに5回推測し終えました。", ephemeral=True
                )
            return

        # --- Word validation ---
        word_upper = word.upper()

        if len(word_upper) != 5:
            await interaction.response.send_message(
                f"単語は5文字でなければなりません。「{word}」は{len(word)}文字です。",
                ephemeral=True,
            )
            return

        if not word_upper.isalpha():
            await interaction.response.send_message(
                "英字のみ入力してください。", ephemeral=True
            )
            return

        if not is_valid_word(word_upper):
            await interaction.response.send_message(
                f"「{word_upper}」は単語リストにありません。別の単語を試してください。",
                ephemeral=True,
            )
            return

        # --- Process guess ---
        result = game.check_guess(interaction.user.id, word_upper)
        if result is None:
            await interaction.response.send_message(
                "推測を処理できませんでした。", ephemeral=True
            )
            return

        # Acknowledge so Discord doesn't time out while we edit the embed
        await interaction.response.defer(ephemeral=False)

        # Update the game embed
        await self._update_game_embed(channel_id)

        # Send feedback for this specific guess
        if result.is_correct():
            feedback = (
                f"🎉 **{interaction.user.display_name}** が正解しました！\n"
                f"{result.to_display()}"
            )
        else:
            remaining = game.MAX_GUESSES - player.guess_count
            if player.state == PlayerState.LOST:
                feedback = (
                    f"💀 **{interaction.user.display_name}** は全ての推測を使い切りました。\n"
                    f"{result.to_display()}"
                )
            else:
                feedback = (
                    f"**{interaction.user.display_name}**: {result.to_display()}\n"
                    f"残り {remaining} 回"
                )

        await interaction.followup.send(feedback)

        # Check if game is over
        if game.phase == GamePhase.ENDED:
            await self._end_game(channel_id)

    # ------------------------------------------------------------------
    # Game flow helpers
    # ------------------------------------------------------------------

    async def start_game(
        self,
        channel_id: int,
        interaction: Optional[discord.Interaction] = None,
    ) -> None:
        """
        Transition from RECRUITING to PLAYING.
        Called either by the host's button press or the auto-start task.
        `interaction` is provided when force-started by button; None when auto-started.
        """
        game = self.active_games.get(channel_id)
        if game is None or game.phase != GamePhase.RECRUITING:
            return

        # Cancel the auto-start task if it's still running
        task = self._recruit_tasks.pop(channel_id, None)
        if task is not None and not task.done():
            task.cancel()

        # Start the game with a random word
        word = get_random_word()
        game.start(word)

        # Disable the recruitment buttons
        recruit_msg = self._recruit_messages.get(channel_id)
        if recruit_msg is not None:
            try:
                disabled_view = JoinView(cog=self, channel_id=channel_id)
                for item in disabled_view.children:
                    item.disabled = True  # type: ignore[attr-defined]
                await recruit_msg.edit(view=disabled_view)
            except discord.HTTPException:
                pass

        # Determine where to send the game embed
        channel = self.bot.get_channel(channel_id)
        if channel is None or not isinstance(channel, discord.abc.Messageable):
            return

        game_embed = build_game_embed(game)

        if interaction is not None:
            # Force-start via button; the interaction was already deferred
            game_msg = await interaction.followup.send(embed=game_embed, wait=True)
        else:
            game_msg = await channel.send(embed=game_embed)

        self._game_messages[channel_id] = game_msg

    async def _auto_start(self, channel_id: int) -> None:
        """Wait RECRUITMENT_TIMEOUT seconds, then start the game automatically."""
        try:
            await asyncio.sleep(RECRUITMENT_TIMEOUT)
        except asyncio.CancelledError:
            return

        game = self.active_games.get(channel_id)
        if game is None or game.phase != GamePhase.RECRUITING:
            return

        if not game.players:
            # No one joined; cancel the game
            channel = self.bot.get_channel(channel_id)
            if isinstance(channel, discord.abc.Messageable):
                await channel.send(
                    "参加者がいなかったため、ゲームをキャンセルしました。"
                )
            self._cleanup_game(channel_id)
            return

        await self.start_game(channel_id, interaction=None)

    async def _update_game_embed(self, channel_id: int) -> None:
        """Edit the game status message with the latest game state."""
        game = self.active_games.get(channel_id)
        game_msg = self._game_messages.get(channel_id)
        if game is None or game_msg is None:
            return

        embed = build_game_embed(game)
        try:
            await game_msg.edit(embed=embed)
        except discord.HTTPException as exc:
            log.warning("Failed to update game embed for channel %d: %s", channel_id, exc)

    async def _end_game(self, channel_id: int) -> None:
        """Send the end-game summary and clean up state."""
        game = self.active_games.get(channel_id)
        if game is None:
            return

        channel = self.bot.get_channel(channel_id)
        if isinstance(channel, discord.abc.Messageable):
            end_embed = build_end_embed(game)
            await channel.send(embed=end_embed)

        self._cleanup_game(channel_id)

    def _cleanup_game(self, channel_id: int) -> None:
        """Remove all state for a game."""
        self.active_games.pop(channel_id, None)
        self._game_messages.pop(channel_id, None)
        self._recruit_messages.pop(channel_id, None)
        task = self._recruit_tasks.pop(channel_id, None)
        if task is not None and not task.done():
            task.cancel()


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WordleCog(bot))
