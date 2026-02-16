# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

from django.contrib.auth.forms import AuthenticationForm
from django.forms import ValidationError
from turnstile.fields import TurnstileField


class FormLoginUtilisateur(AuthenticationForm):
    turnstile = TurnstileField()

    def __init__(self, *args, **kwargs):
        super(FormLoginUtilisateur, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = "form-control"
        self.fields['username'].widget.attrs['placeholder'] = "Utilisateur"
        self.fields['password'].widget.attrs['class'] = "form-control"
        self.fields['password'].widget.attrs['placeholder'] = "Mot de passe"
