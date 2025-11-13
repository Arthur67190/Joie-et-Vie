# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from core.models import Structure


class FormulaireBase():
    def __init__(self, *args, **kwargs):
        if not hasattr(self, "request"):
            self.request = kwargs.pop("request", None)
        self.mode = kwargs.pop("mode", None)
        super(FormulaireBase, self).__init__(*args, **kwargs)

        if self.request:
            champ = self.fields.get("structure")
            if champ:
                if self.request.user.is_superuser:
                    champ.required = False
                    champ.queryset = Structure.objects.order_by("nom")
                    champ.empty_label = "Toutes les structures"
                else:
                    champ.required = True  # ici tu rends le champ obligatoire
                    champ.queryset = self.request.user.structures.filter(visible=True).order_by("nom")

        # Envoi du request dans le widget activites pour effectuer un filtre sur les structures accessibles
        if self.request and "activites" in self.fields:
            self.fields["activites"].widget.request = self.request


    def Set_mode_consultation(self):
        # Désactive les champs en mode consultation
        for nom, field in self.fields.items():
            field.disabled = True
            field.help_text = None
