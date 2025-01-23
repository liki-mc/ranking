import sys
from signal import SIGTERM
import asyncio
import logging

import bot
from bot.bot import Bot
from bot.constants import DISCORD_TOKEN


async def main():
    bot.instance = Bot()

    await bot.instance.load_extensions()

    await bot.instance.start(DISCORD_TOKEN)


async def close(task):
    await bot.instance.close()
    task.cancel()
    task.exception()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    bot_task = loop.create_task(main())

    loop.add_signal_handler(SIGTERM, lambda: loop.create_task(close(bot_task)))

    try:
        loop.run_until_complete(bot_task)
    except KeyboardInterrupt as interrupt:
        loop.run_until_complete(close(bot_task))
        loop.run_forever()
    except Exception as err:
        print(err, file=sys.stderr)
    finally:
        loop.close()
        sys.exit(69)
