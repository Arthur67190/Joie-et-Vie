# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django.urls import reverse_lazy, reverse
from core.views.mydatatableview import MyDatatable, columns, helpers
from core.views import crud
from core.models import Structure
from parametrage.forms.structures import Formulaire
from django.db.models import Q, Count


class Page(crud.Page):
    model = Structure
    url_liste = "structures_liste"
    url_ajouter = "structures_ajouter"
    url_modifier = "structures_modifier"
    url_supprimer = "structures_supprimer"
    description_liste = "Voici ci-dessous la liste des structures. Les structures ne peuvent être modifiées ou supprimées que par un super-utilisateur ou par un utilisateur habilité."
    description_saisie = "Saisissez toutes les informations concernant la structure à saisir et cliquez sur le bouton Enregistrer."
    objet_singulier = "une structure"
    objet_pluriel = "des structures"
    boutons_liste = [
        {"label": "Ajouter", "classe": "btn btn-success", "href": reverse_lazy(url_ajouter), "icone": "fa fa-plus"},
    ]
    compatible_demo = False


class Liste(Page, crud.Liste):
    model = Structure

    def get_queryset(self):
        return Structure.objects_all.filter(self.Get_filtres("Q")).annotate(nbre_activites=Count('activite'))

    def get_context_data(self, **kwargs):
        context = super(Liste, self).get_context_data(**kwargs)
        context['impression_introduction'] = ""
        context['impression_conclusion'] = ""
        context['afficher_menu_brothers'] = True
        return context

    class datatable_class(MyDatatable):
        filtres = ['idstructure', 'nom']
        actions = columns.TextColumn("Actions", sources=None, processor='Get_actions_speciales')
        nbre_activites = columns.TextColumn("Activités associées", sources="nbre_activites")
        visible = columns.TextColumn("Visible sur le portail", sources="visible", processor='Format_visible')


        class Meta:
            structure_template = MyDatatable.structure_template
            columns = ['idstructure', 'nom', 'nbre_activites', 'visible']
            ordering = ['nom']

        def Get_actions_speciales(self, instance, *args, **kwargs):
            view = kwargs["view"]
            html = []
            if instance.actif and view.request.user.is_superuser or instance in view.request.user.structures.all():
                # Affiche les boutons d'action si l'utilisateur est associé à la structure
                html = [
                    self.Create_bouton_modifier(url=reverse(view.url_modifier, args=[instance.pk])),
                    self.Create_bouton_supprimer(url=reverse(view.url_supprimer, args=[instance.pk])),
                ]
            # --- Bouton archiver / désarchiver ---
            if instance.actif:
                label = ""
                css = "btn-warning"
                icon = "fa fa-archive"
                url_proc = reverse("structure_toggle_archive", args=[instance.pk])
                help_text = "Archiver la structure"
            else:
                label = ""
                css = "btn-success"
                icon = "fa fa-folder-open"
                url_proc = reverse("desarchive_toggle_archive_structure", args=[instance.pk])
                help_text = "Désarchiver la structure"

            bouton_archive = f'''
            <a href="{url_proc}" class="btn {css} btn-sm" title="{help_text}">
                <i class="{icon}"></i> {label}
            </a>
            '''
            html.append(bouton_archive)
            return self.Create_boutons_actions(html)

        def Format_visible(self, instance, *args, **kwargs):
            return "Oui" if instance.visible else "Non"

class Ajouter(Page, crud.Ajouter):
    form_class = Formulaire
    def form_valid(self, form):
            # Enregistre d'abord la structure
            redirect = super(Ajouter, self).form_valid(form)
            # Associe la structure à l'utilisateur qui vient de la créer
            self.request.user.structures_admin.add(form.instance)
            self.request.user.structures.add(form.instance)
            return redirect

class Modifier(Page, crud.Modifier):
    form_class = Formulaire

class Supprimer(Page, crud.Supprimer):
    pass
