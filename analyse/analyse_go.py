"""
INF6253 - Projet P2 : Analyse comparative Gene Ontology
-------------------------------------------------------
Partie 1 du projet - tâches 1, 2 et 3 :

  Tâche 1 — Structure générale (par version) :
    - Nombre de triplets (approximation du nombre d'axiomes)
    - Nombre de classes totales, actives, dépréciées
    - Nombre de propriétés objet et d'annotation
    - Nombre d'axiomes OWL explicites (subClassOf, equivalentClass, disjointWith,
      restrictions someValuesFrom, owl:Axiom)

  Tâche 2 — Analyse quantitative (domaine apoptose) :
    - Nombre de classes dans chaque version
    - Nombre de classes nouvelles (v2 - v1)
    - Nombre de classes dépréciées (owl:deprecated true)
    - Nombre de classes dont la hiérarchie a changé (parents différents)

  Tâche 3 — Analyse qualitative (5 termes) :
    - Comparaison des définitions (IAO:0000115 ET rdfs:comment)
    - Comparaison de la position dans la hiérarchie (rdfs:subClassOf)
    - Identification des changements de relations (part_of, regulates, etc.)

Ce module ne charge aucun fichier OWL.
Il reçoit les graphes prêts depuis main.py via le dict retourné par
traitement_go.charger_et_preparer().

Rapports générés dans analyse/reports/ :
  - structure_oct2025.txt
  - structure_jan2026.txt
  - rapport_quantitatif.txt
  - rapport_qualitatif.txt
"""

import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

try:
    from rdflib import Graph, URIRef, Literal, BNode
    from rdflib.namespace import RDF, RDFS, OWL
except ImportError:
    print("rdflib manquant. Installez-le avec : pip install rdflib")
    sys.exit(1)

from traitement_go import (
    REPORTS_DIR,
    ROOT_ID,
    DEFINITION,
    IS_DEPRECATED,
    PART_OF,
    REGULATES,
    POS_REGULATES,
    NEG_REGULATES,
    OBO,
    uri,
    go_id_from_uri,
    log_progress,
)

# 5 termes pour l'analyse qualitative (tâche 3)
QUAL_TERMS = [
    "GO:0006915",  # apoptotic process
    "GO:0008625",  # extrinsic apoptotic signaling pathway via death domain receptors
    "GO:0043065",  # positive regulation of apoptotic process
    "GO:0043066",  # negative regulation of apoptotic process
    "GO:0097194",  # execution phase of apoptosis
]


# ─── Journalisation vers fichier ──────────────────────────────────────────────
class FileLogger:
    """
    Redirige les appels print() vers un fichier texte uniquement.
    S'utilise comme gestionnaire de contexte : with FileLogger(path).
    La console n'est pas affectée : utiliser log_progress() pour la progression.
    """

    def __init__(self, filepath: Path):
        self._stdout = sys.stdout
        self.file    = open(filepath, "w", encoding="utf-8")

    def write(self, message: str):
        self.file.write(message)

    def flush(self):
        self.file.flush()

    def close(self):
        self.file.close()
        sys.stdout = self._stdout

    def __enter__(self):
        sys.stdout = self
        return self

    def __exit__(self, *args):
        self.close()


# ─── Utilitaires RDF ─────────────────────────────────────────────────────────
def get_label(g: Graph, term_uri) -> str:
    """
    Retourne le label rdfs:label d'un terme GO.
    Retourne '(?)' si aucun label n'est défini.
    """
    lbl = g.value(term_uri, RDFS.label)
    return str(lbl) if lbl else "(?)"


def get_definition(g: Graph, term_uri) -> tuple[str, str]:
    """
    Retourne un tuple (source, texte) pour la définition d'un terme GO.

    Cherche dans l'ordre :
      1. IAO:0000115 — définition officielle OBO (source = "IAO:0000115")
      2. rdfs:comment — commentaire RDFS en fallback (source = "rdfs:comment")

    Retourne ("(aucune definition)", "") si aucune n'est trouvée.
    Retourner la source permet au rapport d'indiquer d'où vient la définition,
    conformément à la tâche 3 qui mentionne explicitement rdfs:comment.
    """
    defn = g.value(term_uri, DEFINITION)
    if defn:
        return "IAO:0000115", str(defn)
    comment = g.value(term_uri, RDFS.comment)
    if comment:
        return "rdfs:comment", str(comment)
    return "(aucune definition)", ""


