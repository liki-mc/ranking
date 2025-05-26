from asgiref.sync import sync_to_async as sta
import asyncio
import re

from discord import Interaction, Message
from discord.ext import commands

from bot.bot import Bot

from website import models

from django.db import close_old_connections

import traceback

def format_rankings(rankings: list[models.Ranking], users: dict[int, str]) -> str:
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
        for entry in entries:
            scores[entry.user] = {
                "score": entry.number + scores[entry.user]["score"],
                "last_updated": max(entry.updated_at.timestamp(), scores[entry.user]["last_updated"])
            }

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
        for user_id, user_data in sorted_scores:
            score = round(user_data["score"], 2)
            if score != 0 or not users[user_id][1]:
                s += f"1. {users[user_id][0]}: {round(user_data['score'], 2)}\n"
        
    else:
        users = {user_id: {"score": 0, "last_updated": 0, "name": user_info[0], "string": "", "bot": user_info[1]} for user_id, user_info in users.items()}
        for ranking_id, ranking_info in ranking_scores.items():
            for user_id, user in ranking_info["scores"].items():
                users[user_id]["score"] += user["score"]
                users[user_id]["last_updated"] = max(users[user_id]["last_updated"], user["last_updated"])
                display_token = ranking_info["ranking"].token if ranking_info["ranking"].token is not None else ('+' if user['score'] >= 0 else '')
                users[user_id]["string"] += f" {display_token}{round(user['score'], 1)}"
        
        # Sort the scores by score and last_updated
        sorted_scores = sorted(
            sorted(
                users.items(),
                key = lambda x: x[1]["last_updated"],
            ),
            key = lambda x: x[1]["score"],
            reverse = True
        )

        s += f"## Rankings\n"
        for entry in sorted_scores:
            if entry[1]["score"] != 0 or not entry[1]["bot"]:
                s += f"1. {entry[1]['name']}: {entry[1]['string']} = {round(entry[1]['score'], 1)}\n"
    
    return s

def to_float(number: str) -> float:
    """
    Convert a string to a float
    """
    try:
        return float(number.replace(",", "."))
    except ValueError:
        return 0.0
    except TypeError:
        return 0.0

