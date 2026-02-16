import pytest
from playwright.sync_api import expect
from core.models import AdresseMail


@pytest.mark.django_db
class TestAdressesMail:
    def test_empty_adresse_mail_list(self, auto_login_user, admin_user, live_server):
        page = auto_login_user(admin_user)

        page.goto(f"{live_server.url}/utilisateur/parametrage/adresses_mail/liste")

        expect(page.get_by_role("cell", name="Aucune donnée")).to_be_visible()

    def test_create_adresse_mail(self, auto_login_user, admin_user, live_server):
        page = auto_login_user(admin_user)

        page.goto(f"{live_server.url}/utilisateur/parametrage/adresses_mail/ajouter ")

        page.get_by_label("Moteur*").select_option("console")

        page.get_by_role("textbox", name="Adresse d'envoi*").fill("test@test.flambeaux.org")

        page.get_by_title("Enregistrer", exact=True).click()

        expect(page.get_by_role("cell", name="test@test.flambeaux.org")).to_be_visible()

    def test_modify_adresse_mail(self, auto_login_user, admin_user, live_server):
        page = auto_login_user(admin_user)

        AdresseMail.objects.create(moteur="console", adresse="test@test.flambeaux.org")

        new_email = "test@flambeaux.org"

        page.goto(f"{live_server.url}/utilisateur/parametrage/adresses_mail/liste")

        page.get_by_title("Modifier").click()
        page.get_by_role("textbox", name="Adresse d'envoi*").click()

        page.get_by_role("textbox", name="Adresse d'envoi*").fill(new_email)

        page.get_by_title("Enregistrer", exact=True).click()

        expect(page.get_by_role("cell", name=new_email)).to_be_visible()

    def test_delete_adresse_mail(self, auto_login_user, admin_user, live_server):
        page = auto_login_user(admin_user)

        addresse = AdresseMail.objects.create(moteur="console", adresse="test@flambeaux.org")

        page.goto(f"{live_server.url}/utilisateur/parametrage/adresses_mail/liste")
        page.locator(f"[id=\"{addresse.idadresse}\"]").get_by_title("Supprimer").click()
        page.get_by_role("button", name="Supprimer").click()

        expect(page.get_by_role("cell", name="test@flambeaux.org")).not_to_be_visible()

    def test_duplicate_adresse_mail(self, auto_login_user, admin_user, live_server):
        page = auto_login_user(admin_user)

        AdresseMail.objects.create(moteur="console", adresse="test@flambeaux.org")
        page.goto(f"{live_server.url}/utilisateur/parametrage/adresses_mail/liste")
        page.get_by_title("Dupliquer").click()
        page.get_by_role("button", name="dupliquer", exact=True).click()
        expect(page.get_by_role("cell", name="Copie de test@flambeaux.org")).to_be_visible()
