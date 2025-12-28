# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

import logging
logger = logging.getLogger(__name__)
from portail.views.base import CustomView
from django.views.generic import TemplateView
from django.utils.translation import gettext as _
from django.utils import timezone
from core.models import TokenHA, Prestation, HelloAssoConfig, ModeReglement, CompteBancaire, Reglement, Ventilation, ComptaOperation
import requests
import logging
from django.shortcuts import redirect


logger = logging.getLogger(__name__)

def verifier_paiement_prestation(prestation_id=None, checkout_intent_id=None):
    """
    Vérifie l'état du paiement pour une prestation ou un checkout_intent_id via HelloAsso.
    """
    # 1️⃣ Récupérer le TokenHA valide
    token_qs = TokenHA.objects.filter(
        expires_at__gt=timezone.now()
    )

    if prestation_id:
        token_qs = token_qs.filter(prestation__idprestation=prestation_id)
    elif checkout_intent_id:
        token_qs = token_qs.filter(checkout_intent_id=checkout_intent_id)
    else:
        logger.error("Il faut soit prestation_id soit checkout_intent_id")
        return None

    token_entry = token_qs.order_by('-expires_at').first()
    if not token_entry:
        logger.error("Aucun token valide trouvé dans TokenHA pour ce paiement")
        return None

    token = token_entry.access_token
    org_slug = token_entry.organisation_slug
    checkout_id = checkout_intent_id or token_entry.checkout_intent_id
    if not checkout_id:
        logger.error("Pas de checkout_intent_id disponible pour ce paiement")
        return None

    # 2️⃣ Appel à l'API HelloAsso
    url = f"https://api.helloasso.com/v5/organizations/{org_slug}/checkout-intents/{checkout_id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Erreur API HelloAsso: {e}")
        return None

    data = resp.json()
    # 3️⃣ Retourner les infos utiles, par ex. le state
    return {
        "state": data.get("state"),
        "checkout_id": checkout_id,
        "amount": data.get("totalAmount"),
        "order_id": data.get("orderId"),
        "reference": data.get("reference")
    }


from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
import requests
from core.models import TokenHA, Reglement, Ventilation, CompteBancaire, HelloAssoConfig

class View(CustomView, TemplateView):
    menu_code = "portail_attente_paiement"
    template_name = "portail/attente_paiement.html"
    compatible_demo = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_titre'] = "Attente du paiement"
        context['box_titre'] = "Paiement en cours"
        context['box_introduction'] = ""

        # On passe checkoutIntentId et orderId au template
        context['checkout_intent_id'] = self.request.GET.get("checkoutIntentId")
        context['order_id'] = self.request.GET.get("orderId")
        return context

    def get(self, request, *args, **kwargs):
        checkout_intent_id = request.GET.get("checkoutIntentId")
        orderId = request.GET.get("orderId")
        if not checkout_intent_id:
            messages.error(request, "Aucun checkoutIntentId fourni.")
            return redirect('portail_facturation')

        # 1️⃣ Récupérer le TokenHA pour ce checkout
        token_entry = TokenHA.objects.filter(
            checkout_intent_id=checkout_intent_id,
            expires_at__gt=timezone.now()
        ).order_by('-expires_at').first()

        if not token_entry:
            messages.error(request, "Token non trouvé ou expiré")
            return redirect('portail_facturation')

        prestation = token_entry.prestation
        token = token_entry.access_token
        org_slug = token_entry.organisation_slug

        # ⚠️ DEV ONLY — passer à False en production
        HELLOASSO_FORCE_SANDBOX = True
        api_base = "https://api.helloasso-sandbox.com/v5/organizations" if HELLOASSO_FORCE_SANDBOX else "https://api.helloasso.com/v5/organizations"

        # 2️⃣ Vérifier le paiement via HelloAsso
        url = f"{api_base}/{org_slug}/checkout-intents/{checkout_intent_id}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            messages.error(request, f"Erreur API HelloAsso: {e}")
            return redirect('portail_facturation')

        order = data.get("order")
        if not order:
            messages.info(request, "Paiement en attente...")
            return redirect('portail_facturation')

        # 3️⃣ Paiement validé → créer règlement et ventilation
        paiement_info = {
            "state": "PAID",
            "amount": order.get("amount", {}).get("total"),
            "order_id": order.get("id"),
            "reference": order.get("reference"),
        }

        # 4️⃣ Récupérer l'activité et le compte bancaire
        config = HelloAssoConfig.objects.get(org_slug=org_slug)
        activite = config.activites.first()
        compte = CompteBancaire.objects.filter(structure=activite.structure).first()
        if not compte:
            compte = CompteBancaire.objects.filter(pk=1).first()  # compte par défaut

        # 5️⃣ Création du règlement et ventilation
        reglement = Reglement.objects.create(
            famille=prestation.famille,
            date=timezone.now(),
            montant=paiement_info['amount']/100,
            compte=compte,
            modelimp_id=2,
            mode_id=6,
            payeur_id=3,  # par défaut
        )
        Ventilation.objects.create(
            famille=prestation.famille,
            reglement=reglement,
            prestation=prestation,
            montant=paiement_info['amount']/100,
        )


        libelle = f"Prestation : {prestation.label} Famille : {prestation.famille.nom}"

        ComptaOperation.objects.create(
            type="credit",
            date=timezone.now(),
            libelle=libelle,
            montant=paiement_info['amount']/100,
            compte=compte,
            mode_id=6,
            regul_avance=False,
            remb_avance=False,
            num_piece=orderId,
        )


        messages.success(request, "Paiement validé ! Merci pour votre règlement.")
        return redirect('portail_facturation')
