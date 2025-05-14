# Ranking site and discord bot

See the [discord.py docs](https://discordpy.readthedocs.io/en/stable/) for more info.

See the [django docs](https://docs.djangoproject.com/en/5.2/) for more info.

## Running

Set up the psql database.

Create a .env file, an example is provided as `example.env`.

Run `docker compose up --build` to start the bot.

## Managing dependencies

Create and activate a venv with `python -m venv venv` and `source venv/bin/activate`.

Install [poetry](https://python-poetry.org/docs/#installation)

Add dependencies with `poetry add <dep>` and make sure they're installed with `poetry install`

## Project structure and commands

The project follows the standard Django structure with apps for modular functionality, including a `ranking` app for core features. The `ranking/bot` folder contains the bot logic and extensions for Discord integration.

Any file with a setup function for a Cog in the `ranking/bot/extensions/` folder will automatically be added to the bot on startup.
