# -*- coding: utf-8 -*-
#  Copyright (c) 2019-2021 Ivan LUCAS.
#  Noethysweb, application de gestion multi-activités.
#  Distribué sous licence GNU GPL.

import json, time
from django.http import JsonResponse
from django.views.generic import TemplateView
from core.views.base import CustomView
from core.utils import utils_dates
from comptabilite.forms.edition_justifs import Formulaire
import io
from datetime import datetime
from django.template.loader import render_to_string
from django.conf import settings
from django.core.files.storage import default_storage
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from core.models import ComptaOperation
from django.utils.html import strip_tags
from django.core.files.base import ContentFile
from PIL import Image  # Pour traiter l'image (si nécessaire)



def Generer_pdf(request):
    # Récupérer les options du formulaire
    form = Formulaire(request.POST, request=request)
    if not form.is_valid():
        return JsonResponse({"erreur": "Veuillez compléter les paramètres"}, status=401)
    options = form.cleaned_data


    # Récupération des paramètres de la période
    date_debut = utils_dates.ConvertDateENGtoDate(options["periode"].split(";")[0])
    date_fin = utils_dates.ConvertDateENGtoDate(options["periode"].split(";")[1])
    options["periode"] = (date_debut, date_fin)

    # Récupérer le compte sélectionné
    compte = options["compte"]
    compte_id = compte.idcompte
    compte_label = compte.nom

    if not compte:
        return JsonResponse({"erreur": "Compte non trouvé."}, status=404)

    # Récupérer toutes les opérations dans la période donnée pour ce compte
    operations = ComptaOperation.objects.filter(compte_id=compte_id, date__gte=date_debut, date__lte=date_fin, document__isnull=False).exclude(document='').order_by('num_piece')
    print(operations)
    if not operations:
        return JsonResponse({"erreur": "Aucune opération avec document pour cette période."}, status=404)

    # Créer un fichier PDF en mémoire
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # Définir les dimensions de la page A4
    largeur, hauteur = A4

    # Page de garde
    c.setFont("Helvetica-Bold", 20)
    titre = f"Justificatifs compte {compte_id}"
    titre_width = c.stringWidth(titre, "Helvetica-Bold", 20)
    c.drawString((largeur - titre_width) / 2, hauteur - 100, titre)  # Centrer le titre

    # Sous-titre : Structure
    c.setFont("Helvetica", 14)
    structure_nom = compte.structure.nom if compte.structure else "Structure inconnue"
    structure_width = c.stringWidth(structure_nom, "Helvetica", 14)
    structure = f"Structure : {structure_nom}"
    c.drawString((largeur - c.stringWidth(structure, "Helvetica", 12)) / 2, hauteur - 150, structure)

    # Sous-titre : Période
    c.setFont("Helvetica", 12)
    periode = f"Période : {date_debut.strftime('%d/%m/%Y')} - {date_fin.strftime('%d/%m/%Y')}"
    c.drawString((largeur - c.stringWidth(periode, "Helvetica", 12)) / 2, hauteur - 200, periode)

    # Ajouter une page pour la page de garde
    c.showPage()

    # Pages des justificatifs
    for operation in operations:
        # Titre des pages suivantes : N° de pièce et Libellé
        titre = f"N° de pièce : {operation.num_piece} - {operation.libelle}"
        c.setFont("Helvetica-Bold", 16)
        titre_width = c.stringWidth(titre, "Helvetica-Bold", 16)
        c.drawString((largeur - titre_width) / 2, hauteur - 100, titre)  # Centrer le titre

        # Sous-titre : Date de l'opération
        c.setFont("Helvetica", 12)
        date_op = f"Date : {operation.date.strftime('%d/%m/%Y')}"
        c.drawString((largeur - c.stringWidth(date_op, "Helvetica", 12)) / 2, hauteur - 150, date_op)

        if operation.document:
            # Récupérer le chemin absolu du fichier
            document_url = operation.document.name  # Récupère le chemin relatif (compta_operations/xxx.jpg)
            document_path = default_storage.path(
                document_url)  # Utilise default_storage pour obtenir le chemin absolu du fichier

            print(f"Chemin absolu du fichier : {document_path}")  # Pour vérifier le chemin

            # Si le document est une image, on peut l'intégrer dans le PDF
            if document_url.lower().endswith(('jpg', 'jpeg', 'png', 'gif')):
                # Charger l'image
                image_path = default_storage.path(document_url)  # Récupérer le chemin absolu du fichier
                print(image_path)
                try:
                    img = Image.open(image_path)  # Utiliser PIL pour charger l'image
                    img_width, img_height = img.size  # Obtenir la taille de l'image
                except Exception as e:
                    img_width, img_height = 0, 0  # Si l'image ne peut pas être chargée, ignorer l'image

                # Définir une taille maximale pour l'image
                max_width = 500  # Largeur maximale de l'image dans le PDF
                max_height = 800  # Hauteur maximale de l'image dans le PDF

                # Calculer le ratio de redimensionnement pour l'image
                if img_width > max_width or img_height > max_height:
                    ratio = min(max_width / img_width, max_height / img_height)
                    img_width = int(img_width * ratio)
                    img_height = int(img_height * ratio)

                # Ajouter l'image dans le PDF
                if img_width > 0 and img_height > 0:
                    c.drawImage(image_path, 50, hauteur - 200 - img_height, width=img_width, height=img_height)

        # Ajouter la page et passer à la suivante
        c.showPage()

        # Sauvegarder le PDF dans le buffer
    c.save()

        # Convertir le contenu du buffer en un fichier Django avec ContentFile
    pdf_content = ContentFile(buffer.getvalue())

        # Vérifier si le fichier existe déjà
    filename = f"justifs_compta/justificatifs_compte_{compte_id}_{date_debut.strftime('%Y%m%d')}_{date_fin.strftime('%Y%m%d')}.pdf"

        # Vérifier si le fichier existe déjà
    if default_storage.exists(filename):
            # Si le fichier existe déjà, on le remplace par le nouveau
            default_storage.delete(filename)  # On supprime l'ancien fichier
            print(f"Le fichier {filename} existe déjà. Il va être remplacé.")

        # Sauvegarder le nouveau fichier
    file_path = default_storage.save(filename, pdf_content)

        # Retourner le nom du fichier généré pour permettre à l'utilisateur de le télécharger
    time.sleep(1)  # Simuler un léger délai pour la génération du fichier
    return JsonResponse({"nom_fichier": file_path})



class View(CustomView, TemplateView):
    menu_code = "edition_justifs"
    template_name = "comptabilite/edition_justifs.html"

    def get_context_data(self, **kwargs):
        context = super(View, self).get_context_data(**kwargs)
        context['page_titre'] = "Edition PDF des justificatifs"
        context['box_titre'] = ""
        context['box_introduction'] = "Renseignez les paramètres et cliquez sur le bouton Générer le PDF. La génération du document peut nécessiter quelques instants d'attente."
        if "form" not in kwargs:
            context['form'] = Formulaire(request=self.request)
        return context
