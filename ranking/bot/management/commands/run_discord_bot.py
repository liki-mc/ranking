# myapp/management/commands/run_discord_bot.py
from django.core.management.base import BaseCommand
from run_bot import main

class Command(BaseCommand):
    help = 'Run the Discord bot'

    def handle(self, *args, **kwargs):
        main()