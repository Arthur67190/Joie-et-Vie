import pytest
from playwright.sync_api import expect
from core.models import AdresseMail


@pytest.mark.django_db
class TestStructure:
    def test_empty_structure_list(self, auto_login_user, admin_user, live_server):
        page = auto_login_user(admin_user)

        page.goto(f"{live_server.url}/utilisateur/parametrage/structures/liste")

        expect(page.get_by_role("cell", name="Aucune donnée")).to_be_visible()

    def test_create_structure(self, auto_login_user, admin_user, live_server):
        page = auto_login_user(admin_user)

        AdresseMail.objects.create(adresse="test@test.org")

        page.goto(f"{live_server.url}/utilisateur/parametrage/structures/ajouter")

        page.get_by_role("textbox", name="Nom*").fill("Test")
        page.get_by_label("Adresse d'expédition*").select_option("1")
        page.get_by_title("Enregistrer", exact=True).click()

        expect(page).to_have_url(f"{live_server.url}/utilisateur/parametrage/structures/liste")
        expect(page.get_by_role("cell", name="Test")).to_be_visible()