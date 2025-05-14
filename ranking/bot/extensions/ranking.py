from asgiref.sync import sync_to_async as sta

from discord import Interaction, Message
from discord.ext import commands

from bot.bot import Bot

from website import models


class Ranking(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def cog_load(self):
        command = self.bot.get_command("create")
        if command:
            command.help = self.create.__doc__

    @commands.command()
    async def create(self, ctx: commands.Context, name: str = None, token: str = None):
        """
        ```
        Create a ranking in the current channel

        Arguments:
        - name:  The name of the ranking
        - token: The token of the ranking (optional)
        ```
        """
        if not name:
            await ctx.send("Please provide a name for the ranking")
            return

        try:
            ranking : models.Ranking = await sta(models.Ranking.objects.create)(
                name = name,
                token = token,
                description = "",
                active = True,
                reverse_sort = False
            )
            if not isinstance(ranking, models.Ranking):
                await ctx.send("Failed to create ranking")
            
            else:
                ranking_channel : models.RankingChannel = await sta(models.RankingChannel.objects.create)(
                    ranking = ranking,
                    channel_id = ctx.channel.id,
                    guild_id = ctx.guild.id
                )
                if not isinstance(ranking_channel, models.RankingChannel):
                    await ctx.send(f"Failed to link ranking (#{ranking.id}) to channel")
                
                else:
                    await ctx.send(f"Created ranking {ranking.name} (#{ranking.id}) with {'no token' if not ranking.token else f'token {ranking.token}'}")
            
        
        except Exception as e:
            await ctx.send(f"Failed to create ranking")
            self.bot.logger.error(f"Failed to create ranking: {e}")

        


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
