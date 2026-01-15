# -*- coding: utf-8 -*-
import logging
from outils.views.procedures import BaseProcedure
from core.models import Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Utilisateur
from utils import utils_permissions  # là où est GetPermissionsPossibles

logger = logging.getLogger(__name__)


class Procedure(BaseProcedure):
    """
    Procédure pour créer/forcer toutes les permissions "menu" définies
    par GetPermissionsPossibles, sans les assigner aux utilisateurs.
    """

    def Arguments(self, parser=None):
        # Pas d'arguments nécessaires ici
        pass

    def Executer(self, variables=None):
        # ContentType pour le modèle Utilisateur
        ct = ContentType.objects.get_for_model(Utilisateur)

        # Récupération des permissions possibles
        liste_permissions = utils_permissions.GetPermissionsPossibles()
        created_count = 0
        updated_count = 0

        for codename, name in liste_permissions:
            perm, created_flag = Permission.objects.get_or_create(
                codename=codename,
                content_type=ct,
                defaults={"name": name}
            )
            if created_flag:
                created_count += 1
                logger.info(f"Permission créée : {name} ({codename})")
            elif perm.name != name:
                perm.name = name
                perm.save()
                updated_count += 1
                logger.info(f"Permission mise à jour : {name} ({codename})")

        msg = (
            f"{len(liste_permissions)} permissions vérifiées : "
            f"{created_count} créées, {updated_count} mises à jour."
        )
        logger.info(msg)
        return msg
