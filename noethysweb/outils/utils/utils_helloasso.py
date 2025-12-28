import requests
import logging
import logging, decimal, sys, datetime, re, copy, json
from core.models import TokenHA
from django.utils import timezone

logger = logging.getLogger(__name__)

class HelloAssoClient:
    TOKEN_URL_PROD = "https://api.helloasso.com/oauth2/token"
    TOKEN_URL_SANDBOX = "https://api.helloasso-sandbox.com/oauth2/token"
    CHECKOUT_URL_PROD_TEMPLATE = "https://api.helloasso.com/v5/organizations/{org}/checkout-intents"
    CHECKOUT_URL_SANDBOX_TEMPLATE = "https://api.helloasso-sandbox.com/v5/organizations/{org}/checkout-intents"

    def __init__(self, client_id, client_secret, organisation_slug, sandbox=False): #POUR LE DEV UNIQUEMENT !!!!!
        self.client_id = client_id
        self.client_secret = client_secret
        self.organisation_slug = organisation_slug
        self.sandbox = sandbox
        self.token = None
        if sandbox:
            self.CHECKOUT_URL_TEMPLATE = self.CHECKOUT_URL_SANDBOX_TEMPLATE
        else:
            self.CHECKOUT_URL_TEMPLATE = self.CHECKOUT_URL_PROD_TEMPLATE

    def get_cached_token(self):
        """
        Vérifie si un token existant est encore valide et le retourne.
        Sinon, récupère un nouveau token v ia l'API.
        """
        # Chercher le dernier token pour cette organisation
        token_entry = TokenHA.objects.filter(
            organisation_slug=self.organisation_slug,
            expires_at__gt=timezone.now()
        ).order_by('-expires_at').first()

        if token_entry:
            self.token = token_entry.access_token
            return self.token

        # Pas de token valide, récupérer un nouveau
        return self.get_token()

    def get_token(self):
        """Récupère le token OAuth2 (client_credentials)."""
        if self.token:
            return self.token

        url = self.TOKEN_URL_SANDBOX if self.sandbox else self.TOKEN_URL_PROD
        response = requests.post(url, data={
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        })
        response.raise_for_status()
        self.token = response.json()["access_token"]
        return self.token

    def create_checkout(self, total_amount, initial_amount, item_name, back_url, error_url, return_url,
                        contains_donation, reference=None):
        token = self.get_cached_token()
        url = self.CHECKOUT_URL_TEMPLATE.format(org=self.organisation_slug)
        payload = {
            "totalAmount": int(total_amount * 100),
            "initialAmount": int(initial_amount * 100),
            "itemName": item_name,
            "backUrl": back_url,
            "errorUrl": error_url,
            "returnUrl": return_url,
            "containsDonation": contains_donation,
            "reference": reference or "PAIEMENT_AUTO"
        }
        print("=== INIT PAYLOAD ===")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data