def parse_message(message: str, token: str = None, mappings: dict[str, float] = {}) -> tuple[float, str]:
    s = 0.0
    matches = False
    regex_string = f"(?:{re.escape(token)}) ?(\d+(?:(?:\.|,)\d+)?(?:[eE][+-]?\d+)?)" if token is not None else r"([+-] ?\d+(?:(?:\.|,)\d+)?(?:[eE][+-]?\d+)?)"
    if mappings:
        regex_string += f" ?((?:{')|(?:'.join([re.escape(k) for k in mappings.keys()])}))?"

    for match in re.finditer(regex_string, message):
        matches = True
        multiplier = 1.0 if (len(match.groups()) < 2) else mappings.get(match.group(2), 1)
        s += to_float(match.group(1)) * multiplier
    
    return s if matches else None

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
        await sta(close_old_connections)()
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
            await ranking.asave()
            if not isinstance(ranking, models.Ranking):
                await ctx.send("Failed to create ranking")
            
            else:
                ranking_channel : models.RankingChannel = await models.RankingChannel.objects.acreate(
                    ranking = ranking,
                    channel_id = ctx.channel.id,
                    guild_id = ctx.guild.id
                )
                await ranking_channel.asave()
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
        await sta(close_old_connections)()
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
        await sta(close_old_connections)()
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
            await ranking_channel.asave()
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
        await sta(close_old_connections)()
        rankings = []
        if ranking_id is None:
            ranking_channels = await sta(models.RankingChannel.objects.filter)(
                channel_id = ctx.channel.id
            )
            async for ranking_channel in ranking_channels:
                rankings.append(
                    await models.Ranking.objects.aget(id = ranking_channel.ranking_id)
                )
        
        else:
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
                return
            
            rankings.append(ranking)

        try:
            users = {m.id: (m.display_name, m.bot) for m in ctx.channel.members}
            formatted_string = await sta(format_rankings)(rankings, users)
            await ctx.send(formatted_string)
        
        except Exception as e:
            await ctx.send(f"Failed to show ranking")
            self.bot.logger.error(f"Failed to show ranking: {e}")

    @commands.command()
    async def add(self, ctx: commands.Context, string: str = None, value: float = None, ranking_id: int = None):
        """
        ```
        Add a mapping to a ranking

        Arguments:
        - string: The string to map
        - value: The value to map the string to
        - ranking_id: The ID of the ranking to add the mapping to (optional)
        ```
        """
        await sta(close_old_connections)()
        if not string or not value:
            await ctx.send("Please provide a string and value")
            return
        
        
        try:
            ranking_ids = [ranking_id]
            if ranking_id is None:
                ranking_ids = []
                ranking_channels = await sta(models.RankingChannel.objects.filter)(
                    channel_id = ctx.channel.id
                )
                async for ranking_channel in ranking_channels:
                    ranking_ids.append(ranking_channel.ranking_id)

            for ranking_id in ranking_ids:
                ranking : models.Ranking = await models.Ranking.objects.aget(id = ranking_id)
                if not isinstance(ranking, models.Ranking):
                    await ctx.send(f"Failed to get ranking (#{ranking_id})")
                    return
                
                mapping : models.Mapping = await models.Mapping.objects.acreate(
                    ranking = ranking,
                    string = string,
                    value = value
                )
                await mapping.asave()
                if not isinstance(mapping, models.Mapping):
                    await ctx.send(f"Failed to add mapping")
                
                else:
                    await ctx.send(f"Added mapping {mapping.string} ({mapping.value}) to ranking {mapping.ranking.name} (#{mapping.ranking.id})")
        
        except Exception as e:
            await ctx.send(f"Failed to add mapping")
            self.bot.logger.error(f"Failed to add mapping: {e}")

    @commands.Cog.listener("on_message")
    async def ranking_listener(self, message: Message):
        """
        https://discordpy.readthedocs.io/en/stable/api.html#event-reference for a list of events
        """
        await sta(close_old_connections)()
        if message.author.bot and message.author.id == self.bot.user.id:
            return
        
        if "http" in message.content:
            return
        
        try:
            ranking_channels = await sta(models.RankingChannel.objects.filter)(
                channel_id = message.channel.id
            )
            async for ranking_channel in ranking_channels:
                matches = False
                ranking = await models.Ranking.objects.aget(id = ranking_channel.ranking_id)
                if ranking.active:
                    mappings = await sta(models.Mapping.objects.filter)(
                        ranking_id = ranking.id
                    )
                    mapping_dict = {}
                    async for mapping in mappings:
                        mapping_dict[mapping.string] = mapping.value

                    s = parse_message(message.content, ranking.token, mapping_dict)
                    
                    if s is not None:
                        matches = True
                        entry : models.Entry = await models.Entry.objects.acreate(
                            ranking = ranking,
                            number = s,
                            user = message.author.id,
                            message_id = message.id
                        )
                        await entry.asave()
                        if not isinstance(entry, models.Entry):
                            await message.add_reaction("❌")
                            self.bot.logger.error(f"Failed to create entry for {message.author.name} in {ranking.name}")
                
                if matches:
                    await message.add_reaction("✅")
        
        except Exception as e:
            self.bot.logger.error(f"Failed to parse message: {e}")
            # await message.add_reaction("❓")
            self.bot.logger.error(f"{traceback.format_exc()}")
            return

    @commands.Cog.listener("on_message_edit")
    async def ranking_edit_listener(self, before: Message, message: Message):
        """
        https://discordpy.readthedocs.io/en/stable/api.html#event-reference for a list of events
        """
        await sta(close_old_connections)()
        if message.author.bot and message.author.id == self.bot.user.id:
            return

        if "http" in message.content:
            return
        
        try:
            message_entries = await sta(models.Entry.objects.filter)(
                message_id = before.id
            )
            if await message_entries.acount() == 0:
                return

            async for entry in message_entries:
                ranking = await models.Ranking.objects.aget(id = entry.ranking_id)
                if ranking.active:
                    s = parse_message(message.content, ranking.token)
                    
                    if s is not None:
                        entry.number = s
                        entry.message_id = message.id
                        await entry.asave()
            
            asyncio.create_task(self.update_reactions(message))
        
        except Exception as e:
            self.bot.logger.error(f"Failed to parse message: {e}")
            # await message.add_reaction("❓")
            self.bot.logger.error(f"{traceback.format_exc()}")
            return
    
    async def update_reactions(self, message: Message):
        await message.add_reaction("🔁")
        await asyncio.sleep(20)
        await message.remove_reaction("🔁", self.bot.user)

async def setup(bot: Bot):
    await bot.add_cog(Ranking(bot))
