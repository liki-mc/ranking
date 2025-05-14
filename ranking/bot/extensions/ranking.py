from asgiref.sync import sync_to_async as sta

from discord import Interaction, Message
from discord.ext import commands

from bot.bot import Bot

from website import models

def format_rankings(rankings: list[models.Ranking], users: dict[int, str], logger) -> str:
    """
    Format a list of rankings into a string
    """
    ranking_scores = {}
    for ranking in rankings:
        entries = models.Entry.objects.filter(
            ranking_id = ranking.id,
            user__in = users.keys()
        )
        scores = {user: {"score": 0, "last_updated": 0} for user in users.keys()}
        logger.info(f"{scores}")
        for entry in entries:
            scores[entry.user] = {
                "score": entry.number + scores[entry.user]["score"],
                "last_updated": max(entry.updated_at.timestamp(), scores[entry.user]["last_updated"])
            }
        logger.info("heyooosdqifjiqsjd")

        ranking_scores[ranking.id] = {
            "scores": scores,
            "ranking": ranking
        }
    
    s = ""
    if len(ranking_scores) == 1:
        ranking_id, ranking_info = list(ranking_scores.items())[0]
        ranking = ranking_info["ranking"]
        scores = ranking_info["scores"]
        # Sort the scores by score and last_updated
        sorted_scores = sorted(
            sorted(
                scores.items(),
                key = lambda x: x[1]["last_updated"],
            ),
            key = lambda x: x[1]["score"],
            reverse = not ranking.reverse_sort
        )

        
        s += f"## {ranking.name} (#{ranking.id})\n"
        logger.info(sorted_scores)
        for user_id, user_data in sorted_scores:
            s += f"1. {users[user_id]}: {user_data['score']}\n"
        
    else:
        users = {user_id: {"score": 0, "last_updated": 0, "name": user_name, "string": ""} for user_id, user_name in users.items()}
        for ranking_id, ranking_info in ranking_scores.items():
            for user_id, user in ranking_info["scores"].items():
                users[user_id]["score"] += user["score"]
                users[user_id]["last_updated"] = max(users[user_id]["last_updated"], user["last_updated"])
                users[user_id]["string"] += f"{ranking_info['ranking'].token}{user['score']}\n"
        
        # Sort the scores by score and last_updated
        sorted_scores = sorted(
            sorted(
                users.items(),
                key = lambda x: x[1]["last_updated"],
            ),
            key = lambda x: x[1]["score"],
            reverse = False
        )

        s += f"## Rankings\n"
        for entry in sorted_scores:
            s += f"1. {entry[1]['name']}: {entry[1]['string']} = {entry[1]['score']}\n"
    
    return s

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

    @commands.command()
    async def show(self, ctx: commands.Context, ranking_id: int = None):
        """
        ```
        Show the ranking(s) in the current channel

        Arguments:
        - ranking_id: The ID of the ranking to show (optional)
        ```
        """
        if ranking_id is None:
            ranking_ids = await sta(models.RankingChannel.objects.filter(
                channel_id = ctx.channel.id
            ).values_list)('ranking_id', flat = True)
            if not ranking_ids:
                await ctx.send("No rankings found in this channel")
                return
            ranking_id = ranking_ids[0]

        try:
            ranking : models.Ranking = await models.Ranking.objects.aget(id = ranking_id)
            if not ranking:
                await ctx.send(f"Ranking with ID {ranking_id} not found")
                return
            
            ranking_channel : models.RankingChannel = await models.RankingChannel.objects.aget(
                channel_id = ctx.channel.id,
                guild_id = ctx.guild.id,
                ranking_id = ranking.id
            )
            if not isinstance(ranking_channel, models.RankingChannel):
                await ctx.send(f"Ranking (#{ranking_id}) is not linked to this channel")
            
            else:
                users = {m.id: m.display_name for m in ctx.channel.members if not m.bot}
                self.bot.logger.info(f"{users}")
                formatted_string = await sta(format_rankings)([ranking], users, self.bot.logger)
                await ctx.send(formatted_string)
        
        except Exception as e:
            await ctx.send(f"Failed to show ranking")
            self.bot.logger.error(f"Failed to show ranking: {e}")

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
