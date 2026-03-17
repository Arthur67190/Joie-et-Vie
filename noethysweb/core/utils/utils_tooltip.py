# -*- coding: utf-8 -*-


def Get_html_with_tooltip(text, tooltip_text=None, icon_class='fa fa-info-circle', icon_color='text-info'):
    """
    Génère un HTML avec texte et tooltip au survol.
    
    Args:
        text (str|int): Le texte à afficher
        tooltip_text (str): Le texte du tooltip (optionnel)
        icon_class (str): Classes CSS pour l'icône
        icon_color (str): Classe de couleur pour l'icône
        
    Returns:
        str: HTML formaté avec le texte et l'icône avec tooltip si fourni
    """
    if not tooltip_text:
        return str(text)
    
    return f'{text} <i class="{icon_class} {icon_color}" style="cursor:pointer;" data-toggle="tooltip" data-html="true" title="{tooltip_text}"></i>'
