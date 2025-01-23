import asyncio
from contextlib import suppress
import logging

import discord
from discord.ext import commands


logger = logging.getLogger("bot")


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        intents = discord.Intents.default()
        intents.message_content = True

        self.logger = logger

        super().__init__(command_prefix="$", *args, intents=intents, **kwargs)

    async def load_extensions(self) -> None:
        from bot.extensions import EXTENSIONS

        for ext in EXTENSIONS:
            await self.load_extension(ext)
            self.logger.info(f"loaded extension '{ext}'")

    async def close(self) -> None:
        extension_tasks = []
        for ext in list(self.extensions):
            with suppress(Exception):
                extension_tasks.append(self.unload_extension(ext))

        await asyncio.gather(*extension_tasks)

        return await super().close()

    async def on_error(self, event_method, /, *args, **kwargs):
        self.logger.error(event_method)

    async def on_command_error(self, context, exception):
        self.logger.error(f"{context}\n{exception}")
