from discord import Interaction, Message
from discord.ext import commands

from bot.bot import Bot

from website.models import *


class Ranking(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def cog_load(self):
        command = self.bot.get_command("create")
        if command:
            command.help = self.create.__doc__

    @commands.command(
        name = "create",
        
    )
    async def create(self, ctx: commands.Context, name: str, token: str = None):
        """
        *Create a ranking in the current channel*

        __Arguments__:
        - name:  The name of the ranking
        - token: The token of the ranking (optional)
        """
        if ctx.channel.id != 0:
            return await ctx.send("This command is disabled in this channel")
        
        url = f"{URL}{path}/"
        data = {
            "name": name,
            "token": token,
            "channel": ctx.channel.id
        }
        async with self.bot.session.post(url, json = data) as resp:
            if resp.status != 201:
                self.bot.logger.error(f"failed to create ranking, reason: {await resp.text()}")
                return await ctx.send("Failed to create ranking")
            
            rid = (await resp.json())["rid"]
            self.channels.setdefault(ctx.channel.id, []).append((token, rid))
            return await ctx.send("Created ranking")

    @commands.Cog.listener("on_message")
    async def example_listener(self, msg: Message):
        """
        https://discordpy.readthedocs.io/en/stable/api.html#event-reference for a list of events
        """

        if msg.author.bot:
            return

        if self.bot.user in msg.mentions:
            await msg.reply("hello")


async def setup(bot: Bot):
    await bot.add_cog(Ranking(bot))
