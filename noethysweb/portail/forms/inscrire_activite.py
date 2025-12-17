# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

import datetime
from django import forms
from django.forms import ModelForm, CheckboxSelectMultiple, ModelMultipleChoiceField, HiddenInput
from django.db.models import Q
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Hidden, HTML, Div, Field
from crispy_forms.bootstrap import Field
from core.models import Activite, Rattachement, Groupe, PortailRenseignement, CategorieTarif, NomTarif, Tarif, Structure, TarifLigne, PortailDocument
from core.utils.utils_commandes import Commandes
from portail.forms.fiche import FormulaireBase
from individus.utils import utils_pieces_manquantes


class Formulaire_extra(FormulaireBase, forms.Form):
    groupe = forms.ModelChoiceField(label=_("Groupe"), queryset=Groupe.objects.all(), required=True, help_text=_("Sélectionnez le groupe correspondant à l'individu dans la liste."))
    image_url = forms.CharField(widget=HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        structure = kwargs.pop("structure", None)
        activite = kwargs.pop("activite", None)
        famille = kwargs.pop("famille", None)
        individu = kwargs.pop("individu", None)
        super(Formulaire_extra, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'portail_inscrire_activite_extra_form'
        self.helper.form_method = 'post'
        self.helper.attrs = {'enctype': 'multipart/form-data'}
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-2 col-form-label'
        self.helper.field_class = 'col-md-10'
        self.helper.use_custom_control = False
        self.helper.form_tag = False

        # Initialisation de self.helper.layout avec un Layout vide
        self.helper.layout = Layout()

        # Pour chaque tarif, ajoute un champ avec une case à cocher
        liste_nom_tarif = NomTarif.objects.filter(activite=activite, visible=True).order_by("nom").distinct()
        for nom_tarif in liste_nom_tarif:
            tarifs = Tarif.objects.filter(nom_tarif=nom_tarif, activite=activite, visible=True)

            # Vérifie si des tarifs sont associés au nom_tarif
            if tarifs.exists():
                field_name = f"tarifs_{nom_tarif.idnom_tarif}"
                self.fields[field_name] = forms.ModelChoiceField(
                    label=nom_tarif.nom,
                    queryset=tarifs,
                    widget=forms.RadioSelect(),
                    required=False
                )
                # Modification du widget pour afficher le label avec description + montant_unique
                tarif_choices = []
                for tarif in tarifs:
                    tarif_lignes = TarifLigne.objects.filter(tarif=tarif)
                    montant_unique = tarif_lignes.first().montant_unique if tarif_lignes.exists() else 0
                    montant_formate = f"{montant_unique:,.2f}".replace(',', ' ').replace('.',
                                                                                         ',')  # Formater avec espace comme séparateur
                    tarif_choices.append((tarif.pk, f"{tarif.description} - {montant_formate}\u00A0€"))

                self.fields[field_name].widget.choices = tarif_choices
            else:
                continue

        liste_groupes = Groupe.objects.filter(activite=activite).order_by("nom")
        self.fields["groupe"].queryset = liste_groupes
        if len(liste_groupes) == 1:
            self.fields["groupe"].initial = liste_groupes.first()

        # Mise à jour de l'URL de l'image
        image_url = activite.image.url if activite and activite.image else None
        if image_url:
            self.helper.layout.append(
                HTML(
                    f'<div id="image-container" style="text-align: center; margin-bottom: 20px;">'
                    f'<img src="{image_url}" alt="Image de l\'activité" style="max-width: 100%; height: auto; width: auto; max-height: 600px; border: 2px solid #ddd; box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);">'
                    f'</div>'
                )
            )

        # Ajout des autres champs
        self.helper.layout.append(Field("groupe"))
        self.helper.layout.extend([
            Field(f"tarifs_{nom_tarif.idnom_tarif}")
            for nom_tarif in liste_nom_tarif
        ])

        # Ajout des pièces à fournir si nécessaire
        if activite.portail_inscriptions_imposer_pieces:
            pieces_necessaires = utils_pieces_manquantes.Get_liste_pieces_necessaires(activite=activite,
                                                                                      famille=famille,
                                                                                      individu=individu)

            # Vérifiez si toutes les pièces sont valides
            pieces_pas_valides = [piece for piece in pieces_necessaires if not piece["valide"]]

            print(pieces_pas_valides)

            if not pieces_necessaires:
                self.helper.layout.append(HTML("<p>Aucune pièce justificative n'est requise pour cette activité.</p>"))
            elif not pieces_pas_valides:
                self.helper.layout.append(
                    HTML("<p>Toutes les pièces justificatives sont déjà fournies et validées.</p>"))
            else:
                for piece_necessaire in pieces_necessaires:
                    if not piece_necessaire["valide"]:
                        nom_field = f"document_{piece_necessaire['type_piece'].pk}"
                        help_text = """Vous devez joindre ce document au format pdf, jpg ou png. """

                        portail_document = PortailDocument.objects.filter(activites=activite, type_piece=piece_necessaire["type_piece"]).first()

                        if portail_document:
                            url_document_a_telecharger = portail_document.document.url
                            help_text += f"""Vous pouvez télécharger le document modèle de la structure à compléter en cliquant sur le lien suivant : 
                                                         <a href='{url_document_a_telecharger}' target="_blank" title="Télécharger le document">
                                                         <i class="fa fa-download margin-r-5"></i>Télécharger le document</a>."""
                        elif piece_necessaire["document"]:
                            url_document_a_telecharger = piece_necessaire["document"].document.url
                            help_text += f"""Vous pouvez télécharger le document modèle standard à compléter en cliquant sur le lien suivant : 
                                                         <a href='{url_document_a_telecharger}' target="_blank" title="Télécharger le document">
                                                         <i class="fa fa-download margin-r-5"></i>Télécharger le document</a>."""

                        self.fields[nom_field] = forms.FileField(
                            label=piece_necessaire["type_piece"].nom,
                            help_text=help_text,
                            required=True,
                            validators=[FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg'])]
                        )
                        self.helper.layout.append(Field(nom_field))


class Formulaire(FormulaireBase, ModelForm):
    activite = forms.ModelChoiceField(label=_("Activité"), queryset=Activite.objects.none(), required=True, help_text=_("Sélectionnez l'activité souhaitée dans la liste."))
    structure = forms.ModelChoiceField(label=_("Structures"), queryset=Structure.objects.none(), required=True, help_text=_("Sélectionnez la structure souhaitée dans la liste."))

    class Meta:
        model = PortailRenseignement
        fields = "__all__"
        labels = {
            "individu": _("Individu"),
        }
        help_texts = {
            "individu": _("Sélectionnez le membre de la famille à inscrire."),
        }

    def __init__(self, *args, **kwargs):
        super(Formulaire, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'portail_inscrire_activite_form'
        self.helper.form_method = 'post'

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-2 col-form-label'
        self.helper.field_class = 'col-md-10'
        self.helper.use_custom_control = False
        self.helper.attrs = {'enctype': 'multipart/form-data'}

        # Individu (avec filtrage de la catégorie 2)
        rattachements = Rattachement.objects.select_related("individu").filter(
            famille=self.request.user.famille).exclude(individu__in=self.request.user.famille.individus_masques.all()).order_by("categorie")

        self.fields["individu"].choices = [(rattachement.individu_id, rattachement.individu.Get_nom()) for rattachement
                                           in rattachements]
        self.fields["individu"].required = True

        # Activité
        conditions = (Q(visible=True) & Q(portail_inscriptions_affichage="TOUJOURS") | (Q(portail_inscriptions_affichage="PERIODE") & Q(
            portail_inscriptions_date_debut__lte=datetime.datetime.now()) & Q(
            portail_inscriptions_date_fin__gte=datetime.datetime.now())))
        self.fields["activite"].queryset = Activite.objects.filter(conditions).order_by("nom")

        conditions = (Q(visible=True))
        self.fields["structure"].queryset = Structure.objects.filter(conditions).order_by("nom")

        # Affichage
        self.helper.layout = Layout(
            Hidden("famille", value=self.request.user.famille.pk),
            Hidden("etat", value="ATTENTE"),
            Hidden("categorie", value="activites"),
            Hidden("code", value="inscrire_activite"),
            Field("individu"),
            Field("structure"),
            Field("activite"),
            Div(id="form_extra"),
            HTML(EXTRA_SCRIPT),
            Commandes(
                enregistrer_label="<i class='fa fa-send margin-r-5'></i>%s" % _("Envoyer la demande d'inscription"),
                annuler_url="{% url 'portail_activites' %}", ajouter=False, aide=False, css_class="pull-right"),
        )


EXTRA_SCRIPT = """
<script>
    // Fonction pour mettre à jour les activités en fonction de la structure sélectionnée
    function On_change_structure() {
        var idstructure = $("#id_structure").val(); // Récupère l'ID de la structure sélectionnée
        if (!idstructure) {
            $("#id_activite").empty().append(new Option("Sélectionnez une structure pour découvrir les activités", ""));
            return;
        }
        $.ajax({
            type: "POST",
            url: "{% url 'portail_ajax_get_activites_par_structure' %}",
            data: {
                'structure_id': idstructure,
                'csrfmiddlewaretoken': "{{ csrf_token }}" // Ajoutez le token CSRF pour la sécurité
            },
            success: function(data) {
                var $activiteField = $("#id_activite");
                $activiteField.empty(); // Vide le champ des activités

                if (data.activites.length === 0) {
                    $activiteField.append(new Option("Aucune activité disponible à l'inscription", ""));
                } else {
                    // Ajoute les nouvelles options au champ des activités
                    $.each(data.activites, function(index, activite) {
                        $activiteField.append(new Option(activite.nom, activite.id));
                    });
                }
                On_change_activite();

            },
            error: function() {
                console.error("Erreur lors de la récupération des activités.");
            }
        });
    }

    // Fonction pour actualiser le formulaire en fonction de l'activité sélectionnée
    function On_change_activite() {
        var idactivite = $("#id_activite").val(); // Récupère l'ID de l'activité sélectionnée
        $.ajax({
            type: "POST",
            url: "{% url 'portail_ajax_inscrire_get_form_extra' %}",
            data: $("#portail_inscrire_activite_form").serialize(),
        success: function (data) {
            $("#form_extra").html(data['form_html']);
        }

        });
    }

    $(document).ready(function() {
        // Appelle On_change_structure lors du changement de structure
        $('#id_structure').change(On_change_structure);
        // Appelle On_change_activite lors du changement d'activité
        $('#id_activite').change(On_change_activite);

        // Initialise les listes d'activités lors du chargement de la page
        On_change_structure(); // Met à jour les activités en fonction de la structure initiale

        // Gestion de la soumission du formulaire
        $("#portail_inscrire_activite_form").on('submit', function (event) {
            event.preventDefault();
            var formData = new FormData($("#portail_inscrire_activite_form")[0]);
            formData.append("csrfmiddlewaretoken", "{{ csrf_token }}");
            $.ajax({
                type: "POST",
                url: "{% url 'portail_ajax_inscrire_valid_form' %}",
                data: formData,
                contentType: false,
                processData: false,
                datatype: "json",
                success: function(data){
                    window.location.href = data.url;
                },
                error: function(data) {
                    toastr.error(data.responseJSON.erreur);
                }
            });
        });
    });
</script>
"""
