from discord import app_commands, Interaction, Message
from discord.ext.commands import Cog

from bot.bot import Bot


class Example(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @app_commands.command(name="example")
    async def example(self, ia: Interaction):
        return await ia.response.send_message("example command")

    @Cog.listener("on_message")
    async def example_listener(self, msg: Message):
        """
        https://discordpy.readthedocs.io/en/stable/api.html#event-reference for a list of events
        """

        if msg.author.bot:
            return

        if self.bot.user in msg.mentions:
            await msg.reply("hello")


async def setup(bot: Bot):
    await bot.add_cog(Example(bot))
