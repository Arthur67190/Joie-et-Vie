# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Fieldset
from crispy_forms.bootstrap import Field
from django_select2.forms import Select2Widget, ModelSelect2Widget
from core.utils.utils_commandes import Commandes
from core.widgets import SelectionActivitesWidget, DateRangePickerWidget
from core.forms.base import FormulaireBase
from core.models import CompteBancaire
from datetime import date, timedelta
from django.db.models import Q
import datetime


class Formulaire(FormulaireBase, forms.Form):
    compte = forms.ModelChoiceField(label="Compte", widget=Select2Widget({"lang": "fr", "data-width": "100%", "data-minimum-input-length": 0}), queryset=CompteBancaire.objects.none(), required=True)
    periode = forms.CharField(label="Période", required=True, widget=DateRangePickerWidget(attrs={"afficher_check": False}))

    def __init__(self, *args, **kwargs):
        super(Formulaire, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'form_parametres'
        self.helper.form_method = 'post'

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-2'
        self.helper.field_class = 'col-md-10'

        self.fields["compte"].queryset = CompteBancaire.objects.filter(Q(structure__in=self.request.user.structures.all()) | Q(structure__isnull=True)).order_by("nom")

        # Période par défaut: aujourd'hui jusqu'à un an plus tard
        date_debut = date(1900, 1, 1)
        date_fin = date.today()
        periode_initial = f"{date_debut};{date_fin}"
        self.fields["periode"].initial = periode_initial

        self.helper.layout = Layout(
            Commandes(annuler_url="{% url 'comptabilite_toc' %}", enregistrer=False, ajouter=False,
                      commandes_principales=[HTML(
                          """<a type='button' class="btn btn-primary margin-r-5" onclick="generer_pdf()" title="Génération du PDF"><i class='fa fa-file-pdf-o margin-r-5'></i>Générer le PDF</a>"""),
                      ]),
            Fieldset("Sélection des paramètres",
                Field("compte"),
                Field("periode"),
            ),
        )
