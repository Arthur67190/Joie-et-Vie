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
from core.models import Activite, Facture, Prestation, Ventilation, PortailPeriode, Paiement, Reglement, Payeur, ModeReglement, CompteBancaire, PortailRenseignement, ModeleImpression, Mandat
from core.utils import utils_portail, utils_fichiers, utils_dates, utils_texte
from django.core.serializers import serialize
from django.views.decorators.http import require_POST
from datetime import date
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
import decimal
from django.db.models import Sum, F, DecimalField, ExpressionWrapper


class View(CustomView, TemplateView):
    menu_code = "portail_facturation"
    template_name = "portail/facturation.html"

    def get_context_data(self, **kwargs):
        context = super(View, self).get_context_data(**kwargs)
        context['page_titre'] = "Facturation"

        return context

    def get(self, request, *args, **kwargs):
        checkout_intent_id = request.GET.get("checkoutIntentId")
        code = request.GET.get("code")
        order_id = request.GET.get("orderId")

        logger.info("Retour HelloAsso")
        logger.info(f"checkoutIntentId={checkout_intent_id}")
        logger.info(f"code={code}")
        logger.info(f"orderId={order_id}")

        if not checkout_intent_id or not code:
            messages.error(request, "Retour de paiement invalide.")
            return redirect("/paiement/error/")

        try:
            paiement = Paiement.objects.get(
                helloasso_checkout_id=checkout_intent_id
            )
        except Paiement.DoesNotExist:
            messages.error(request, "Paiement introuvable.")
            return redirect("/paiement/error/")

        # 🔹 Statut du paiement
        if code == "succeeded":
            paiement.statut = Paiement.STATUT_SUCCES
            paiement.helloasso_order_id = order_id
            paiement.save()

            messages.success(request, "Paiement effectué avec succès 🎉")
            return redirect("/paiement/success/")

        elif code in ["failed", "canceled"]:
            paiement.statut = Paiement.STATUT_ECHEC
            paiement.save()

            messages.error(request, "Le paiement a échoué ou a été annulé.")
            return redirect("/paiement/error/")

        messages.error(request, "Statut de paiement inconnu.")
        return redirect("/paiement/error/")