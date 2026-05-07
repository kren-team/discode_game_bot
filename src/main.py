from __future__ import annotations

import asyncio
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


class WordleBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        await self.load_extension("src.cogs.wordle")
        log.info("Loaded cog: src.cogs.wordle")
        # Sync slash commands globally (may take up to 1 hour to propagate).
        # For faster testing in a single guild, replace with:
        #   await self.tree.sync(guild=discord.Object(id=YOUR_GUILD_ID))
        synced = await self.tree.sync()
        log.info("Synced %d slash command(s).", len(synced))

    async def on_ready(self) -> None:
        assert self.user is not None
        log.info("Logged in as %s (ID: %d)", self.user, self.user.id)
        await self.change_presence(
            activity=discord.Game(name="/wordle でゲームスタート！")
        )


async def main() -> None:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError(
            "DISCORD_TOKEN is not set. Copy .env.example to .env and fill in your token."
        )

    bot = WordleBot()
    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
