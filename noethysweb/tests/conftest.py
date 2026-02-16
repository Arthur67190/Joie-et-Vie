import os

import pytest
from django.conf.global_settings import SESSION_COOKIE_NAME
from playwright.sync_api import Page

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for tests."""
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "locale": "fr-FR",
        "timezone_id": "Europe/Paris",
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Configure browser launch arguments."""
    return {
        **browser_type_launch_args,
        "headless": False,
    }

@pytest.fixture
def auto_login_user(db, client, live_server, page: Page):
    def make_auto_login(user):
        client.force_login(user)
        session_cookie = client.cookies[SESSION_COOKIE_NAME]

        page.context.add_cookies([{
            'name': SESSION_COOKIE_NAME,
            'value': session_cookie.value,
            'domain': live_server.url.split("//")[1].split(":")[0],
            'path': "/"
        }])

        return page

    return make_auto_login