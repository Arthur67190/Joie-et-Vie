# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django.urls import reverse_lazy, reverse
from core.views.mydatatableview import MyDatatable, columns, helpers
from core.views import crud
from core.models import Inscription, Prestation
from fiche_individu.forms.individu_inscriptions import Formulaire
from django.db.models import Q


class Page(crud.Page):
    model = Inscription
    url_liste = "inscriptions_liste"
    url_modifier = "inscriptions_modifier"
    url_supprimer = "inscriptions_supprimer"
    url_supprimer_plusieurs = "inscriptions_supprimer_plusieurs"
    description_liste = "Voici ci-dessous la liste des inscriptions. Vous ne pouvez accéder qu'aux inscriptions associées à vos structures. ATTENTION ! Supprimer une inscription ne supprime pas les prestations liées !"
    description_saisie = "Saisissez toutes les informations concernant l'inscription à saisir et cliquez sur le bouton Enregistrer."
    objet_singulier = "une inscription"
    objet_pluriel = "des inscriptions"


class Liste(Page, crud.Liste):
    model = Inscription

    def get_queryset(self):
        condition = Q(activite__structure__in=self.request.user.structures.all())
        return Inscription.objects.select_related("famille", "individu", "groupe", "categorie_tarif", "activite", "activite__structure").filter(self.Get_filtres("Q"), condition)

    def get_context_data(self, **kwargs):
        context = super(Liste, self).get_context_data(**kwargs)
        context["impression_introduction"] = ""
        context["impression_conclusion"] = ""
        context["afficher_menu_brothers"] = True
        context["active_checkbox"] = True
        return context

    class datatable_class(MyDatatable):
        filtres = ["ipresent:individu", "fpresent:famille", "idinscription", "famille__nom", "activite:activite", "groupe__nom", "statut"]
        check = columns.CheckBoxSelectColumn(label="")
        actions = columns.TextColumn("Actions", sources=None, processor="Get_actions_speciales")
        activite = columns.TextColumn("Activité", sources=["activite__nom"])
        groupe = columns.TextColumn("Groupe", sources=["groupe__nom"])
        individu = columns.CompoundColumn("Individu", sources=["individu__nom", "individu__prenom"])
        famille = columns.TextColumn("Famille", sources=["famille__nom"])
        tarif = columns.TextColumn("Tarifs", processor='format_tarif')
        individu_ville = columns.TextColumn("Ville de l'individu", processor="Get_ville_individu")
        famille_ville = columns.TextColumn("Ville de la famille", processor="Get_ville_famille")
        mail_famille = columns.TextColumn("Email famille", processor='Get_mail_famille')

        class Meta:
            structure_template = MyDatatable.structure_template
            columns = ["check", "idinscription", "date_debut", "individu", "famille", "activite", "groupe", "tarif", "individu_ville", "famille_ville", "mail_famille", "statut"]
            hidden_columns = ["famille_ville", "mail_famille"]
            processors = {
                "date_debut": helpers.format_date("%d/%m/%Y"),
                "statut": "Formate_statut",
            }
            labels = {
                "date_debut": "Date d'inscription",
            }
            ordering = ["individu"]

        def format_tarif(self, instance, *args, **kwargs):
            tarifs = instance.tarifs.all()
            descriptions = [tarif.description for tarif in tarifs]
            result = ' // '.join(descriptions)
            return result

        def Formate_statut(self, instance, *args, **kwargs):
            if instance.statut == "attente":
                return "<i class='fa fa-hourglass-2 text-yellow'></i> Attente"
            elif instance.statut == "refus":
                return "<i class='fa fa-times-circle text-red'></i> Refus"
            else:
                return "<i class='fa fa-check-circle-o text-green'></i> Valide"

        def Get_actions_speciales(self, instance, *args, **kwargs):
            """Inclut l'idindividu dans les boutons d'actions"""
            view = kwargs["view"]
            # Récupération idindividu et idfamille
            kwargs = view.kwargs
            kwargs["idfamille"] = instance.famille.pk if instance.famille else None
            kwargs["idindividu"] = instance.individu.pk if instance.individu else None
            kwargs["pk"] = instance.pk

            # Actions spécifiques pour la modification
            if instance.activite.structure in view.request.user.structures.all():
                modifier_kwargs = {key: value for key, value in kwargs.items() if key != "pk"}
                modifier_url = reverse(view.url_modifier, kwargs=modifier_kwargs)

                # Boutons pour la modification
                modifier_buttons = [
                    self.Create_bouton_modifier(url=modifier_url),
                ]
            else:
                # Afficher que l'accès est interdit
                modifier_buttons = [
                    "<span class='text-red'><i class='fa fa-minus-circle margin-r-5' title='Accès non autorisé'></i>Accès interdit</span>", ]

            # Actions spécifiques pour la suppression
            supprimer_url = reverse(view.url_supprimer,kwargs={"pk": instance.pk})
            supprimer_button = self.Create_bouton_supprimer(url=supprimer_url)

            # Bouton pour ouvrir la fiche famille
            ouvrir_famille_url = reverse("famille_resume", args=[instance.famille_id])
            ouvrir_famille_button = self.Create_bouton(url=ouvrir_famille_url, title="Ouvrir la fiche famille",
                                                       icone="fa-users")

            # Retourner les boutons correspondants
            return self.Create_boutons_actions(modifier_buttons + [supprimer_button] + [ouvrir_famille_button])

        def Get_ville_individu(self, instance, *args, **kwargs):
            return instance.individu.ville_resid

        def Get_ville_famille(self, instance, *args, **kwargs):
            return instance.famille.ville_resid

        def Get_mail_famille(self, instance, *args, **kwargs):
            return instance.famille.mail


class Ajouter(Page, crud.Ajouter):
    form_class = Formulaire

class Modifier(Page, crud.Modifier):
    form_class = Formulaire
pass

class Supprimer(Page, crud.Supprimer):
    def Check_protections(self, objet=None):
        protections = []

        nbre_prestations_facturees = Prestation.objects.filter(famille=objet.famille, individu=objet.individu, activite=objet.activite, facture__isnull=False).count()
        if nbre_prestations_facturees:
            protections.append("Vous ne pouvez pas supprimer cette inscription car %s prestations associées sont déjà facturées." % nbre_prestations_facturees)

        nbre_prestations = Prestation.objects.filter(famille=objet.famille, individu=objet.individu, activite=objet.activite).exclude(forfait=2).count()
        if nbre_prestations:
            protections.append("Vous ne pouvez pas supprimer cette inscription car %s prestations sont déjà associées." % nbre_prestations)

        return protections
class Supprimer_plusieurs(Page, crud.Supprimer_plusieurs):

    pass