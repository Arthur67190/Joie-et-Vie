# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

import logging, decimal, sys, datetime, re, copy, json
logger = logging.getLogger(__name__)
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.db.models import Sum, Q
from django.contrib import messages
from eopayment import Payment
from portail.views.base import CustomView
from core.models import Activite, Facture, Prestation, Ventilation, PortailPeriode, Paiement, Reglement, Payeur, TokenHA, ModeReglement, CompteBancaire, PortailRenseignement, ModeleImpression, Mandat
from core.utils import utils_portail, utils_fichiers, utils_dates, utils_texte
from django.core.serializers import serialize
from django.views.decorators.http import require_POST
from datetime import date
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
import decimal
from django.db.models import Sum, F, DecimalField, ExpressionWrapper

from django.utils import timezone

from django.core.cache import cache
import time
import requests
import base64

from django.views.decorators.http import require_POST
from django.http import JsonResponse
from core.models import Prestation, HelloAssoConfig
from outils.utils.utils_helloasso import HelloAssoClient

@require_POST
def paiement_tpe(request):
    id_prestation = request.POST.get("id_prestation")
    montant = float(request.POST.get("montant"))

    try:
        prestation = Prestation.objects.get(pk=id_prestation)
        activite = prestation.activite
        plateforme = activite.pay_org_tpe
    except Prestation.DoesNotExist:
        return JsonResponse({"success": False, "erreur": "Prestation non trouvée"}, status=404)

    print("=== INIT PAIEMENT PRESTATION ===")

    if plateforme == "HELLOASSO":
        back_url = request.build_absolute_uri("/paiement/cancel/")
        error_url = request.build_absolute_uri("/paiement/error/")
        return_url = request.build_absolute_uri("/paiement/retour/")
        item_name = f"Paiement Prestation {prestation.idprestation}"[:250]  # max 250 caractères
        contains_donation = False

        # HelloAsso : on crée le checkout et renvoie l'URL
        config = HelloAssoConfig.objects.filter(activites=activite, actif=True).first()
        if not config:
            return JsonResponse({"success": False, "erreur": "Aucune configuration HelloAsso trouvée"}, status=400)

        client = HelloAssoClient(config.client_id, config.client_secret, organisation_slug=config.org_slug, sandbox=False) #CHANGER EN PROD
        try:
            url_checkout = client.create_checkout(
                total_amount=montant,
                initial_amount=montant,
                item_name=f"Paiement prestation {prestation.idprestation}",
                back_url="https://sacadoc.flambeaux.org/attente_paiement/",
                error_url="https://sacadoc.flambeaux.org/attente_paiement/",
                return_url="https://sacadoc.flambeaux.org/attente_paiement/",
                contains_donation=False,
                reference=f"PRESTA_{prestation.idprestation}"
            )

            checkout_intent_id = url_checkout.get("id")
            TokenHA.objects.create(
                prestation=prestation,
                checkout_intent_id=checkout_intent_id,
                organisation_slug=client.organisation_slug,
                access_token=client.token,
                expires_at=timezone.now() + timezone.timedelta(seconds=1500)
            )
        except Exception as e:
            print("DEBUG: Erreur lors de l'appel à create_checkout:", e)
            return JsonResponse({"success": False, "erreur": str(e)}, status=500)

        redirect_url = url_checkout.get("redirectUrl")

        return JsonResponse({
            "success": True,
            "systeme_paiement": "helloasso",
            "url_helloasso": redirect_url
        })

    elif plateforme == "STRIPE":
        # Stripe : placeholder pour le moment
        return JsonResponse({
            "success": True,
            "systeme_paiement": "stripe",
            "texte": "Simulation Stripe"
        })

    else:
        return JsonResponse({"success": False, "erreur": "Plateforme de paiement non configurée"}, status=400)





class View(CustomView, TemplateView):
    menu_code = "portail_paiement"
    template_name = "portail/paiement_tpe.html"

    def get_context_data(self, **kwargs):
        context = super(View, self).get_context_data(**kwargs)
        context['page_titre'] = "Paiement"

        return context