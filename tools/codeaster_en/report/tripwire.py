"""French tripwire for the rendered report (``docs/REPORT-SPEC.md`` §2).

The Markdown report must contain no French outside code: fenced code blocks (the quoted
``.comm`` and log excerpts) and inline code spans (solver identifiers such as ``GROUP_MA``,
``ACIER``, which are the solver's API or the user's own names; CLAUDE.md rule 2) are exempt.
Everything else is checked for common French function words and engineering terms, and for
French accented letters. Words in capitals without accents are skipped: they are solver
identifiers quoted inside English message text (``SOLVEUR``, ``NPREC``), and raw log lines,
where French capitals would appear, only ever go into fenced code.
"""

from __future__ import annotations

import re

# Function words and engineering terms that do not double as common English words.
FRENCH_WORDS = frozenset(
    """
    le la les des du un une et est sont pour par avec dans sur au aux ce cette ces qui que
    pas ne il elle nous vous ils elles mais ou où moins très entre sans sous été être
    avoir fait faire peut doit chaque tout tous toute toutes aucun aucune alors donc ainsi lors
    selon leur leurs ses notre votre même autre autres déjà encore aussi comme quand
    dont ici voici puis oui afin depuis vers chez contre pendant après avant
    maillage modèle modele modélisation contrainte contraintes déplacement deplacement
    déplacements calcul calculs erreur erreurs alarme alarmes résultat resultat résultats
    champ champs noeud noeuds nœud nœuds maille mailles matériau materiau matériaux chargement
    chargements appui appuis encastrement effort efforts réaction réactions fréquence frequence
    fréquences propre propres valeur valeurs nombre temps mémoire memoire fichier fichiers
    commande commandes groupe groupes élément éléments liberté degrés solveur matrice vecteur
    composante composantes pression poids masse rigidité raideur épaisseur coque coques
    poutre poutres béton acier arrêt début ligne lignes numéro ordre vérification calculé
    calculée imposé imposée imposés répartie nodale nodales cas essai ouverture fermeture
    écriture taille utilisée utilisé maximale minimale requise exécution
    """.split()
)
ACCENTED = re.compile(r"[àâäçéèêëîïôöùûüÿœæÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸŒÆ]")
_FENCE = re.compile(r"^(```|~~~).*?^\1\s*$", re.M | re.S)
_INLINE = re.compile(r"`[^`\n]*`")
_HTML = re.compile(r"<[^>]+>")
_WORD = re.compile(r"[A-Za-zÀ-ÿœŒæÆ]+(?:['’][A-Za-zÀ-ÿ]+)?")


def prose(markdown: str) -> str:
    """The text of a Markdown document with code blocks, code spans and tags removed."""
    text = _FENCE.sub("", markdown)
    text = _INLINE.sub("", text)
    return _HTML.sub("", text)


def french_words(markdown: str) -> list[str]:
    """French words found outside code, in order of appearance (empty when clean)."""
    found = []
    for word in _WORD.findall(prose(markdown)):
        if ACCENTED.search(word):
            found.append(word)
        elif word.isupper() and len(word) > 1:
            continue
        elif word.lower() in FRENCH_WORDS:
            found.append(word)
    return found
