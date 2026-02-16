import pytest

from core.models import Organisateur


@pytest.mark.django_db
def test_create_organisateur(auto_login_user, admin_user, live_server):
    page = auto_login_user(admin_user)

    page.goto(f"{live_server.url}/utilisateur/parametrage/organisateur/ajouter")

    page.get_by_label("Nom").fill("Mouvement des Flambeaux et des Claires Flammes")
    page.get_by_role("button", name="Enregistrer").click()

    if Organisateur.objects.count() != 1:
        raise AssertionError("L'organisateur n'a pas été créé en base de données.")
    orga = Organisateur.objects.get(pk=1)
    if orga.nom != "Mouvement des Flambeaux et des Claires Flammes":
        raise AssertionError("Le nom de l'organisateur créé ne correspond pas.")

