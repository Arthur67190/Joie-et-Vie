# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

import datetime
from django.contrib.auth.forms import AuthenticationForm
from django.forms import ValidationError
from django.utils.translation import gettext as _
from turnstile.fields import TurnstileField


class FormLoginFamille(AuthenticationForm):
    turnstile = TurnstileField()

    def __init__(self, *args, **kwargs):
        super(FormLoginFamille, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = "form-control"
        self.fields['username'].widget.attrs['placeholder'] = _("Identifiant")
        self.fields['password'].widget.attrs['class'] = "form-control"
        self.fields['password'].widget.attrs['placeholder'] = _("Mot de passe")

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise ValidationError(_("Ce compte a été désactivé"), code='inactive')
        if user.date_expiration_mdp and user.date_expiration_mdp < datetime.datetime.now():
            raise ValidationError(_("Ce mot de passe a expiré"), code='mdp_expire')
