import logging
from outils.views.procedures import BaseProcedure
from core.models import Article, Activite, Structure, PortailDocument, SignatureEmail, Album, ModeleDocument, QuestionnaireQuestion
from django.db.models import F, Value
from django.db.models.functions import Concat

logger = logging.getLogger(__name__)


class Procedure(BaseProcedure):
    def Arguments(self, parser=None):
        # Aucune modification nécessaire ici pour le moment
        pass

    def Executer(self, variables=None):
        try:
            # Vérification que l'activité a été fournie
            activite = variables.get('activite')

            if not activite:
                return "Aucune activité sélectionnée."

            # Assurer que `activite` est un seul objet Activite
            if isinstance(activite, Activite):
                activite_id = activite.idactivite
            else:
                return "L'activité fournie n'est pas valide."

            # Récupérer les structures associées à l'activité
            structures = Structure.objects.filter(activite=activite_id)

            # Articles
            articles_modifies = Article.objects.filter(
                activites=activite
            ).update(structure=12, statut='non_publie')

            # Questionnaires
            questionnaires_modifiés = QuestionnaireQuestion.objects.filter(
                activites=activite
            ).update(structure=12)

            # Album
            album_modifies = Album.objects.filter(
                structure__in=structures,
                article__activite__in=activites
            ).update(structure=12)

            # Documents
            strucdocument_modifies = PortailDocument.objects.filter(
                activites=activite
            ).update(structure=12)

            actdocument_modifies = PortailDocument.objects.filter(
                structure=12
            )

            # Renommage Activité
            activite_statut = Activite.objects.filter(
                idactivite=activite_id
            ).update(visible=False, nom=Concat(Value('ARCHIVE - '), F('nom')), structure=12)

            # Mise à jour des documents associés
            for doc in actdocument_modifies:
                doc.activites.set([23])

            structures.delete()

            return (
                f"Nombre d'articles modifiés : {articles_modifies}, "
                f"Nombre de questionnaires modifiés : {questionnaires_modifiés}, "
                f"Nombre de documents modifiés : {strucdocument_modifies}, "
                f"Nombre d'albums modifiés : {album_modifies}, "
            )

        except Exception as e:
            logger.error(f"Une erreur est survenue : {str(e)}")
            return f"Une erreur est survenue : {str(e)}"
