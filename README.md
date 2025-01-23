# Discord bot template

See the [discord.py docs](https://discordpy.readthedocs.io/en/stable/) for more info

## Running

Make a file called `discord_token.txt` in the folder `secrets/` and paste your discord token into it.

Run `docker compose up --build` to start the bot.

## Managing dependencies

Create and activate a venv with `python -m venv venv` and `source venv/bin/activate`.

Install [poetry](https://python-poetry.org/docs/#installation)

Add dependencies with `poetry add <dep>` and make sure they're installed with `poetry install`

## Adding commands

Any file with a setup function for a Cog in the `bot/extensions/` folder will automatically be
added to the bot on startup
