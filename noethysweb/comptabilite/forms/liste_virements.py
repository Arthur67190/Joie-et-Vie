# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

import datetime
from django import forms
from django.forms import ModelForm
from core.forms.base import FormulaireBase
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset
from crispy_forms.bootstrap import Field, PrependedText
from core.widgets import DatePickerWidget
from core.utils.utils_commandes import Commandes
from core.utils import utils_preferences
from core.models import ComptaVirement, CompteBancaire


class Formulaire(FormulaireBase, ModelForm):
    class Meta:
        model = ComptaVirement
        fields = "__all__"
        widgets = {
            "date": DatePickerWidget(),
            "observations": forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super(Formulaire, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "liste_virements_form"
        self.helper.form_method = 'post'

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-2'
        self.helper.field_class = 'col-md-10'

        # Filtrage des comptes bancaires selon l'utilisateur
        if self.request:
            user = self.request.user

            for champ in ("compte_debit", "compte_credit"):
                if champ in self.fields:
                    qs = CompteBancaire.objects.all()

                    if not user.is_superuser:
                        qs = qs.filter(structure__in=user.structures.all())

                    self.fields[champ].queryset = qs.order_by("nom")
                    self.fields[champ].label_from_instance = (
                        lambda obj: f"{obj.nom} ({obj.structure.nom if obj.structure else 'Aucune structure'})"
                    )

        # Date
        if not self.instance.pk:
            self.fields["date"].initial = datetime.date.today()
            # Montant vide par défaut pour les nouveaux virements
            self.fields["montant"].initial = None

        # Affichage
        self.helper.layout = Layout(
            Commandes(annuler_url="{% url 'operations_tresorerie_liste' %}"),
            Fieldset("Généralités",
                Field("date"),
                Field("compte_debit"),
                Field("compte_credit"),
                PrependedText("montant", utils_preferences.Get_symbole_monnaie()),
            ),
            Fieldset("Options",
            #     Field("releve_debit"),
            #     Field("releve_credit"),
                Field("observations"),
            ),
        )

    def clean(self):
        if self.cleaned_data["compte_debit"] == self.cleaned_data["compte_credit"]:
            self.add_error("compte_debit", "Vous devez sélectionner des comptes différents")
            return

        if not self.cleaned_data["montant"]:
            self.add_error("montant", "Vous devez saisir un montant.")
            return
        return self.cleaned_data
