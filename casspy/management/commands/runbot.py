from django.core.management.base import BaseCommand
from casspy import cassoundra


class Command(BaseCommand):
    help = 'Runs the Discord bot with database access'

    def handle(self, *args, **options):
        cassoundra.main()
