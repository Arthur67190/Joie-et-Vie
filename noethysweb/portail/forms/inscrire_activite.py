# -*- coding: utf-8 -*-

import datetime
import json
from django import forms
from django.forms import ModelForm
from django.db.models import Q
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Hidden, HTML, Div, Field
from core.models import (Activite, Rattachement, Groupe, PortailRenseignement,
                         NomTarif, Tarif, Structure, TarifLigne,PortailDocument)
from core.utils.utils_commandes import Commandes
from portail.forms.fiche import FormulaireBase
from individus.utils import utils_pieces_manquantes


class Formulaire_extra(FormulaireBase, forms.Form):
    """ Formulaire dynamique pour les tarifs et pièces jointes """

    def __init__(self, *args, **kwargs):
        activite = kwargs.pop("activite", None)
        famille = kwargs.pop("famille", None)
        individu = kwargs.pop("individu", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.label_class = 'col-md-3'
        self.helper.field_class = 'col-md-9'

        layout_elements = []

        # 1. Image de l'activité
        if activite and activite.image:
            layout_elements.append(HTML(
                f'<div class="text-center my-3">'
                f'<img src="{activite.image.url}" class="img-fluid rounded shadow-sm" style="max-height: 400px;">'
                f'</div>'
            ))

        # 2. Tarifs (Radio boutons)
        if activite:
            noms_tarifs = NomTarif.objects.filter(activite=activite, visible=True).order_by("nom")
            if noms_tarifs.exists():
                # Ajout du titre pour la section Tarifs
                layout_elements.append(HTML("""
                                <div class='alert alert-warning mb-4 shadow-sm border-0'>
                                    <div class='d-flex align-items-center'>
                                        <i class='fa fa-euro fa-2x mr-3 text-info'></i>
                                        <div>
                                            <h5 class='mb-0 text-bold'>Choix des tarifs</h5>
                                            <p class='mb-0 small text-muted'>Veuillez sélectionner le tarif correspondant à votre situation.</p>
                                        </div>
                                    </div>
                                </div>
                            """))
            for nt in noms_tarifs:
                tarifs = Tarif.objects.filter(nom_tarif=nt, activite=activite, visible=True)
                if tarifs.exists():
                    f_name = f"tarifs_{nt.idnom_tarif}"
                    choices = []
                    for t in tarifs:
                        ligne = TarifLigne.objects.filter(tarif=t).first()
                        montant = f"{ligne.montant_unique:,.2f} €".replace('.', ',') if ligne else "0,00 €"
                        choices.append((t.pk, f"{t.description} ({montant})"))

                    self.fields[f_name] = forms.ModelChoiceField(
                        label=f"<strong>{nt.nom}</strong>",
                        queryset=tarifs,
                        widget=forms.RadioSelect(),
                        required=False  # Optionnel pour pouvoir décocher
                    )
                    self.fields[f_name].choices = choices
                    layout_elements.append(Field(f_name))

            if activite and famille and individu:  # Sécurité pour éviter le TypeError
                if activite.portail_inscriptions_imposer_pieces:
                    pieces_necessaires = utils_pieces_manquantes.Get_liste_pieces_necessaires(
                        activite=activite,
                        famille=famille,
                        individu=individu
                    )

                    pieces_pas_valides = [piece for piece in pieces_necessaires if not piece["valide"]]
                    if pieces_pas_valides:
                        layout_elements.append(HTML("""
                            <div class='alert alert-warning mb-4 shadow-sm border-0'>
                                <div class='d-flex align-items-center'>
                                    <i class='fa fa-file fa-2x mr-3 text-info'></i>
                                    <div>
                                        <h5 class='mb-0 text-bold'>Pièces justificatives manquantes</h5>
                                        <p class='mb-0 small text-muted'>Veuillez joindre les documents requis pour finaliser votre inscription.</p>
                                    </div>
                                </div>
                            </div>
                        """))
                    if not pieces_necessaires:
                        layout_elements.append(
                            HTML("<p class='alert alert-info'>Aucune pièce justificative n'est requise.</p>"))
                    elif not pieces_pas_valides:
                        layout_elements.append(
                            HTML("<p class='alert alert-success'>Toutes les pièces sont déjà validées.</p>"))
                    else:
                        for piece_necessaire in pieces_necessaires:
                            if not piece_necessaire["valide"]:
                                nom_field = f"document_{piece_necessaire['type_piece'].pk}"

                                # --- Préparation du texte d'aide avec icône de téléchargement ---
                                help_text = ""
                                modele_url = None

                                portail_document = PortailDocument.objects.filter(activites=activite,
                                                                                  type_piece=piece_necessaire[
                                                                                      "type_piece"]).first()
                                if portail_document:
                                    modele_url = portail_document.document.url
                                elif piece_necessaire["document"]:
                                    modele_url = piece_necessaire["document"].document.url

                                if modele_url:
                                    help_text = f"""<div class='mt-2'><a href='{modele_url}' target='_blank' class='btn btn-xs btn-outline-info'>
                                                        <i class='fa fa-download mr-1'></i> Télécharger le modèle à compléter</a></div>"""

                                self.fields[nom_field] = forms.FileField(
                                    label=piece_necessaire["type_piece"].nom,
                                    help_text=help_text,
                                    required=True,
                                    widget=forms.FileInput(attrs={'class': 'form-control-file'}),  # Widget plus propre
                                    validators=[FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg'])]
                                )

                                # Encapsulation dans une Div stylisée
                                layout_elements.append(Div(
                                    Field(nom_field),
                                    css_class="document-upload-box p-3 mb-3 border rounded bg-light"
                                ))

        self.helper.layout = Layout(*layout_elements)


class Formulaire(FormulaireBase, ModelForm):
    # On utilise des QuerySets larges pour que Django accepte la validation des IDs envoyés en AJAX
    activite = forms.ModelChoiceField(label=_("Activité"), queryset=Activite.objects.all(), required=True)
    structure = forms.ModelChoiceField(label=_("Structures"), queryset=Structure.objects.all(), required=True)
    groupe = forms.ModelChoiceField(label=_("Groupe"), queryset=Groupe.objects.all(), required=True)

    class Meta:
        model = PortailRenseignement
        # On liste explicitement les champs pour s'assurer qu'ils sont traités
        fields = ["individu", "famille", "structure", "activite", "groupe", "etat", "categorie", "code"]

    def __init__(self, *args, **kwargs):
        super(Formulaire, self).__init__(*args, **kwargs)

        # Initialisation des valeurs par défaut pour les champs cachés
        if self.request:
            self.fields["famille"].initial = self.request.user.famille.pk
        self.fields["etat"].initial = "ATTENTE"
        self.fields["categorie"].initial = "activites"
        self.fields["code"].initial = "inscrire_activite"

        self.helper = FormHelper()
        self.helper.form_id = 'portail_inscrire_activite_form'
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-2 col-form-label'
        self.helper.field_class = 'col-md-10'
        self.helper.attrs = {'enctype': 'multipart/form-data', 'novalidate': ''}  # novalidate aide pour le focusable

        # Filtrage des individus de la famille
        rattachements = Rattachement.objects.select_related("individu").filter(
            famille=self.request.user.famille).exclude(
            individu__in=self.request.user.famille.individus_masques.all()).order_by("categorie")
        self.fields["individu"].choices = [(r.individu_id, r.individu.Get_nom()) for r in rattachements]

        # On réduit le QuerySet d'affichage pour l'activité (mais Django garde .all() pour valider)
        conditions = (Q(visible=True) & Q(portail_inscriptions_affichage="TOUJOURS") |
                      (Q(portail_inscriptions_affichage="PERIODE") &
                       Q(portail_inscriptions_date_debut__lte=datetime.datetime.now()) &
                       Q(portail_inscriptions_date_fin__gte=datetime.datetime.now())))
        self.fields["activite"].queryset = Activite.objects.filter(conditions).order_by("nom")

        self.helper.layout = Layout(
            Hidden("famille", self.fields["famille"].initial),
            Hidden("etat", self.fields["etat"].initial),
            Hidden("categorie", self.fields["categorie"].initial),
            Hidden("code", self.fields["code"].initial),
            Field("individu"),
            Field("structure"),
            Field("activite"),
            Field("groupe"),
            Div(id="form_extra"),
            HTML(EXTRA_SCRIPT),
            Commandes(
                enregistrer_label="<i class='fa fa-send mr-2'></i>Envoyer la demande",
                annuler_url="{% url 'portail_activites' %}", ajouter=False, aide=False, css_class="pull-right"),
        )


EXTRA_SCRIPT = """
<script>
$(function () {
    const $form = $("#portail_inscrire_activite_form");
    const $structure = $("#id_structure");
    const $activite = $("#id_activite");
    const $groupe = $("#id_groupe");
    const $divExtra = $("#form_extra");
    const $placeholder = $("#placeholder_extra");

    let dataActivites = []; 

    // Initialisation : on vide l'activité au chargement de la page
    $activite.empty().append(new Option("Sélectionnez d'abord une structure", ""));
    $groupe.empty().append(new Option("---", ""));

    // --- CASCADE 1 : STRUCTURE -> ACTIVITÉ ---
    $structure.on("change", function() {
        const structureId = $(this).val();

        // On vide tout en dessous immédiatement
        $activite.empty().append(new Option("Chargement...", ""));
        $groupe.empty().append(new Option("---", ""));
        $divExtra.empty();
        $placeholder.show();

        if (!structureId) {
            $activite.empty().append(new Option("Sélectionnez une structure", ""));
            return;
        }

        $.post("{% url 'portail_ajax_get_activites_par_structure' %}", {
            structure_id: structureId,
            csrfmiddlewaretoken: "{{ csrf_token }}"
        }).done(function(data) {
            dataActivites = data.activites;
            $activite.empty().append(new Option("--- Choisir une activité ---", ""));
            $.each(dataActivites, function(_, act) {
                // On s'assure que act.id est le nombre et act.nom le texte
                $activite.append(new Option(act.nom, act.id));
            });
        });
    });

    // --- CASCADE 2 : ACTIVITÉ -> GROUPE & FORM EXTRA ---
    $activite.on("change", function() {
        const activiteId = $(this).val();
        
        if (activiteId) {
        // 1. ON ACTIVE LE CHAMP (on retire le "grisé")
        $groupe.prop('disabled', false);
        $groupe.empty();
        
        // 2. Remplissage des groupes
        const selectedAct = dataActivites.find(a => String(a.id) === String(activiteId));
        
        if (selectedAct && selectedAct.groupes) {
            $.each(selectedAct.groupes, function(_, g) {
                $groupe.append(new Option(g.nom, g.idgroupe));
            });
        } else {
            $groupe.append(new Option("Aucun groupe disponible", ""));
        }

        // 2. Chargement du bloc Extra (Tarifs/Pièces)
        $placeholder.hide();
        $divExtra.html('<div class="text-center py-3"><i class="fa fa-spinner fa-spin"></i> Chargement...</div>');

        // On n'envoie l'AJAX que si on a un ID d'activité valide
        $.post("{% url 'portail_ajax_inscrire_get_form_extra' %}", $form.serialize())
            .done(function (data) {
                $divExtra.html(data.form_html);
            })
            .fail(function () {
                toastr.error("Erreur de chargement.");
            });
    });
});
</script>
"""
