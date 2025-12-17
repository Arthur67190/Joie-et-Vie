from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Backup the database"

    def handle(self, *args, **kwargs):
        from outils.utils import utils_update
        resultat = utils_update.backup_database()
        print("Backup result:", resultat)