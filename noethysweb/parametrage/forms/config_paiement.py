# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django import forms
import json
from django.forms import ModelForm
from core.forms.base import FormulaireBase
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, ButtonHolder, Submit, HTML, Row, Column, Fieldset
from crispy_forms.bootstrap import Field, FormActions, PrependedText, StrictButton
from core.utils.utils_commandes import Commandes
from core.models import HelloAssoConfig, Activite
from core.forms.select2 import Select2Widget, Select2MultipleWidget
from core.widgets import DateRangePickerWidget, SelectionActivitesWidget
from django.core.exceptions import ValidationError


class Formulaire(FormulaireBase, ModelForm):

    class Meta:
        model = HelloAssoConfig
        fields = ["client_id", "client_secret", "org_slug", "actif", "activites"]
        widgets = {
            "activites": Select2MultipleWidget(),
        }

    def __init__(self, *args, **kwargs):
        self.idconfig = kwargs.pop("idconfig", None)
        super(Formulaire, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'config_paiement_form'
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-2'
        self.helper.field_class = 'col-md-10'

        user_structures = self.request.user.structures.all()
        self.fields["activites"].queryset = Activite.objects.filter(structure__in=self.request.user.structures.all(), visible=True)

        # Affichage
        self.helper.layout = Layout(
            Commandes(annuler_url="{% url 'config_paiement_liste' %}"),
            Fieldset("Passerelle HelloAsso",
                Field('client_id'),
                Field('client_secret'),
                     Field('org_slug'),
                     Field('actif'),
                     Field('activites'),

                     ),
            Fieldset("Passerelle Stripe",
                     )
        )

    def clean(self):
        cleaned_data = super().clean()
        activites = cleaned_data.get("activites")
            # Toutes les configs sauf celle en cours
        qs = HelloAssoConfig.objects.exclude(pk=self.instance.pk)
            # Activités déjà utilisées dans une autre config
        conflits = qs.filter(activites__idactivite__in=activites).distinct()

        if conflits.exists():
                # Récupérer les IDs exacts en conflit
                conflits_ids = conflits.values_list('activites__idactivite', flat=True)
                activites_conflictuelles = Activite.objects.filter(idactivite__in=conflits_ids)
                noms = ", ".join([a.nom for a in activites_conflictuelles])
                raise ValidationError(
                    f"Les activités suivantes sont déjà utilisées dans une autre configuration : {noms}")

        return cleaned_data