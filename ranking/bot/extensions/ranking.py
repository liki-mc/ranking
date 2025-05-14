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
            ranking : models.Ranking = await models.Ranking.objects.acreate(
                name = name,
                token = token,
                description = "",
                active = True,
                reverse_sort = False
            )
            if not isinstance(ranking, models.Ranking):
                await ctx.send("Failed to create ranking")
            
            else:
                ranking_channel : models.RankingChannel = await models.RankingChannel.objects.acreate(
                    ranking = ranking,
                    channel_id = ctx.channel.id,
                    guild_id = ctx.guild.id
                )
                if not isinstance(ranking_channel, models.RankingChannel):
                    await ctx.send(f"Failed to link ranking (#{ranking.id}) to channel")
                
                else:
                    await ctx.send(f"Created ranking {ranking.name} (#{ranking.id}) with {'default +/- tokens' if not ranking.token else f'token {ranking.token}'}")
        
        except Exception as e:
            await ctx.send(f"Failed to create ranking")
            self.bot.logger.error(f"Failed to create ranking: {e}")

    @commands.command()
    async def list(self, ctx: commands.Context, inactive: str = None):
        """
        ```
        List all rankings in the current channel

        Arguments:
        - inactive: If set to "all", list all rankings, including inactive ones
        ```
        """
        try:
            rankings = []
            ranking_channels = models.RankingChannel.objects.filter(channel_id = ctx.channel.id)
            async for ranking_channel in ranking_channels:
                ranking = await models.Ranking.objects.aget(id = ranking_channel.ranking_id)
                if ranking.active or inactive == "all":
                    rankings.append(
                        f"- {ranking.name} (#{ranking.id})"
                    )

            if len(rankings) == 0:
                await ctx.send("No rankings found in this channel")
            
            else:
                await ctx.send(f"## Current ranking{'s' if len(ranking_channels) > 1 else ''}\n" + "\n".join(rankings))
        
        except Exception as e:
            await ctx.send(f"Failed to list rankings")
            self.bot.logger.error(f"Failed to list rankings: {e}")
        
    @commands.command()
    async def link(self, ctx: commands.Context, ranking_id: int = None):
        """
        ```
        Link a ranking to the current channel

        Arguments:
        - ranking_id: The ID of the ranking to link
        ```
        """
        if not ranking_id:
            await ctx.send("Please provide a ranking ID")
            return

        try:
            ranking : models.Ranking = await models.Ranking.objects.aget(id = ranking_id)
            if not ranking:
                await ctx.send(f"Ranking with ID {ranking_id} not found")
                return
            
            ranking_channel : models.RankingChannel = await models.RankingChannel.objects.acreate(
                ranking = ranking,
                channel_id = ctx.channel.id,
                guild_id = ctx.guild.id
            )
            if not isinstance(ranking_channel, models.RankingChannel):
                await ctx.send(f"Failed to link ranking (#{ranking_id}) to channel")
            
            else:
                await ctx.send(f"Linked ranking {ranking_channel.ranking.name} (#{ranking_channel.ranking.id}) to channel")
        
        except Exception as e:
            await ctx.send(f"Failed to link ranking")
            self.bot.logger.error(f"Failed to link ranking: {e}")

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
