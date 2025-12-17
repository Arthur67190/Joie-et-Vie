# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django import forms
from django.forms import ModelForm
from core.forms.base import FormulaireBase
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset
from crispy_forms.bootstrap import Field
from core.utils.utils_commandes import Commandes
from core.models import ComptaAvance, Structure
from django.db.models import Q


class Formulaire(FormulaireBase, ModelForm):
    class Meta:
        model = ComptaAvance
        fields = "__all__"
        widgets = {
        }

    def __init__(self, *args, **kwargs):
        super(Formulaire, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'avance_form'
        self.helper.form_method = 'post'
        self.helper.use_custom_control = False

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-2'
        self.helper.field_class = 'col-md-10'
        self.fields['structure'].required = True

        if self.request:
            self.fields["structure"].queryset = Structure.objects.filter(
                Q(idstructure__in=self.request.user.structures.all()) & Q(visible=True)
            ).order_by("nom")

        # Affichage
        self.helper.layout = Layout(
            Commandes(annuler_url="{% url 'assureurs_liste' %}"),
            Field('nom'),
            Field('structure')

        )
