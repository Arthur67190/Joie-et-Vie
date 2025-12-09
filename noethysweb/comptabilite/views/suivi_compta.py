# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

import json, decimal
from collections import Counter
from django.views.generic import TemplateView
from django.db.models import Q, Sum
from core.views.base import CustomView
from core.models import ComptaVentilation, ComptaOperationBudgetaire, ComptaCategorieBudget, ComptaCategorie, CompteBancaire
from comptabilite.forms.suivi_compta import Formulaire


class View(CustomView, TemplateView):
    menu_code = "suivi_compta"
    template_name = "comptabilite/suivi_compta.html"

    def get_context_data(self, **kwargs):
        context = super(View, self).get_context_data(**kwargs)
        context['page_titre'] = "Suivi des finances"
        context['afficher_menu_brothers'] = True
        if "form_parametres" not in kwargs:
            context['form_parametres'] = Formulaire(request=self.request)
        context.update(kwargs)
        return context

    def post(self, request, **kwargs):
        form = Formulaire(request.POST, request=self.request)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form_parametres=form))

        liste_lignes, soldes_hors_bilan = self.Get_resultats(parametres=form.cleaned_data)
        context = {
            "form_parametres": form,
            "liste_lignes": json.dumps(liste_lignes),
            "soldes_hors_bilan": soldes_hors_bilan,
        }
        return self.render_to_response(self.get_context_data(**context))

    def Get_resultats(self, parametres={}):
        comptes = parametres["comptes"]

        condition_structure = (Q(structure__in=self.request.user.structures.all()) | Q(structure__isnull=True)) & Q(bilan=True)

        # Importation des catégories
        dict_categories = {categorie.pk: categorie for categorie in ComptaCategorie.objects.filter(condition_structure)}

        # Importation des ventilations
        condition = Q(operation__compte__in=comptes) & Q(categorie__bilan=True)
        ventilations_tresorerie = Counter({ventilation["categorie"]: ventilation["total"] for ventilation in ComptaVentilation.objects.values("categorie").filter(condition).annotate(total=Sum("montant"))})
        dict_realise = {dict_categories[idcategorie]: montant for idcategorie, montant in dict(ventilations_tresorerie).items()}

        # Création des lignes de catégories
        categories = {**dict_realise}.keys()
        categories = sorted(categories, key=lambda x: (x.type, x.nom))

        # Création des lignes
        lignes = []
        regroupements = {}
        for categorie in categories:
            # Création du regroupement (débit ou crédit)
            if not categorie.type in regroupements:
                regroupements[categorie.type] = {"id": 1000000 + len(regroupements), "realise": decimal.Decimal(0), "budgete": decimal.Decimal(0)}
                lignes.append({"id": regroupements[categorie.type]["id"], "pid": 0, "regroupement": True, "label": categorie.get_type_display()})

            # Calcul des données de la ligne
            realise = dict_realise.get(categorie, decimal.Decimal(0))

            # Mémorisation pour ligne de total
            regroupements[categorie.type]["realise"] += realise

            # Création de la ligne
            lignes.append({"id": categorie.pk, "pid": regroupements[categorie.type]["id"], "regroupement": False,
                           "label": categorie.nom,
                           "realise": float(realise),
                           })

        # Ligne de total
        total_realise = (regroupements.get("credit", {}).get("realise", decimal.Decimal(0))
                         - regroupements.get("debit", {}).get("realise", decimal.Decimal(0)))

        lignes.append({
            "id": 99999998,
            "regroupement": True,
            "label": "Total",
            "realise": float(total_realise),  # <-- on injecte le total ici
        })

        # Soldes hors bilan
        condition_structure_hb = (Q(structure__in=self.request.user.structures.all()) | Q(structure__isnull=True))
        categories_hors_bilan = ComptaCategorie.objects.filter(condition_structure_hb, bilan=False)
        soldes_hors_bilan = []
        for cat in categories_hors_bilan:
            solde = ComptaVentilation.objects.filter(
                operation__compte__in=comptes,
                categorie=cat
            ).aggregate(total=Sum("montant"))["total"] or decimal.Decimal(0)
            soldes_hors_bilan.append((cat.nom, solde, cat.type))  # <-- tuple au lieu de string

        # On renvoie les deux listes
        return lignes, soldes_hors_bilan