def is_deprecated(g: Graph, term_uri) -> bool:
    """
    Retourne True si le terme est marqué owl:deprecated true.
    """
    dep = g.value(term_uri, IS_DEPRECATED)
    return dep == Literal(True)


def get_parents(g: Graph, term_uri) -> set:
    """
    Retourne les parents directs (is_a) via rdfs:subClassOf.
    Exclut les blank nodes (restrictions OWL someValuesFrom).
    """
    return {
        parent for parent in g.objects(term_uri, RDFS.subClassOf)
        if isinstance(parent, URIRef)
    }


def get_relations(g: Graph, term_uri) -> dict:
    """
    Extrait les relations sémantiques OBO d'un terme GO.

    Dans go-base.owl, les relations part_of, regulates, etc. sont encodées
    comme des restrictions OWL blank nodes :
      T rdfs:subClassOf [ owl:onProperty P ; owl:someValuesFrom C ]

    Retourne {nom_relation: {set d'URIRef cibles}}.
    """
    relations = defaultdict(set)
    REL_MAP = {
        str(PART_OF):       "part_of",
        str(REGULATES):     "regulates",
        str(POS_REGULATES): "positively_regulates",
        str(NEG_REGULATES): "negatively_regulates",
    }
    for bnode in g.objects(term_uri, RDFS.subClassOf):
        if not isinstance(bnode, URIRef):
            prop   = g.value(bnode, OWL.onProperty)
            filler = g.value(bnode, OWL.someValuesFrom)
            if prop and filler and isinstance(filler, URIRef):
                rel_name = REL_MAP.get(str(prop), str(prop).split("/")[-1])
                relations[rel_name].add(filler)
    return dict(relations)


def compter_axiomes(g: Graph) -> dict:
    """
    Compte les axiomes OWL explicites dans le graphe.

    Le projet demande le "nombre d'axiomes". Dans rdflib, chaque triplet est
    un fait RDF, mais certains triplets représentent des axiomes OWL structurels.
    On distingue ici les catégories pertinentes pour GO :

      - subClassOf     : relations de subsomption (is_a et restrictions)
      - equivalentClass: définitions nécessaires et suffisantes
      - disjointWith   : contraintes de disjonction
      - restrictions   : blank nodes owl:Restriction (someValuesFrom, allValuesFrom)
      - axiomes_annotes: triplets owl:Axiom (annotations de triplets existants)
      - total_triplets : total brut (toutes assertions confondues)

    Retourne un dict avec ces compteurs.
    """
    n_subclassof     = sum(1 for _ in g.triples((None, RDFS.subClassOf,     None)))
    n_equivalent     = sum(1 for _ in g.triples((None, OWL.equivalentClass, None)))
    n_disjoint       = sum(1 for _ in g.triples((None, OWL.disjointWith,    None)))
    n_restrictions   = sum(
        1 for s in g.subjects(RDF.type, OWL.Restriction)
        if isinstance(s, BNode)
    )
    n_axiomes_annotes = sum(1 for _ in g.subjects(RDF.type, OWL.Axiom))

    return {
        "subClassOf":      n_subclassof,
        "equivalentClass": n_equivalent,
        "disjointWith":    n_disjoint,
        "restrictions":    n_restrictions,
        "axiomes_annotes": n_axiomes_annotes,
        "total_triplets":  len(g),
    }


