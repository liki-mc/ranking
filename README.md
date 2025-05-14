# Discord bot template

See the [discord.py docs](https://discordpy.readthedocs.io/en/stable/) for more info

## Running

Create a .env file:
```
DISCORD_TOKEN=
POSTGRES_PASSWORD=
```

Run `docker compose up --build` to start the bot.

## Managing dependencies

Create and activate a venv with `python -m venv venv` and `source venv/bin/activate`.

Install [poetry](https://python-poetry.org/docs/#installation)

Add dependencies with `poetry add <dep>` and make sure they're installed with `poetry install`

## Adding commands

The project follows the standard Django structure with apps for modular functionality, including a `ranking` app for core features. The `ranking/bot` folder contains the bot logic and extensions for Discord integration.

Any file with a setup function for a Cog in the `ranking/bot/extensions/` folder will automatically be added to the bot on startup.
