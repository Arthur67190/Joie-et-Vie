from django.db import migrations

def copy_structures_to_admin(apps, schema_editor):
    Utilisateur = apps.get_model('core', 'Utilisateur')
    for user in Utilisateur.objects.all():
        user.structures_admin.set(user.structures.all())

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0211_auto_20251210_2256'),
    ]

    operations = [
        migrations.RunPython(copy_structures_to_admin),
    ]
