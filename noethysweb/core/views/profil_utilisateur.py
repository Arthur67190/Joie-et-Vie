# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

import logging, time
logger = logging.getLogger(__name__)
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib import messages
from core.views.base import CustomView
from core.forms.profil import FormSignature


def Purger_filtres_listes(request):
    """ Supprime tous les filtres de listes de l'utilisateur """
    time.sleep(2)
    from core.models import FiltreListe
    FiltreListe.objects.filter(utilisateur=request.user).delete()
    messages.add_message(request, messages.SUCCESS, "Tous les filtres de listes de l'utilisateur ont été supprimés")
    return JsonResponse({"url": reverse_lazy("profil_utilisateur")})


class View(CustomView, TemplateView):
    menu_code = "accueil"
    template_name = "core/profil.html"
    compatible_demo = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_titre'] = "Profil"
        context['box_titre'] = "Profil de l'utilisateur"
        context['box_introduction'] = ""

        # Ajouter le formulaire signature
        form = FormSignature(instance=self.request.user)
        context['form_signature'] = form

        return context

    def post(self, request, *args, **kwargs):
        # Si le POST contient un fichier ou un champ signature, on traite la signature
        if 'signature_image' in request.FILES or 'signature' in request.POST:
            form = FormSignature(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Votre signature a été enregistrée avec succès.")
            else:
                messages.error(request, "Erreur lors de l'enregistrement de la signature.")

        # Si le POST contient des structures
        if 'structures' in request.POST:
            structures_ids = request.POST.getlist("structures")
            if structures_ids:
                allowed = request.user.structures_admin.filter(idstructure__in=structures_ids)
                request.user.structures.set(allowed)
            else:
                request.user.structures.clear()
            messages.success(request, "Le filtre des structures a été mis à jour.")

        return self.get(request, *args, **kwargs)

