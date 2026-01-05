# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

import logging, datetime
logger = logging.getLogger(__name__)
from portail.views.base import CustomView
from django.views.generic import TemplateView
from django.utils.translation import gettext as _
from core.models import Structure, PortailMessage, Inscription, Activite
from django.db.models import Q, Count


class View(CustomView, TemplateView):
    menu_code = "portail_contact"
    template_name = "portail/contact.html"

    def get_context_data(self, **kwargs):
        context = super(View, self).get_context_data(**kwargs)
        context['page_titre'] = _("Contact")

        # Récupération des activités avec inscription
        inscriptions = Inscription.objects.filter(famille=self.request.user.famille)
        activites_avec_inscription = list(set(inscription.activite for inscription in inscriptions))

        # Filtrer les structures liées aux activités avec inscription
        liste_structures = Structure.objects.filter(activite__in=activites_avec_inscription).distinct().order_by("nom")

        # Structures avec messagerie
        context['liste_structures_messagerie'] = [structure for structure in liste_structures]

        # Structures avec coordonnées
        context['liste_structures_coords'] = [structure for structure in liste_structures if structure.afficher_coords]

        context['structure_all'] = Structure.objects.filter(visible=True).order_by('nom')

        # Importation du nombre de messages non lus (regroupement par structure)
        context['dict_messages_non_lus'] = {valeur["structure"]: valeur["nbre"] for valeur in PortailMessage.objects.values("structure").filter(famille=self.request.user.famille, utilisateur__isnull=False, date_lecture__isnull=True).annotate(nbre=Count('pk'))}

        # Récupérer l'idstructure sélectionné depuis l'URL (optionnel)
        idstructure = self.kwargs.get("idstructure", None)
        if idstructure:
            context['structure'] = Structure.objects.get(pk=idstructure)
            context['liste_messages_discussion'] = PortailMessage.objects.select_related("famille", "structure", "utilisateur").filter(famille=self.request.user.famille, structure_id=idstructure).order_by("date_creation")

            # Marquer les messages non lus de cette structure comme lus
            PortailMessage.objects.filter(famille=self.request.user.famille, structure_id=idstructure, utilisateur__isnull=False, date_lecture__isnull=True).update(date_lecture=datetime.datetime.now())
        else:
            context['liste_messages_discussion'] = []

        return context
