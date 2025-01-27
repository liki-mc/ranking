import aiohttp
import asyncio

from discord import Interaction, Message
from discord.ext import commands, tasks

from bot.bot import Bot

import re

URL = "http://host.docker.internal:8000"
path = "/api/v1/ranking"

class RankingCog(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.channels : dict[int, list[tuple[str | None, int]]] = {}
        self.caffeines : dict[str, float] = {}

        # Safe update of channels
        self._lock = asyncio.Lock()
        self._active_operations = 0
        self.update_channels.start()

        self._caffeine_lock = asyncio.Lock()
        self.update_caffeines.start()
    
    async def load_channels(self):
        self.channels.clear()
        url = f"{URL}{path}/"
        async with self.bot.session.get(url) as resp:
            if resp.status != 200:
                return print(await resp.text())
            
            data = await resp.json()
            for ranking in data:
                if ranking["active"]:
                    self.channels.setdefault(ranking["channel"], []).append((ranking["token"], ranking["rid"]))
        
        self.bot.logger.info(self.channels)
    
    @tasks.loop(minutes = 10) 
    async def update_channels(self):
        async with self._lock:
            # wait until all active operations are done
            while self._active_operations:
                await asyncio.sleep(1)

            await self.load_channels()
    
    async def load_caffeines(self):
        self.caffeines.clear()
        url = f"{URL}/api/v1/ranking/caffeine/"
        async with self.bot.session.get(url) as resp:
            if resp.status != 200:
                return self.bot.logger.info(await resp.text())
            
            data = await resp.json()
            for caffeine in data:
                self.caffeines[caffeine["name"]] = caffeine["caffeine"]
        
        self.bot.logger.info(self.caffeines)
    
    @tasks.loop(minutes = 10)
    async def update_caffeines(self):
        async with self._caffeine_lock:
            await self.load_caffeines()
    
    @staticmethod
    def lock(func):
        async def wrapped(self : "RankingCog", *args, **kwargs):
            async with self._lock:
                self._active_operations += 1
            try:
                return await func(self, *args, **kwargs)
            finally:
                async with self._lock:
                    self._active_operations -= 1
        wrapped.__name__ = func.__name__
        return wrapped

    @commands.command()
    async def ping(self, ctx: commands.Context):
        return await ctx.send("pong")
    
    @commands.command()
    @lock
    async def create(self, ctx: commands.Context, name: str, token: str = None):
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
    
    @commands.command()
    @lock
    async def list(self, ctx: commands.Context, inactive: str = None):
        url = f"{URL}{path}/channel/{ctx.channel.id}/"
        async with self.bot.session.get(url) as resp:
            if resp.status != 200:
                self.bot.logger.error(f"failed to list ranking, reason: {await resp.text()}")
                return await ctx.send("Failed to list ranking")
            
            data = await resp.json()
            active_list = []
            inactive_list = []
            for ranking in data:
                if ranking["active"]:
                    active_list.append(f'{ranking["name"]} (#{ranking["rid"]})')
                else:
                    inactive_list.append(f'{ranking["name"]} (#{ranking["rid"]})')
            
            s = ""
            if active_list:
                s += f"## Current active ranking{'s' if len(active_list) > 1 else ''}:\n- " + "\n- ".join(f"{ranking}" for ranking in active_list) + "\n"
            if inactive_list and inactive == "all":
                s += f"## Current inactive ranking{'s' if len(inactive_list) > 1 else ''}:\n- " + "\n- ".join(f"{ranking}" for ranking in inactive_list)
            return await ctx.send(s)
    
    @commands.command()
    @lock
    async def deactivate(self, ctx: commands.Context, rid: str):
        try:
            rid = int(rid)
        except ValueError:
            return await ctx.send("Invalid ranking id")
        
        rankings = self.channels.get(ctx.channel.id)
        if rankings is None:
            return await ctx.send("No ranking in this channel")
        
        index = -1
        for i, (token, r) in enumerate(rankings):
            self.bot.logger.info(f"{i, token, r, rid}")
            if r == rid:
                index = i

        if index == -1:
            return await ctx.send("No ranking with that id in this channel")
        
        token, _ = rankings.pop(index)

        url = f"{URL}{path}/{rid}/deactivate/"
        async with self.bot.session.post(url) as resp:
            if resp.status != 200:
                self.bot.logger.error(f"failed to deactivate ranking, reason: {await resp.text()}")
                return await ctx.send("Failed to deactivate ranking")
            
            await ctx.send(f"Deactivated ranking #{rid}")
    
    @commands.command()
    @lock
    async def restart(self, ctx: commands.Context, rid: str):
        try:
            rid = int(rid)
        except ValueError:
            return await ctx.send("Invalid ranking id")
        
        rankings = self.channels.get(ctx.channel.id)
        if rankings is None:
            return await ctx.send("No ranking in this channel")
        
        index = -1
        for i, (token, r) in enumerate(rankings):
            self.bot.logger.info(f"{i, token, r, rid}")
            if r == rid:
                index = i

        if index == -1:
            return await ctx.send("No ranking with that id in this channel")
        
        token, _ = rankings.pop(index)

        url = f"{URL}{path}/{rid}/deactivate/"
        async with self.bot.session.post(url) as resp:
            if resp.status != 200:
                self.bot.logger.error(f"failed to deactivate ranking, reason: {await resp.text()}")
                return await ctx.send("Failed to restart ranking")
            
            ranking = await resp.json()
        
        url = f"{URL}{path}/"
        data = {
            "name": ranking["name"],
            "token": ranking["token"],
            "channel": ranking["channel"]
        }
        async with self.bot.session.post(url, json = data) as resp:
            if resp.status != 201:
                self.bot.logger.error(f"failed to create ranking, reason: {await resp.text()}")
                return await ctx.send("Failed to restart ranking")
            
            new_rid = (await resp.json())["rid"]
            self.channels.setdefault(ctx.channel.id, []).append((ranking["token"], new_rid))
            return await ctx.send(f"Restarted ranking #{rid} as #{new_rid}")
        
    @commands.command()
    @lock
    async def show(self, ctx: commands.Context, rid: str = None):
        if rid is not None:
            try:
                rids = [int(rid)]
            except ValueError:
                return await ctx.send("Invalid ranking id")
            
            url = f"{URL}{path}/{rids[0]}/"
            async with self.bot.session.get(url) as resp:
                if resp.status != 200:
                    self.bot.logger.error(f"failed to show ranking, reason: {await resp.text()}")
                    return await ctx.send("Failed to show ranking")
                
                ranking = await resp.json()
                if ranking["channel"] != ctx.channel.id:
                    return await ctx.send("No ranking with that id in this channel")
            
            rankings = [ranking]
        
        else:
            rankings = []
            failed = []
            async def get_ranking(rid):
                url = f"{URL}{path}/{rid}/"
                async with self.bot.session.get(url) as resp:
                    if resp.status != 200:
                        self.bot.logger.error(f"failed to show ranking, reason: {await resp.text()}")
                        failed.append(True)
                        return
                    
                    rankings.append(await resp.json())
            
            tasks = [get_ranking(r) for _, r in self.channels.get(ctx.channel.id, [])]
            await asyncio.gather(*tasks)
            if failed:
                return await ctx.send("Failed to show ranking(s)")

        
        if len(rankings) == 1:
            ranking = rankings[0]
            url = f"{URL}{path}/{ranking['rid']}/name_scores/"
            async with self.bot.session.get(url) as resp:
                if resp.status != 200:
                    self.bot.logger.error(f"failed to show ranking, reason: {await resp.text()}")
                    return await ctx.send("Failed to show ranking")
                
                data: list = await resp.json()
                data.sort(key = lambda x: x["score"], reverse = True)
                s = f"## {ranking['name']} (#{ranking['rid']})\n"
                for entry in data:
                    s += f"1. {entry['user']}: {entry['score']}\n"
                return await ctx.send(s)

    @commands.command()
    @lock
    async def reset(self, ctx: commands.Context, rid: str = None):
        if rid is not None:
            try:
                rids = [int(rid)]
            except ValueError:
                return await ctx.send("Invalid ranking id")
            
        else:
            rids = [r for _, r in self.channels.get(ctx.channel.id, [])]

        failed = []
        async def reset_ranking_for_user(rid, uid):
            url = f"{URL}{path}/{rid}/entries/user/{uid}/"
            async with self.bot.session.delete(url) as resp:
                self.bot.logger.info(f"resetting {uid} in {rid}")
                if resp.status != 204:
                    self.bot.logger.error(f"failed to reset ranking, reason: {await resp.text()}")
                    failed.append(rid)
                
                self.bot.logger.info(f"reset {uid} in {rid}")

        tasks = [reset_ranking_for_user(r, ctx.author.id) for r in rids]
        await asyncio.gather(*tasks)
        if failed:
            self.bot.logger.error(f"failed to reset ranking(s) {failed}")
            return await ctx.send("Possibly failed to reset ranking(s)")
        
        return await ctx.send("Reset ranking(s)")

    @commands.command()
    @lock
    async def set(self, ctx: commands.Context, number: str, uid: str = None, rid: str = None):
        if uid is None:
            try:
                number = float(number)
            except ValueError:
                return await ctx.send("Invalid number")
            uid = ctx.author.id
        
        else:
            try:
                uid, number = int(number), float(uid)
            except ValueError:
                return await ctx.send("Invalid number or user id")
        
        self.bot.logger.info(f"setting {uid} to {number}")
        if rid is None:
            rids = [r for _, r in self.channels.get(ctx.channel.id, [])]
        else:
            try:
                rids = [int(rid)]
            except ValueError:
                return await ctx.send("Invalid ranking id")
            
            if rids[0] not in [r for _, r in self.channels.get(ctx.channel.id, [])]:
                return await ctx.send("No ranking with that id in this channel")
        
        user = await self.bot.fetch_user(uid)
        for rid in rids:
            url = f"{URL}{path}/{rid}/entries/user/{uid}/score/"
            data = {
                "number": number,
                "username": user.name,
                "message_id": 0 # not from a message
            }
            async with self.bot.session.put(url, json = data) as resp:
                if resp.status != 200:
                    self.bot.logger.error(f"failed to set ranking, reason: {await resp.text()}")
                    return await ctx.send("Failed to set ranking")
            
            self.bot.logger.info(f"set {uid} to {number} in {rid}")
        
        return await ctx.send("Set ranking(s)")

    @commands.command()
    async def caffeine(self, ctx: commands.Context, action: str, *args: str):
        match action:
            case "add":
                if len(args) != 2:
                    return await ctx.send("Please provide a name and caffeine content")
                
                name, caffeine = args
                if name in self.caffeines:
                    return await ctx.send("Caffeine content already exists, user `caffeine update` to update")
                
                try:
                    caffeine = float(caffeine)
                except ValueError:
                    return await ctx.send("Invalid caffeine content")
                
                url = f"{URL}/api/v1/ranking/caffeine/"
                data = {
                    "name": name,
                    "caffeine": caffeine
                }
                async with self.bot.session.post(url, json = data) as resp:
                    if resp.status != 201:
                        self.bot.logger.error(f"failed to add caffeine content, reason: {await resp.text()}")
                        return await ctx.send("Failed to add caffeine content")
                
                self.caffeines[name] = caffeine
                return await ctx.send("Added caffeine content")

            case "update":
                if len(args) != 2:
                    return await ctx.send("Please provide a name and caffeine content")
                
                name, caffeine = args
                if name not in self.caffeines:
                    return await ctx.send("Caffeine content does not exist, use `caffeine add` to add")
                
                try:
                    caffeine = float(caffeine)
                except ValueError:
                    return await ctx.send("Invalid caffeine content")
                
                url = f"{URL}/api/v1/ranking/caffeine/{name}/"
                data = {
                    "caffeine": caffeine
                }
                async with self.bot.session.put(url, json = data) as resp:
                    if resp.status != 200:
                        self.bot.logger.error(f"failed to update caffeine content, reason: {await resp.text()}")
                        return await ctx.send("Failed to update caffeine content")
                
                self.caffeines[name] = caffeine
                return await ctx.send("Updated caffeine content")
            
            case "remove":
                if len(args) != 1:
                    return await ctx.send("Please provide a name")
                
                name = args[0]
                if name not in self.caffeines:
                    return await ctx.send("Caffeine content does not exist")
                
                url = f"{URL}/api/v1/ranking/caffeine/{name}/"
                async with self.bot.session.delete(url) as resp:
                    if resp.status != 204:
                        self.bot.logger.error(f"failed to remove caffeine content, reason: {await resp.text()}")
                        return await ctx.send("Failed to remove caffeine content")
                    
                self.caffeines.pop(name)
                return await ctx.send("Removed caffeine content")
            
            case "list":
                s = "## Caffeine content:\n"
                caffeines = [(name, caffeine) for name, caffeine in self.caffeines.items()]
                caffeines.sort(key = lambda x: x[1], reverse = True)
                for name, caffeine in caffeines:
                    s += f"- {name}: {caffeine}\n"
                return await ctx.send(s)
            
            case _:
                return await ctx.send("Invalid action")

    @commands.command()
    async def name(self, ctx: commands.Context, name: str = None):
        if name is None:
            name = ctx.author.display_name
            
        url = f"{URL}{path}/users/"
        data = {
            "name": name,
            "uid": ctx.author.id
        }
        async with self.bot.session.put(f"{url}{ctx.author.id}/", json = data) as resp:
            if resp.status == 201:
                if resp.status == 404:
                    async with self.bot.session.post(url, json = data) as resp:
                        if resp.status != 201:
                            self.bot.logger.error(f"failed to create user name, reason: {await resp.text()}")
                            return await ctx.send("Failed to create user name")
                        
                        return await ctx.send("Set user name")

                self.bot.logger.error(f"failed to update user name, reason: {await resp.text()}")
                return await ctx.send("Failed to update user name")
            
            return await ctx.send("Updated user name")

    @staticmethod
    def to_float(s: str) -> float:
        try:
            return float(s)
        except ValueError:
            return 0.0
        except TypeError:
            return 0.0

    @commands.Cog.listener("on_message")
    @lock
    async def ranking_listener(self, msg: Message):
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
                s = 0.0
                regex_string = f"(?:{re.escape(token)}) ?(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)" if token is not None else r"([+-]\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
                for match in re.finditer(regex_string, msg.content):
                    s += self.to_float(match.group(1))
                
                if s:
                    # add to database
                    url = f"{URL}{path}/{rid}/entries/"
                    data = {
                        "user": msg.author.id,
                        "number": s,
                        "message_id": msg.id,
                        "username": msg.author.name
                    }
                    self.bot.logger.info(f"posting {data} to {url}")
                    
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

    @commands.Cog.listener("on_message_edit")
    async def raking_edit_listener(self, before: Message, after: Message):
        """
        https://discordpy.readthedocs.io/en/stable/api.html#event-reference for a list of events
        """
        if before.author.bot:
            return
        
        rankings = self.channels.get(before.channel.id, [])
        if not rankings:
            return
        
        async with self._lock:
            self._active_operations += 1
        try:
            url = f"{URL}{path}/message/{before.id}/"
            async with self.bot.session.get(url) as resp:
                if resp.status != 200:
                    return self.bot.logger.error(f"failed to get entry on message edit, reason: {await resp.text()}")
                
                entries = await resp.json()
            
            for entry in entries:
                ranking = entry["ranking"]
                if (ranking["token"], ranking["rid"]) in rankings:
                    token = ranking["token"]
                    s = 0.0
                    regex_string = f"(?:{re.escape(token)}) ?(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)" if token is not None else r"([+-]\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
                    for match in re.finditer(regex_string, after.content):
                        s += self.to_float(match.group(1))
                    
                    if s != entry["number"]:
                        url = f"{URL}{path}/{ranking['rid']}/entries/{entry['id']}/"
                        data = {
                            "number": s
                        }
                        async with self.bot.session.put(url, json = data) as resp:
                            if resp.status != 200:
                                self.bot.logger.error(f"failed to update entry on message edit, reason: {await resp.text()}")
                                return

                        self.bot.logger.info(f"updated entry {entry['id']} to {s}")
                        
        finally:
            async with self._lock:
                self._active_operations -= 1
        
        asyncio.create_task(self.update_reactions(after))
    
    async def update_reactions(self, msg: Message):
        await msg.add_reaction("🔁")
        await asyncio.sleep(20)
        await msg.remove_reaction("🔁", self.bot.user)


async def setup(bot: Bot):
    cog = RankingCog(bot)
    bot.logger.info("Loaded example cog")
    await bot.add_cog(cog)
