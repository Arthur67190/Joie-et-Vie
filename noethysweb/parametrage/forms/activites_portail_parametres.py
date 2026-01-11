# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

import datetime
from django import forms
from django.forms import ModelForm
from core.forms.base import FormulaireBase
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Fieldset, Div
from crispy_forms.bootstrap import Field, InlineCheckboxes
from core.utils.utils_commandes import Commandes
from core.models import Activite, ModeleEmail, JOURS_SEMAINE
from core.widgets import DateTimePickerWidget


class Formulaire(FormulaireBase, ModelForm):
    portail_inscriptions_date_debut = forms.DateTimeField(label="Date de début*", required=False, widget=DateTimePickerWidget())
    portail_inscriptions_date_fin = forms.DateTimeField(label="Date de fin*", required=False, widget=DateTimePickerWidget())

    class Meta:
        model = Activite
        fields = ["portail_inscriptions_affichage", "visible", "portail_inscriptions_date_debut", "portail_inscriptions_date_fin",
                  "portail_reservations_limite", "portail_inscriptions_bloquer_si_complet", "portail_inscriptions_imposer_pieces",
                  "reattribution_auto", "reattribution_adresse_exp", "reattribution_delai", "reattribution_modele_email","interne","maitrise", "pay_org_tpe", "pay", "actif", "pay_org"
                  ]
        help_texts = {
            "portail_inscriptions_affichage": "Sélectionnez Autoriser pour permettre aux usagers de demander une inscription à cette activité depuis le portail. Cette demande devra être validée par un utilisateur.",
            "portail_reservations_affichage": "Sélectionnez Autoriser pour permettre aux usagers de gérer leurs réservations pour cette activité sur le portail.",
            "portail_inscriptions_bloquer_si_complet": "L'usager ne peut pas envoyer sa demande d'inscription si l'activité est complète.",
            "portail_inscriptions_imposer_pieces": "Cochez cette case si vous souhaitez que l'usager fournisse obligatoirement les pièces manquantes depuis le portail pour valider sa demande d'inscription.",
            "pay_org_tpe" : "Passerelle de paiement"
        }

    def __init__(self, *args, **kwargs):
        super(Formulaire, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'activites_portail_parametres_form'
        self.helper.form_method = 'post'
        self.helper.use_custom_control = False

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3 col-form-label'
        self.helper.field_class = 'col-md-9'

        # Modèle d'email de réattribution
        self.fields["reattribution_modele_email"].queryset = ModeleEmail.objects.filter(categorie="portail_places_disponibles")

        # Création des boutons de commande
        if self.mode == "CONSULTATION":
            commandes = Commandes(modifier_url="activites_portail_parametres_modifier", modifier_args="idactivite=activite.idactivite", modifier=True, enregistrer=False, annuler=False, ajouter=False)
            self.Set_mode_consultation()
        else:
            commandes = Commandes(annuler_url="{% url 'activites_portail_parametres' idactivite=activite.idactivite %}", ajouter=False)

        # Affichage
        self.helper.layout = Layout(
            commandes,
            Fieldset("Inscriptions",
                Field("portail_inscriptions_affichage"),
                Div(
                    Field("portail_inscriptions_date_debut"),
                    Field("portail_inscriptions_date_fin"),
                    id="bloc_inscriptions_periode"
                ),
                Field("portail_inscriptions_bloquer_si_complet"),
                Field("portail_inscriptions_imposer_pieces"),
            ),
            Fieldset("Visibilité de l'activité sur le portail",
                     Field("visible"),
                     ),

            Fieldset("Visibilité de l'activité sur Sacadoc (archivée ou active)",
                              Field("actif"),

            ),
            Fieldset("Divers",
                     Field("interne"),
                     Field("maitrise"),
                     ),

            Fieldset("Paiement",
                     Field("pay_org_tpe"),
                     Div(
                         Field("pay"),
                         Field("pay_org"),# Champ qui s'affiche uniquement si pay_org_tpe = Payasso
                         id="bloc_pay"
                     ),
                     ),


                     #Fieldset("Réservations",
            #    Field("portail_reservations_affichage"),
            #    Field("limite_delai"),
            #    Div(
            #        Field("limite_heure"),
            #        Field("exclure_weekends"),
            #        Field("exclure_feries"),
            #        InlineCheckboxes("exclure_jours"),
            #        id="bloc_limite"
            #    ),
            #    Field("portail_afficher_dates_passees"),
            #    ),
            #Fieldset("Réattribution automatique des places disponibles",
            #    Field("reattribution_auto"),
            #    Field("reattribution_adresse_exp"),
            #    Field("reattribution_delai"),
            #    Field("reattribution_modele_email"),
            #),
            HTML(EXTRA_SCRIPT),
        )

    def clean(self):
        cleaned_data = super().clean()

        # Inscriptions
        if self.cleaned_data["portail_inscriptions_affichage"] == "PERIODE":
            if not self.cleaned_data["portail_inscriptions_date_debut"]:
                self.add_error('portail_inscriptions_date_debut', "Vous devez sélectionner une date de début d'affichage")
                return
            if not self.cleaned_data["portail_inscriptions_date_fin"]:
                self.add_error('portail_inscriptions_date_fin', "Vous devez sélectionner une date de fin d'affichage")
                return
            if self.cleaned_data["portail_inscriptions_date_debut"] > self.cleaned_data["portail_inscriptions_date_fin"] :
                self.add_error('portail_inscriptions_date_fin', "La date de fin d'affichage doit être supérieure à la date de début")
                return
        else:
            self.cleaned_data["portail_inscriptions_date_debut"] = None
            self.cleaned_data["portail_inscriptions_date_fin"] = None

        # Limite
            self.cleaned_data["portail_reservations_limite"] = None

        #Autres champs pas utilisés
            self.cleaned_data["portail_reservations_affichage"] = "TOUJOURS"
            self.cleaned_data["portail_reservations_limite"] = None
            self.cleaned_data["portail_afficher_dates_passees"] = "Jamais"
            self.cleaned_data["reattribution_auto"] = 0
            self.cleaned_data["reattribution_adresse_exp"] = None
            self.cleaned_data["reattribution_delai"] = None
            self.cleaned_data["reattribution_modele_email"] = None
        return self.cleaned_data


EXTRA_SCRIPT = """
<script>

// Inscriptions
function On_change_affichage_inscriptions() {
    $('#bloc_inscriptions_periode').hide();
    if($(this).val() == 'PERIODE') {
        $('#bloc_inscriptions_periode').show();
    }
}
$(document).ready(function() {
    $('#id_portail_inscriptions_affichage').change(On_change_affichage_inscriptions);
    On_change_affichage_inscriptions.call($('#id_portail_inscriptions_affichage').get(0));
});

// Heure limite
function On_change_limite_reservations() {
    $('#bloc_limite').hide();
    if($(this).val()) {
        $('#bloc_limite').show();
    }
}
$(document).ready(function() {
    $('#id_limite_delai').change(On_change_limite_reservations);
    On_change_limite_reservations.call($('#id_limite_delai').get(0));
});

// Absenti
function On_change_absenti_reservations() {
    $('#div_id_absenti_heure').hide();
    if($(this).val()) {
        $('#div_id_absenti_heure').show();
    }
}
$(document).ready(function() {
    $('#id_absenti_delai').change(On_change_absenti_reservations);
    On_change_absenti_reservations.call($('#id_absenti_delai').get(0));
});

function On_change_pay_org_tpe() {
    $('#bloc_pay').hide();
    if($('#id_pay_org_tpe').val() == 'PAYASSO') {
        $('#bloc_pay').show();
    }
}

$(document).ready(function() {
    $('#id_pay_org_tpe').change(On_change_pay_org_tpe);
    On_change_pay_org_tpe();  // Initialisation
});

</script>
"""
