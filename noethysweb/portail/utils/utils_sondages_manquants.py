from core.models import Sondage, SondageRepondant, Rattachement, Inscription


def Get_sondages_manquants(famille=None):
    """
    Retourne la liste des sondages (formulaires) que la famille n'a pas encore complétés.

    La liste peut être retrouvé en trouvant tous les structures de la famille et en choppant tous les sondages de la structure qui ont le bon type de public.

    Retourne une liste de dictionnaires avec les informations sur chaque sondage manquant.
    """
    if not famille:
        return []

    sondages_manquants = []

    # Récupérer toutes les structures auxquelles la famille est rattachée via ses inscriptions
    inscriptions = Inscription.objects.select_related('activite', 'activite__structure').filter(famille=famille)
    structure_ids = inscriptions.values_list('activite__structure', flat=True).distinct()

    # Récupérer tous les sondages actifs pour ces structures
    sondages = Sondage.objects.filter(structure__in=structure_ids, structure__visible=True)

    # Récupérer tous les répondants existants pour cette famille
    repondants_existants = SondageRepondant.objects.filter(famille=famille)

    # Créer un dictionnaire des réponses existantes pour un accès rapide
    # Pour les sondages de type "famille" : {idsondage: True}
    # Pour les sondages de type "individu" : {idsondage: {idindividu: True}}
    dict_reponses_famille = {}
    dict_reponses_individu = {}

    for repondant in repondants_existants:
        if repondant.sondage.public == "famille":
            dict_reponses_famille[repondant.sondage.idsondage] = True
        else:  # type "individu"
            if repondant.sondage.idsondage not in dict_reponses_individu:
                dict_reponses_individu[repondant.sondage.idsondage] = set()
            if repondant.individu_id:
                dict_reponses_individu[repondant.sondage.idsondage].add(repondant.individu_id)

    # Récupérer les rattachements de la famille (individus non décédés)
    rattachements = Rattachement.objects.select_related('individu').filter(
        famille=famille,
        individu__deces=False
    )

    # Parcourir tous les sondages et vérifier s'ils sont complétés
    for sondage in sondages:
        if sondage.public == "famille":
            # Sondage de type famille : vérifier si une réponse existe
            if sondage.idsondage not in dict_reponses_famille:
                sondages_manquants.append({
                    'sondage': sondage,
                    'titre': sondage.titre,
                    'code': sondage.code,
                    'type': 'famille',
                    'article': None,  # Pour compatibilité avec le template
                    'individu': None,
                })

        else:  # public == "individu"
            # Sondage de type individu : vérifier pour chaque individu concerné
            # Filtrer les rattachements selon les catégories définies dans le sondage
            rattachements_concernes = rattachements
            if sondage.categories_rattachements:
                # categories_rattachements est un MultiSelectField qui retourne une liste
                categories = [int(cat) for cat in sondage.categories_rattachements]
                rattachements_concernes = [r for r in rattachements if r.categorie in categories]

            # Vérifier pour chaque individu concerné
            for rattachement in rattachements_concernes:
                individu = rattachement.individu

                # Vérifier si cet individu a déjà répondu à ce sondage
                reponses_sondage = dict_reponses_individu.get(sondage.idsondage, set())
                if individu.pk not in reponses_sondage:
                    sondages_manquants.append({
                        'sondage': sondage,
                        'titre': sondage.titre,
                        'code': sondage.code,
                        'type': 'individu',
                        'article': None,  # Pour compatibilité avec le template
                        'individu': individu,
                    })

    return sondages_manquants
