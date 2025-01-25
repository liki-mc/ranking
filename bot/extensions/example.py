from discord import Interaction, Message
from discord.ext import commands

from bot.bot import Bot

import re

URL = "http://host.docker.internal:8000"
path = "/api/v1/ranking/"

class Example(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.channels : dict[int, list[tuple[str, int]]] = {}
    
    async def load_channels(self):
        url = f"{URL}{path}"
        async with self.bot.session.get(url) as resp:
            if resp.status != 200:
                return print(await resp.text())
            
            data = await resp.json()
            for ranking in data:
                self.channels.setdefault(ranking["channel"], []).append((ranking["character"], ranking["rid"]))
        
        self.bot.logger.info(self.channels)

    @commands.command()
    async def ping(self, ctx: commands.Context):
        return await ctx.send("pong")
    
    @commands.command()
    async def create(self, ctx: commands.Context, name: str, token: str):
        url = f"{URL}{path}"
        data = {
            "name": name,
            "character": token,
            "channel": ctx.channel.id
        }
        async with self.bot.session.post(url, json = data) as resp:
            if resp.status != 201:
                return await ctx.send("Failed to create ranking")
            
            rid = (await resp.json())["rid"]
            self.channels.setdefault(ctx.channel.id, []).append((token, rid))
            return await ctx.send("Created ranking")
        return await ctx.send("pong")
    
    @staticmethod
    def to_float(s: str) -> float:
        try:
            return float(s)
        except ValueError:
            return 0.0
        except TypeError:
            return 0.0

    @commands.Cog.listener("on_message")
    async def example_listener(self, msg: Message):
        """
        https://discordpy.readthedocs.io/en/stable/api.html#event-reference for a list of events
        """
        if msg.author.bot:
            return
        
        self.bot.logger.info(f"message from: {msg.author.name}")
        tokens = self.channels.get(msg.channel.id)
        if tokens is None:
            return
        
        self.bot.logger.info(f"tokens: {tokens}")
        try:
            for token, rid in tokens:
                s = 0
                for match in re.finditer(f"(?:{re.escape(token)}) ?(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)", msg.content):
                    self.bot.logger.info(f"found match: {match.group(1)}")
                    s += self.to_float(match.group(1))
                
                if s:
                    # add to database
                    url = f"{URL}{path}{rid}/entries/"
                    data = {
                        "user": msg.author.id,
                        "number": s,
                        "message_id": msg.id
                    }
                    self.bot.logger.info(f"posting to {url}")
                    async with self.bot.session.post(url, json = data) as resp:
                        if resp.status != 201:
                            self.bot.logger.error(f"failed to post to {url}, reason: {await resp.text()}")
                            self.bot.logger.info(f"reacting to {msg.id} 2151")
                            await msg.add_reaction("❌")
                            print(await resp.text())

                        else:
                            self.bot.logger.info(f"reacting to {msg.id}")
                            await msg.add_reaction("✅")

        except Exception as e:
            self.bot.logger.error(f"{e.__class__.__name__, e}")

async def setup(bot: Bot):
    cog = Example(bot)
    await cog.load_channels()
    bot.logger.info("Loaded example cog")
    await bot.add_cog(cog)
