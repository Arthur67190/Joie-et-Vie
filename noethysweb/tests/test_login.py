import pytest
from playwright.sync_api import Page, expect

@pytest.mark.django_db
def test_user_login_with_fixture(page: Page, live_server, django_user_model):
    user = django_user_model.objects.create_user(username="user", password="userpass")

    page.goto(f"{live_server.url}/connexion")

    # Use the user from the fixture
    page.get_by_role("textbox", name="Identifiant").fill(user.username)
    page.get_by_role("textbox", name="Mot de passe").fill("userpass")
    page.get_by_role("button", name="Se connecter").click()

    # Should be logged in
    expect(page).to_have_url(f"{live_server.url}/utilisateur/")