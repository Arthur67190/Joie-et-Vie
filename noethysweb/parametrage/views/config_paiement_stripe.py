# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django.urls import reverse_lazy, reverse
from django.db.models import Count
from core.views.mydatatableview import MyDatatable, columns, helpers
from core.views import crud
from core.models import StripeCompte
from parametrage.forms.config_paiement_stripe import Formulaire


class Page(crud.Page):
    model = StripeCompte
    url_liste = "config_paiement_stripe_liste"
    url_ajouter = "config_paiement_stripe_ajouter"
    url_modifier = "config_paiement_stripe_modifier"
    url_supprimer = "config_paiement_stripe_supprimer"
    description_liste = "Voici ci-dessous la liste des configurations des passerelles de paiement Stripe."
    description_saisie = "Saisissez toutes les informations et cliquez sur le bouton Enregistrer."
    objet_singulier = "une passerelle"
    objet_pluriel = "des passerelles"
    boutons_liste = [
        {"label": "Ajouter", "classe": "btn btn-success", "href": reverse_lazy(url_ajouter), "icone": "fa fa-plus"},
    ]


class Liste(Page, crud.Liste):
    model = StripeCompte

    def get_queryset(self):
        return StripeCompte.objects.filter(self.Get_filtres("Q"))

    def get_context_data(self, **kwargs):
        context = super(Liste, self).get_context_data(**kwargs)
        context['impression_introduction'] = ""
        context['impression_conclusion'] = ""
        context['afficher_menu_brothers'] = True
        return context

    def get_form_kwargs(self, **kwargs):
        """ Envoie l'idactivite au formulaire """
        form_kwargs = super(Page, self).get_form_kwargs(**kwargs)
        form_kwargs["idconfig"] = self.kwargs.get('pk', None)
        return form_kwargs
    class datatable_class(MyDatatable):
        filtres = []
        actions = columns.TextColumn("Actions", sources=None, processor='Get_actions_standard')

        class Meta:
            structure_template = MyDatatable.structure_template
            columns = ["nom", "actif"]
            ordering = ["nom"]


class Ajouter(Page, crud.Ajouter):
    form_class = Formulaire

class Modifier(Page, crud.Modifier):
    form_class = Formulaire

    def get_form_kwargs(self, **kwargs):
        """ Envoie l'idactivite au formulaire """
        form_kwargs = super(Page, self).get_form_kwargs(**kwargs)
        form_kwargs["idconfig"] = self.kwargs.get('pk', None)
        return form_kwargs
class Supprimer(Page, crud.Supprimer):
    pass
