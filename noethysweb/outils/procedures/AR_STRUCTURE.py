import logging
from outils.views.procedures import BaseProcedure
from core.models import Activite, Structure
from django.db.models import F, Value
from django.db.models.functions import Concat

logger = logging.getLogger(__name__)


class Procedure(BaseProcedure):

    def Arguments(self, parser=None):
        pass

    def Executer(self, variables=None):
        try:
            structure_id = variables.get('structure')
            if not structure_id:
                return "Aucune structure sélectionnée."

            # --- Récupération de la structure ---
            try:
                structure = Structure.objects.get(idstructure=structure_id.idstructure)
            except Structure.DoesNotExist:
                return "La structure fournie n'existe pas."

            # --- Archivage de la structure ---
            if not structure.nom.startswith("ARCHIVE - "):
                structure.nom = f"ARCHIVE - {structure.nom}"
            structure.actif = False
            structure.save()

            # --- Archivage des activités liées ---
            activites_qs = Activite.objects_all.filter(
                structure=structure,
                actif=True,
            )

            nb_activites = activites_qs.update(
                actif=False,
                nom=Concat(Value("ARCHIVE - "), F("nom")),
                visible=False
            )

            return (
                f"Structure archivée.\n"
                f"{nb_activites} activité(s) archivée(s)."
            )

        except Exception as e:
            logger.exception("Erreur lors de l'archivage")
            return f"Une erreur est survenue : {str(e)}"
