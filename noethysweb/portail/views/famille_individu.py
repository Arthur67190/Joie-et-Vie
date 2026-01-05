import logging
from datetime import datetime

from django.views.generic import TemplateView

from core.models import (
    CATEGORIE_RATTACHEMENT_ENFANT,
    Famille,
    Individu,
    Rattachement,
    Utilisateur,
    ContactUrgence,
)
from core.utils import utils_questionnaires
from django import forms
from django.urls import reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, HTML, Fieldset, Field

from core.widgets import CodePostal, Ville, Select_many_avec_plus
from portail.views.base import CustomView

logger = logging.getLogger(__name__)


# Widget personnalisé pour le portail qui évite les conflits avec plusieurs widgets sur la même page
class PortailSelectManyAvecPlus(Select_many_avec_plus):
    template_name = "portail/widgets/select_many_avec_plus.html"


class IndividuForm(forms.ModelForm):
    date_naiss = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Date de naissance",
    )
    prenom = forms.CharField(max_length=200, required=True, label="Prénom")
    nom = forms.CharField(max_length=200, required=False, label="Nom")
    photo = forms.ImageField(
        required=False,
        label="Photo de l'enfant",
        help_text="Format JPG ou PNG recommandé",
    )

    # Coordonnées - avec option de copie depuis parent
    copier_adresse_parent = forms.BooleanField(
        required=False,
        initial=True,
        label="Utiliser l'adresse du premier parent",
        help_text="Si coché, l'adresse sera automatiquement copiée depuis le premier parent de la famille",
    )
    rue_resid = forms.CharField(
        required=False, label="Rue", widget=forms.Textarea(attrs={"rows": 2})
    )
    cp_resid = forms.CharField(required=False, label="Code postal", max_length=50)
    ville_resid = forms.CharField(required=False, label="Ville", max_length=200)

    # Allergies
    allergies_detail = forms.CharField(
        required=False,
        label="Conduite à tenir en cas d'allergie",
        widget=forms.Textarea(attrs={"rows": 3}),
        max_length=400,
    )

    # Dispositifs médicaux
    dispmed_detail = forms.CharField(
        required=False,
        label="Conduite à tenir concernant les dispositifs médicaux",
        widget=forms.Textarea(attrs={"rows": 3}),
        max_length=400,
    )

    # Contacts d'urgence - on en crée au moins un
    contact_nom = forms.CharField(
        required=False, label="Nom du contact", max_length=200
    )
    contact_prenom = forms.CharField(
        required=False, label="Prénom du contact", max_length=200
    )
    contact_lien = forms.CharField(
        required=False,
        label="Lien avec l'enfant",
        max_length=200,
        help_text="Ex: Mère, Père, Grand-mère, Tante...",
    )
    contact_tel_mobile = forms.CharField(
        required=False, label="Téléphone portable", max_length=100
    )
    contact_tel_domicile = forms.CharField(
        required=False, label="Téléphone domicile", max_length=100
    )
    contact_autorisation_sortie = forms.BooleanField(
        required=False, initial=True, label="Autorisé à récupérer l'enfant"
    )
    contact_autorisation_appel = forms.BooleanField(
        required=False, initial=True, label="À contacter en cas d'urgence"
    )

    class Meta:
        model = Individu
        fields = [
            "civilite",
            "prenom",
            "nom",
            "date_naiss",
            "cp_naiss",
            "ville_naiss",
            "photo",
            "rue_resid",
            "cp_resid",
            "ville_resid",
            "regimes_alimentaires",
            "allergies",
            "allergies_detail",
            "dispmed",
            "dispmed_detail",
            "medecin",
        ]
        widgets = {
            "cp_naiss": CodePostal(attrs={"id_ville": "id_ville_naiss"}),
            "ville_naiss": Ville(attrs={"id_codepostal": "id_cp_naiss"}),
            "regimes_alimentaires": PortailSelectManyAvecPlus(
                attrs={
                    "url_ajax": "portail_ajax_ajouter_regime_alimentaire",
                    "textes": {
                        "champ": "Nom du régime alimentaire",
                        "ajouter": "Ajouter un régime alimentaire",
                    },
                }
            ),
            "allergies": PortailSelectManyAvecPlus(
                attrs={
                    "url_ajax": "portail_ajax_ajouter_allergie",
                    "textes": {
                        "champ": "Nom de l'allergie",
                        "ajouter": "Ajouter une allergie",
                    },
                }
            ),
            "dispmed": PortailSelectManyAvecPlus(
                attrs={
                    "url_ajax": "portail_ajax_ajouter_dispmed",
                    "textes": {
                        "champ": "Nom du dispositif médical",
                        "ajouter": "Ajouter un dispositif médical",
                    },
                }
            ),
        }
        labels = {
            "civilite": "Civilité",
            "cp_naiss": "Code postal de naissance",
            "ville_naiss": "Ville de naissance",
            "regimes_alimentaires": "Régimes alimentaires",
            "allergies": "Allergies",
            "dispmed": "Dispositifs médicaux",
            "medecin": "Médecin traitant",
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user: Utilisateur = user
        super().__init__(*args, **kwargs)

        # Rendre les champs many-to-many non obligatoires
        self.fields["regimes_alimentaires"].required = False
        self.fields["allergies"].required = False
        self.fields["dispmed"].required = False
        self.fields["medecin"].required = False

        # Trier les listes par ordre alphabétique
        if hasattr(self.fields["regimes_alimentaires"], "queryset"):
            self.fields["regimes_alimentaires"].queryset = self.fields[
                "regimes_alimentaires"
            ].queryset.order_by("nom")
        if hasattr(self.fields["allergies"], "queryset"):
            self.fields["allergies"].queryset = self.fields[
                "allergies"
            ].queryset.order_by("nom")
        if hasattr(self.fields["dispmed"], "queryset"):
            self.fields["dispmed"].queryset = self.fields["dispmed"].queryset.order_by(
                "nom"
            )
        if hasattr(self.fields["medecin"], "queryset"):
            self.fields["medecin"].queryset = self.fields["medecin"].queryset.order_by(
                "nom", "prenom"
            )

        # Ajouter les help_texts avec lien pour ajouter un élément
        # Note: Le widget Select_many_avec_plus a déjà un bouton + pour ajouter des éléments
        # Nous ajoutons juste des instructions d'utilisation
        self.fields["regimes_alimentaires"].help_text = (
            "Cliquez sur le champ ci-dessus pour faire apparaître la liste de choix et sélectionnez un ou plusieurs éléments. "
            "Utilisez le bouton + à droite du champ pour ajouter un régime alimentaire manquant dans la liste de choix."
        )
        self.fields["allergies"].help_text = (
            "Cliquez sur le champ ci-dessus pour faire apparaître la liste de choix et sélectionnez un ou plusieurs éléments. "
            "Utilisez le bouton + à droite du champ pour ajouter une allergie manquante dans la liste de choix."
        )
        self.fields["dispmed"].help_text = (
            "Cliquez sur le champ ci-dessus pour faire apparaître la liste de choix et sélectionnez un ou plusieurs éléments. "
            "Utilisez le bouton + à droite du champ pour ajouter un dispositif médical manquant dans la liste de choix."
        )

        # Configuration de crispy forms avec accordéon pour les sections optionnelles
        self.helper = FormHelper()
        self.helper.form_id = "famille_individu_form"
        self.helper.form_method = "post"
        self.helper.form_class = "form-horizontal"
        self.helper.attrs = {
            "enctype": "multipart/form-data"
        }  # Pour l'upload de la photo
        self.helper.label_class = "col-md-3 col-form-label"
        self.helper.field_class = "col-md-9"

        self.helper.layout = Layout(
            Fieldset(
                "Informations générales",
                Field("civilite"),
                Field("prenom"),
                Field("nom"),
                Field("date_naiss"),
                Field("cp_naiss"),
                Field("ville_naiss"),
                Field("photo"),
            ),
            Fieldset(
                "Coordonnées",
                Field("copier_adresse_parent"),
                Div(
                    Field("rue_resid"),
                    Field("cp_resid"),
                    Field("ville_resid"),
                    css_id="adresse_manuelle",
                ),
                HTML("""
                <script>
                $(document).ready(function() {
                    function toggleAdresse() {
                        if ($('#id_copier_adresse_parent').is(':checked')) {
                            $('#adresse_manuelle').hide();
                        } else {
                            $('#adresse_manuelle').show();
                        }
                    }
                    toggleAdresse();
                    $('#id_copier_adresse_parent').change(toggleAdresse);
                });
                </script>
                """),
            ),
            Fieldset(
                "Allergies (optionnel)",
                Field("allergies"),
                Field("allergies_detail"),
            ),
            Fieldset(
                "Dispositifs médicaux (optionnel)",
                Field("dispmed"),
                Field("dispmed_detail"),
            ),
            Fieldset(
                "Contact d'urgence (optionnel)",
                HTML(
                    '<div class="alert alert-info mb-3"><i class="fa fa-info-circle"></i> Si cet onglet est vide, le contact d\'urgence par défaut est le parent.</div>'
                ),
                Field("contact_nom"),
                Field("contact_prenom"),
                Field("contact_lien"),
                Field("contact_tel_mobile"),
                Field("contact_tel_domicile"),
            ),
            Div(
                HTML('<div class="col-md-9 offset-md-3">'),
                Submit("submit", "Enregistrer", css_class="btn btn-primary"),
                HTML(
                    '<a href="{% url \'portail_renseignements\' %}" class="btn btn-secondary ml-2">Annuler</a>'
                ),
                HTML("</div>"),
                css_class="form-group row",
            ),
        )

    def save_individu(self, famille: Famille):
        # Sauvegarde de l'objet Individu en base de données
        individu = super().save(commit=False)
        individu.statut = Individu.STATUT_JEUNE

        # Gestion de l'adresse
        copier_adresse = self.cleaned_data.get("copier_adresse_parent", True)
        if copier_adresse:
            # Recherche d'une adresse à rattacher (premier parent)
            rattachement_addr = (
                Rattachement.objects.prefetch_related("individu")
                .filter(famille=famille, individu__adresse_auto__isnull=True)
                .first()
            )
            if rattachement_addr:
                individu.adresse_auto = rattachement_addr.individu.pk
        else:
            # Utilise l'adresse saisie manuellement
            individu.rue_resid = self.cleaned_data.get("rue_resid")
            individu.cp_resid = self.cleaned_data.get("cp_resid")
            individu.ville_resid = self.cleaned_data.get("ville_resid")
            individu.adresse_auto = None

        individu.save()

        # Sauvegarde des relations many-to-many
        self.save_m2m()

        # Création des questionnaires de type individu
        utils_questionnaires.Creation_reponses(
            categorie="individu", liste_instances=[individu]
        )

        # Sauvegarde du rattachement
        rattachement = Rattachement(
            famille=famille,
            individu=individu,
            categorie=CATEGORIE_RATTACHEMENT_ENFANT,
            titulaire=False,
            certification_date=datetime.now(),
        )
        rattachement.save()
        individu.Maj_infos()

        # Création du contact d'urgence si les informations sont renseignées
        contact_nom = self.cleaned_data.get("contact_nom")
        contact_prenom = self.cleaned_data.get("contact_prenom")
        if contact_nom or contact_prenom:
            contact = ContactUrgence(
                individu=individu,
                famille=famille,
                nom=contact_nom or "",
                prenom=contact_prenom or "",
                lien=self.cleaned_data.get("contact_lien", ""),
                tel_mobile=self.cleaned_data.get("contact_tel_mobile", ""),
                tel_domicile=self.cleaned_data.get("contact_tel_domicile", ""),
                autorisation_sortie=self.cleaned_data.get(
                    "contact_autorisation_sortie", True
                ),
                autorisation_appel=self.cleaned_data.get(
                    "contact_autorisation_appel", True
                ),
            )
            contact.save()

        return individu


class AjouterIndividu(CustomView, TemplateView):
    template_name = "portail/famille_individu.html"
    menu_code = "portail_renseignements"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_titre"] = "Ajouter un enfant"

        # Le breadcrumb est déjà fourni par CustomView, on peut le compléter si besoin
        if "breadcrumb" in context and context["breadcrumb"]:
            context["breadcrumb"].append(
                {"titre": "Ajouter un enfant", "url": "", "code": ""}
            )

        if self.request.method == "POST":
            context["form"] = IndividuForm(
                self.request.POST, self.request.FILES, user=self.request.user
            )
        else:
            context["form"] = IndividuForm(user=self.request.user)

        return context

    def post(self, request, *args, **kwargs):
        form = IndividuForm(request.POST, request.FILES, user=request.user)
        logger.debug(f"Données soumises: {request.POST}")

        if form.is_valid():
            famille = request.user.famille
            logger.debug(f"Famille: {famille}")
            individu = form.save_individu(famille)
            logger.debug(f"Individu enregistré: {individu}")

            from django.contrib import messages

            messages.success(
                request, f"L'enfant {individu.Get_nom()} a été ajouté avec succès."
            )

            from django.shortcuts import redirect

            return redirect("portail_renseignements")

        # Si le formulaire n'est pas valide, on réaffiche la page avec les erreurs
        context = self.get_context_data()
        context["form"] = form
        return self.render_to_response(context)


# Vue fonction pour compatibilité avec urls.py
ajout = AjouterIndividu.as_view()