# ─── TÂCHE 1 : Structure générale ────────────────────────────────────────────
def analyse_structure_generale(g: Graph, label: str, report_path: Path) -> dict:
    """
    Tâche 1 du projet : analyse la structure globale d'une version de GO.

    Travaille sur le graphe complet (g_full) pour les métriques globales.

    Métriques calculées :
      - Triplets totaux (toutes assertions)
      - Classes totales / actives / dépréciées
      - Propriétés objet et d'annotation
      - Axiomes OWL détaillés (subClassOf, equivalentClass, disjointWith,
        restrictions, owl:Axiom annotés)

    Retourne un dict de stats réutilisé dans le rapport quantitatif.
    """
    log_progress(f"  Structure generale ({label}) -> {report_path.name}")

    all_classes = {c for c in g.subjects(RDF.type, OWL.Class) if isinstance(c, URIRef)}
    deprecated  = {c for c in all_classes if is_deprecated(g, c)}
    active      = all_classes - deprecated
    obj_props   = set(g.subjects(RDF.type, OWL.ObjectProperty))
    ann_props   = set(g.subjects(RDF.type, OWL.AnnotationProperty))
    axiomes     = compter_axiomes(g)

    with FileLogger(report_path):
        print(f"INF6253 - Structure generale de l'ontologie GO")
        print(f"Version   : {label}")
        print(f"Genere le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        print()

        # Classes et propriétés
        print(f"  CLASSES ET PROPRIETES")
        print(f"  {'Metrique':<35} {'Valeur':>10}")
        print(f"  {'-'*47}")
        print(f"  {'Classes totales':<35} {len(all_classes):>10,}")
        print(f"  {'Classes actives':<35} {len(active):>10,}")
        print(f"  {'Classes deprecices':<35} {len(deprecated):>10,}")
        print(f"  {'Proprietes objet':<35} {len(obj_props):>10,}")
        print(f"  {'Proprietes d annotation':<35} {len(ann_props):>10,}")

        # Axiomes OWL
        print()
        print(f"  AXIOMES OWL")
        print(f"  {'Type d axiome':<35} {'Nombre':>10}")
        print(f"  {'-'*47}")
        print(f"  {'rdfs:subClassOf':<35} {axiomes['subClassOf']:>10,}")
        print(f"  {'owl:equivalentClass':<35} {axiomes['equivalentClass']:>10,}")
        print(f"  {'owl:disjointWith':<35} {axiomes['disjointWith']:>10,}")
        print(f"  {'Restrictions (someValuesFrom)':<35} {axiomes['restrictions']:>10,}")
        print(f"  {'Axiomes annotes (owl:Axiom)':<35} {axiomes['axiomes_annotes']:>10,}")
        print()
        print(f"  {'Triplets totaux (toutes assertions)':<35} {axiomes['total_triplets']:>10,}")

    return {
        "classes_totales":   len(all_classes),
        "classes_actives":   len(active),
        "classes_deprecies": len(deprecated),
        "obj_props":         len(obj_props),
        "ann_props":         len(ann_props),
        "triplets":          axiomes["total_triplets"],
        "axiomes":           axiomes,
    }


# ─── TÂCHE 2 : Analyse quantitative ──────────────────────────────────────────
def analyse_quantitative(g_sub_v1: Graph, g_sub_v2: Graph,
                         domain_v1: set, domain_v2: set,
                         stats_v1: dict, stats_v2: dict,
                         report_path: Path) -> dict:
    """
    Tâche 2 du projet : analyse quantitative comparative sur le domaine apoptose.

    Travaille sur les sous-graphes et les sets de termes déjà extraits par
    traitement_go.py — aucune re-extraction ni rechargement.

    Calcule exactement ce que demande le projet :
      - Nombre de classes dans chaque version (total + actives + dépréciées)
      - Nombre de classes nouvelles (URIs présents en v2 absents en v1)
      - Nombre de classes dépréciées (owl:deprecated true) dans chaque version
      - Nombre de classes dont la hiérarchie a changé (parents directs différents)

    Inclut en tête le recap de la structure globale (tâche 1) pour permettre
    la comparaison côte à côte des deux versions dans un seul document.
    """
    log_progress("  Analyse quantitative ...")

    active_v1     = {t for t in domain_v1 if not is_deprecated(g_sub_v1, t)}
    active_v2     = {t for t in domain_v2 if not is_deprecated(g_sub_v2, t)}
    dep_v1        = domain_v1 - active_v1
    dep_v2        = domain_v2 - active_v2
    nouveaux      = domain_v2 - domain_v1
    supprimes     = domain_v1 - domain_v2
    nouv_dep      = {
        t for t in (domain_v1 & domain_v2)
        if not is_deprecated(g_sub_v1, t) and is_deprecated(g_sub_v2, t)
    }

    log_progress("  Calcul des changements hierarchiques ...")
    hier_changes = [
        t for t in (domain_v1 & domain_v2)
        if get_parents(g_sub_v1, t) != get_parents(g_sub_v2, t)
    ]

    with FileLogger(report_path):
        print(f"INF6253 - Analyse quantitative comparative")
        print(f"Domaine : GO:{ROOT_ID.split('_')[1]} - programmed cell death (apoptose)")
        print(f"Genere le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*65}")

        # Recap structure globale (tâche 1 - comparaison côte à côte)
        print()
        print(f"  STRUCTURE GLOBALE DE L'ONTOLOGIE (recap tache 1)")
        print(f"  {'Metrique':<40} {'Oct 2025':>10}  {'Jan 2026':>10}")
        print(f"  {'-'*64}")
        for k, lbl in [
            ("classes_totales",   "Classes totales"),
            ("classes_actives",   "Classes actives"),
            ("classes_deprecies", "Classes deprecices"),
            ("obj_props",         "Proprietes objet"),
            ("ann_props",         "Proprietes d annotation"),
            ("triplets",          "Triplets totaux"),
        ]:
            print(f"  {lbl:<40} {stats_v1[k]:>10,}  {stats_v2[k]:>10,}")

        # Axiomes côte à côte
        print()
        print(f"  AXIOMES OWL (recap tache 1)")
        print(f"  {'Type d axiome':<40} {'Oct 2025':>10}  {'Jan 2026':>10}")
        print(f"  {'-'*64}")
        for k, lbl in [
            ("subClassOf",      "rdfs:subClassOf"),
            ("equivalentClass", "owl:equivalentClass"),
            ("disjointWith",    "owl:disjointWith"),
            ("restrictions",    "Restrictions OWL"),
            ("axiomes_annotes", "Axiomes annotes (owl:Axiom)"),
        ]:
            print(
                f"  {lbl:<40} {stats_v1['axiomes'][k]:>10,}  "
                f"{stats_v2['axiomes'][k]:>10,}"
            )

        # Tâche 2 : domaine apoptose
        print()
        print(f"  TACHE 2 : DOMAINE APOPTOSE (GO:0012501 et descendants)")
        print(f"  {'Metrique':<40} {'Oct 2025':>10}  {'Jan 2026':>10}")
        print(f"  {'-'*64}")
        print(f"  {'Nb de classes dans le domaine':<40} {len(domain_v1):>10,}  {len(domain_v2):>10,}")
        print(f"  {'Nb de classes actives':<40} {len(active_v1):>10,}  {len(active_v2):>10,}")
        print(f"  {'Nb de classes deprecices':<40} {len(dep_v1):>10,}  {len(dep_v2):>10,}")

        print()
        print(f"  CHANGEMENTS ENTRE LES DEUX VERSIONS")
        print(f"  {'Metrique':<40} {'Nombre':>10}")
        print(f"  {'-'*52}")
        print(f"  {'Nb de classes nouvelles (v2 - v1)':<40} {len(nouveaux):>10,}")
        print(f"  {'Nb de classes supprimees (v1 - v2)':<40} {len(supprimes):>10,}")
        print(f"  {'Nouvelles deprecations (actif -> depr.)':<40} {len(nouv_dep):>10,}")
        print(f"  {'Hierarchie modifiee (parents != )':<40} {len(hier_changes):>10,}")

        # Exemples de nouveaux termes
        if nouveaux:
            print()
            print(f"  EXEMPLES DE CLASSES NOUVELLES (max 5)")
            print(f"  {'-'*52}")
            for t in list(nouveaux)[:5]:
                print(f"  + {go_id_from_uri(t):15s}  {get_label(g_sub_v2, t)}")

        # Exemples de nouvelles dépréciations
        if nouv_dep:
            print()
            print(f"  NOUVELLES DEPRECATIONS (max 5)")
            print(f"  {'-'*52}")
            for t in list(nouv_dep)[:5]:
                print(f"  ! {go_id_from_uri(t):15s}  {get_label(g_sub_v2, t)}")

        # Exemples de changements hiérarchiques
        if hier_changes:
            print()
            print(f"  CLASSES A HIERARCHIE MODIFIEE (max 5)")
            print(f"  {'-'*52}")
            for t in hier_changes[:5]:
                tid = go_id_from_uri(t)
                lbl = get_label(g_sub_v2, t)
                p1  = {go_id_from_uri(p) for p in get_parents(g_sub_v1, t)}
                p2  = {go_id_from_uri(p) for p in get_parents(g_sub_v2, t)}
                print(f"  ~ {tid:15s}  {lbl}")
                print(f"    Parents v1 : {', '.join(sorted(p1)) or '(aucun)'}")
                print(f"    Parents v2 : {', '.join(sorted(p2)) or '(aucun)'}")

    return {
        "nouveaux":     nouveaux,
        "supprimes":    supprimes,
        "nouv_dep":     nouv_dep,
        "hier_changes": set(hier_changes),
    }


# ─── TÂCHE 3 : Analyse qualitative ───────────────────────────────────────────
def analyse_qualitative(g_sub_v1: Graph, g_sub_v2: Graph, report_path: Path):
    """
    Tâche 3 du projet : analyse en profondeur des 5 termes définis dans QUAL_TERMS.

    Pour chaque terme, conformément aux exigences du projet :
      - Comparaison des définitions : cherche IAO:0000115 EN PREMIER,
        puis rdfs:comment en fallback. La source est indiquée dans le rapport.
      - Comparaison de la position dans la hiérarchie (rdfs:subClassOf direct)
      - Identification des changements de relations OBO
        (part_of, regulates, positively_regulates, negatively_regulates)

    Marqueurs dans le rapport : + (ajouté), - (retiré), ~ (modifié).
    """
    log_progress("  Analyse qualitative des 5 termes ...")

    with FileLogger(report_path):
        print(f"INF6253 - Analyse qualitative comparative (tache 3)")
        print(f"Domaine : GO:{ROOT_ID.split('_')[1]} - programmed cell death (apoptose)")
        print(f"Genere le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*65}")
        print()
        print(f"  Propriete de definition consultee : IAO:0000115 (OBO)")
        print(f"  Fallback si absente               : rdfs:comment")
        print(f"  Relations comparees               : part_of, regulates,")
        print(f"                                      positively_regulates,")
        print(f"                                      negatively_regulates")

        for go_raw in QUAL_TERMS:
            t   = uri(go_raw)
            tid = go_id_from_uri(t)

            in_v1 = (t, RDF.type, OWL.Class) in g_sub_v1
            in_v2 = (t, RDF.type, OWL.Class) in g_sub_v2

            print(f"\n{'─'*65}")
            print(f"  Terme : {tid}")
            print(f"{'─'*65}")

            if not in_v1 and not in_v2:
                print(f"  Terme absent des deux versions.")
                continue

            # Label
            lbl = get_label(g_sub_v2, t) if in_v2 else get_label(g_sub_v1, t)
            print(f"  Label     : {lbl}")

            # Statut
            dep_v1    = is_deprecated(g_sub_v1, t) if in_v1 else None
            dep_v2    = is_deprecated(g_sub_v2, t) if in_v2 else None
            status_v1 = "DEPRECIE" if dep_v1 else ("actif" if in_v1 else "absent")
            status_v2 = "DEPRECIE" if dep_v2 else ("actif" if in_v2 else "absent")
            print(f"  Statut    : Oct 2025 = {status_v1}  |  Jan 2026 = {status_v2}")

            # Définitions (IAO:0000115 puis rdfs:comment)
            src_v1, def_v1 = get_definition(g_sub_v1, t) if in_v1 else ("(absent)", "")
            src_v2, def_v2 = get_definition(g_sub_v2, t) if in_v2 else ("(absent)", "")
            texte_v1 = def_v1 if def_v1 else src_v1
            texte_v2 = def_v2 if def_v2 else src_v2

            if texte_v1 == texte_v2:
                print(f"  Definition: INCHANGEE (source : {src_v1})")
                print(f"    \"{texte_v1[:120]}{'...' if len(texte_v1) > 120 else ''}\"")
            else:
                print(f"  Definition: MODIFIEE")
                print(f"    V1 (Oct 2025) [{src_v1}] :")
                print(f"      \"{texte_v1[:100]}{'...' if len(texte_v1) > 100 else ''}\"")
                print(f"    V2 (Jan 2026) [{src_v2}] :")
                print(f"      \"{texte_v2[:100]}{'...' if len(texte_v2) > 100 else ''}\"")

            # Position dans la hiérarchie (rdfs:subClassOf direct)
            p1 = {go_id_from_uri(p): get_label(g_sub_v1, p)
                  for p in get_parents(g_sub_v1, t)} if in_v1 else {}
            p2 = {go_id_from_uri(p): get_label(g_sub_v2, p)
                  for p in get_parents(g_sub_v2, t)} if in_v2 else {}

            if p1 == p2:
                print(f"  Hierarchie: INCHANGEE (rdfs:subClassOf)")
                for pid, plbl in list(p1.items())[:3]:
                    print(f"    is_a -> {pid} ({plbl})")
            else:
                added_parents   = set(p2.keys()) - set(p1.keys())
                removed_parents = set(p1.keys()) - set(p2.keys())
                print(f"  Hierarchie: MODIFIEE (rdfs:subClassOf)")
                for pid, plbl in p1.items():
                    marker = "- " if pid in removed_parents else "  "
                    print(f"    {marker}is_a -> {pid} ({plbl})")
                for pid in added_parents:
                    print(f"    + is_a -> {pid} ({p2[pid]})")

            # Relations sémantiques OBO
            rel_v1   = get_relations(g_sub_v1, t) if in_v1 else {}
            rel_v2   = get_relations(g_sub_v2, t) if in_v2 else {}
            all_rels = set(rel_v1.keys()) | set(rel_v2.keys())

            if rel_v1 == rel_v2:
                if rel_v2:
                    print(f"  Relations : INCHANGEES")
                    for rel, targets in rel_v2.items():
                        for tgt in list(targets)[:2]:
                            print(f"    {rel} -> {go_id_from_uri(tgt)} ({get_label(g_sub_v2, tgt)})")
                else:
                    print(f"  Relations : aucune relation OBO encodee dans ce terme")
            else:
                print(f"  Relations : MODIFIEES")
                for rel in all_rels:
                    kept    = rel_v1.get(rel, set()) & rel_v2.get(rel, set())
                    added   = rel_v2.get(rel, set()) - rel_v1.get(rel, set())
                    removed = rel_v1.get(rel, set()) - rel_v2.get(rel, set())
                    for tgt in kept:
                        print(f"      {rel} -> {go_id_from_uri(tgt)} (inchange)")
                    for tgt in added:
                        print(f"    + {rel} -> {go_id_from_uri(tgt)} ({get_label(g_sub_v2, tgt)})")
                    for tgt in removed:
                        print(f"    - {rel} -> {go_id_from_uri(tgt)} ({get_label(g_sub_v1, tgt)})")


# ─── Pipeline d'analyse ───────────────────────────────────────────────────────
def run_analyse(data: dict):
    """
    Lance la pipeline complète d'analyse (tâches 1, 2, 3) à partir du dict
    retourné par traitement_go.charger_et_preparer().

    Paramètres attendus dans data :
      g_full_v1, g_full_v2 : graphes complets (tâche 1 — structure générale)
      g_sub_v1,  g_sub_v2  : sous-graphes apoptose (tâches 2 et 3)
      domain_v1, domain_v2 : sets d'URIRef des termes du domaine (tâche 2)

    Génère 4 rapports dans analyse/reports/.
    """
    g_full_v1 = data["g_full_v1"]
    g_full_v2 = data["g_full_v2"]
    g_sub_v1  = data["g_sub_v1"]
    g_sub_v2  = data["g_sub_v2"]
    domain_v1 = data["domain_v1"]
    domain_v2 = data["domain_v2"]

    log_progress("\n--- Tache 1 : Structure generale ---")
    stats_v1 = analyse_structure_generale(
        g_full_v1, "Oct 2025", REPORTS_DIR / "structure_oct2025.txt"
    )
    stats_v2 = analyse_structure_generale(
        g_full_v2, "Jan 2026", REPORTS_DIR / "structure_jan2026.txt"
    )

    log_progress("\n--- Tache 2 : Analyse quantitative ---")
    analyse_quantitative(
        g_sub_v1, g_sub_v2,
        domain_v1, domain_v2,
        stats_v1, stats_v2,
        REPORTS_DIR / "rapport_quantitatif.txt",
    )

    log_progress("\n--- Tache 3 : Analyse qualitative ---")
    analyse_qualitative(
        g_sub_v1, g_sub_v2,
        REPORTS_DIR / "rapport_qualitatif.txt",
    )

    log_progress("  Rapports generes :")
    log_progress("    - structure_oct2025.txt")
    log_progress("    - structure_jan2026.txt")
    log_progress("    - rapport_quantitatif.txt")
    log_progress("    - rapport_qualitatif.txt")
