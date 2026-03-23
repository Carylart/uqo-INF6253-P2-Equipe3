"""
INF6253 - Projet P2 : Traitement des fichiers OWL Gene Ontology
---------------------------------------------------------------
Responsabilités de ce module :
  - Charge les fichiers .owl en graphes rdflib
  - Extrait le sous-ensemble du domaine apoptose (GO:0012501 + descendants)
  - Sauvegarde les sous-ensembles en fichiers .owl dans analyse/data/

Principe d'extraction du domaine :
  - Construit un index inverse parent->enfants en parcourant toutes les classes
  - Suit les relations is_a directes ET les expressions OWL complexes
    (restrictions someValuesFrom, intersectionOf, unionOf, equivalentClass)
  - BFS depuis GO:0012501 sur cet index pour obtenir tous les descendants
  - Construit un sous-graphe fidèle : tous les triplets des termes du domaine,
    blank nodes récursifs, axiomes owl:Axiom, déclarations minimales externes

Ce module est le point d'entrée unique pour tout accès aux données brutes.
Il est appelé par main.py et ses résultats sont transmis aux autres modules
sans rechargement.

Constantes partagées exportées (importées par analyse_go.py, raisonneur_go.py) :
  FILE_V1, FILE_V2, FILE_SUB_V1, FILE_SUB_V2
  DATA_DIR, REPORTS_DIR
  ROOT_ID
  OBO, DEFINITION, IS_DEPRECATED
  PART_OF, REGULATES, NEG_REGULATES, POS_REGULATES, ...
  DOMAIN_EXPANSION_RELATIONS, CONSERVATION_ONLY_RELATIONS
"""

import sys
import time
from pathlib import Path
from collections import deque, defaultdict

try:
    from rdflib import Graph, Namespace, URIRef, BNode, Literal
    from rdflib.namespace import RDF, RDFS, OWL
except ImportError:
    print("rdflib manquant. Installez-le avec : pip install rdflib")
    sys.exit(1)

# ─── Chemins ──────────────────────────────────────────────────────────────────
DATA_DIR    = Path("analyse/data")
REPORTS_DIR = Path("analyse/reports")

FILE_V1     = DATA_DIR / "go-base-20251010.owl"
FILE_V2     = DATA_DIR / "go-base-20260123.owl"

FILE_SUB_V1 = DATA_DIR / "apoptose-20251010.owl"
FILE_SUB_V2 = DATA_DIR / "apoptose-20260123.owl"

# ─── Namespaces et propriétés GO ──────────────────────────────────────────────
OBO = Namespace("http://purl.obolibrary.org/obo/")

DEFINITION    = OBO["IAO_0000115"]   # définition officielle OBO/IAO
IS_DEPRECATED = OWL.deprecated

# Relations sémantiques RO (Relation Ontology)
PART_OF                 = OBO["RO_0000050"]
REGULATES               = OBO["RO_0002211"]
NEG_REGULATES           = OBO["RO_0002212"]
POS_REGULATES           = OBO["RO_0002213"]
STARTS_WITH             = OBO["RO_0002224"]
ENDS_WITH               = OBO["RO_0002230"]
HAS_INPUT               = OBO["RO_0002233"]
OCCURS_IN               = OBO["BFO_0000066"]
ENABLED_BY              = OBO["RO_0002333"]
INVOLVED_IN             = OBO["RO_0002331"]
LOCATED_IN              = OBO["RO_0001025"]
HAS_TARGET_END_LOCATION = OBO["RO_0002339"]
IN_TAXON                = OBO["RO_0002162"]

# Terme racine du domaine
ROOT_ID = "GO_0012501"  # programmed cell death (apoptose)

# Relations utilisées pour étendre le domaine lors du BFS
DOMAIN_EXPANSION_RELATIONS = {
    PART_OF,
    REGULATES,
    POS_REGULATES,
    NEG_REGULATES,
    STARTS_WITH,
    ENDS_WITH,
    INVOLVED_IN,
}

# Relations conservées dans le sous-graphe mais pas utilisées pour étendre le domaine
CONSERVATION_ONLY_RELATIONS = {
    HAS_INPUT,
    OCCURS_IN,
    ENABLED_BY,
    LOCATED_IN,
    HAS_TARGET_END_LOCATION,
    IN_TAXON,
}


# ─── Journalisation console ───────────────────────────────────────────────────
def log_progress(message: str):
    """
    Affiche un message de progression dans la console via sys.__stdout__.
    Utilise le stdout original pour rester visible même si sys.stdout
    est redirigé vers un fichier par FileLogger dans analyse_go.py.
    """
    sys.__stdout__.write(message + "\n")
    sys.__stdout__.flush()


# ─── Chargement ───────────────────────────────────────────────────────────────
def load_graph(path: Path, label: str) -> Graph:
    """
    Charge un fichier OWL (format RDF/XML) dans un graphe rdflib.
    Affiche le temps de chargement et le nombre de triplets chargés.
    Retourne le graphe chargé.
    """
    log_progress(f"[{label}] Chargement de {path.name} ...")
    t0 = time.time()
    g = Graph()
    g.parse(str(path), format="xml")
    elapsed = time.time() - t0
    log_progress(f"  Charge en {elapsed:.1f}s -- {len(g):,} triplets")
    return g


# ─── Utilitaires URI ──────────────────────────────────────────────────────────
def uri(go_id: str) -> URIRef:
    """
    Convertit un identifiant GO (GO:0012501 ou GO_0012501)
    en URIRef OBO complet : http://purl.obolibrary.org/obo/GO_0012501
    """
    return OBO[go_id.replace(":", "_")]


def go_id_from_uri(u) -> str:
    """
    Extrait l'identifiant lisible GO:XXXXXXX depuis un URIRef OBO.
    Exemple : http://purl.obolibrary.org/obo/GO_0006915 -> GO:0006915
    """
    local = str(u).split("/")[-1]
    return local.replace("_", ":", 1)


def safe_go_id(u) -> str:
    """
    Retourne un identifiant GO lisible si l'URI est dans l'espace OBO,
    sinon retourne la représentation string brute.
    Utilisé dans les fonctions de debug pour l'affichage.
    """
    if isinstance(u, URIRef) and str(u).startswith(str(OBO)):
        return go_id_from_uri(u)
    return str(u)


# ─── Utilitaires RDF / OWL ────────────────────────────────────────────────────
def iter_rdf_list(g: Graph, list_node):
    """
    Itère sur les éléments d'une liste RDF (rdf:first / rdf:rest).
    Gère les cycles éventuels via un ensemble de noeuds visités.
    """
    current = list_node
    visited = set()
    while current and current != RDF.nil:
        if current in visited:
            break
        visited.add(current)
        first = g.value(current, RDF.first)
        if first is not None:
            yield first
        current = g.value(current, RDF.rest)


def is_restriction_bnode(g: Graph, node) -> bool:
    """
    Retourne True si node est un blank node de restriction OWL
    (typé owl:Restriction ou ayant owl:onProperty).
    """
    return isinstance(node, BNode) and (
        (node, RDF.type, OWL.Restriction) in g
        or g.value(node, OWL.onProperty) is not None
    )


# ─── Extraction des parents depuis une expression OWL ────────────────────────
def collect_domain_parents_from_expression(
    g: Graph,
    expr_node,
    domain_relations: set,
    visited_nodes: set = None,
) -> set:
    """
    Extrait récursivement les termes GO "parents de domaine" depuis
    une expression OWL (blank node, restriction, liste RDF).

    Règles d'inclusion :
      - URIRef GO directe -> ajoutée si structurelle (subClassOf, intersection...)
      - Restriction [ onProperty P ; someValuesFrom/allValuesFrom X ] :
        X est ajouté uniquement si P est dans domain_relations
      - intersectionOf / unionOf : exploration récursive des items
      - Listes RDF : exploration récursive
      - Fallback : exploration prudente des objets du blank node

    Retourne un set d'URIRef GO identifiés comme parents de domaine.
    """
    if visited_nodes is None:
        visited_nodes = set()
    if expr_node in visited_nodes:
        return set()
    visited_nodes.add(expr_node)

    parents = set()

    # URI GO structurelle directe
    if isinstance(expr_node, URIRef):
        if str(expr_node).startswith(str(OBO)) and "GO_" in str(expr_node):
            parents.add(expr_node)
        return parents

    # Littéral : rien à extraire
    if isinstance(expr_node, Literal):
        return parents

    # Restriction OWL : someValuesFrom / allValuesFrom
    if is_restriction_bnode(g, expr_node):
        prop = g.value(expr_node, OWL.onProperty)

        for attr in (OWL.someValuesFrom, OWL.allValuesFrom):
            filler = g.value(expr_node, attr)
            if filler is not None:
                if prop in domain_relations and isinstance(filler, URIRef):
                    if str(filler).startswith(str(OBO)) and "GO_" in str(filler):
                        parents.add(filler)
                parents |= collect_domain_parents_from_expression(
                    g, filler, domain_relations, visited_nodes
                )

    # intersectionOf
    inter = g.value(expr_node, OWL.intersectionOf)
    if inter is not None:
        for item in iter_rdf_list(g, inter):
            parents |= collect_domain_parents_from_expression(
                g, item, domain_relations, visited_nodes
            )

    # unionOf
    union = g.value(expr_node, OWL.unionOf)
    if union is not None:
        for item in iter_rdf_list(g, union):
            parents |= collect_domain_parents_from_expression(
                g, item, domain_relations, visited_nodes
            )

    # Noeud de liste RDF direct
    if (expr_node, RDF.first, None) in g or (expr_node, RDF.rest, None) in g:
        for item in iter_rdf_list(g, expr_node):
            parents |= collect_domain_parents_from_expression(
                g, item, domain_relations, visited_nodes
            )

    # Fallback : exploration des objets du blank node (hors annotations)
    for _, p, o in g.triples((expr_node, None, None)):
        if p in {OWL.annotatedSource, OWL.annotatedProperty, OWL.annotatedTarget}:
            continue
        if isinstance(o, (BNode, URIRef)):
            parents |= collect_domain_parents_from_expression(
                g, o, domain_relations, visited_nodes
            )

    return parents


# ─── Index inverse parent -> enfants ─────────────────────────────────────────
def build_reverse_domain_index(g: Graph, domain_relations: set) -> dict:
    """
    Construit un index inverse { parent_GO_uri -> {enfant_GO_uri, ...} }
    en parcourant toutes les classes de l'ontologie.

    Pour chaque classe candidate, analyse :
      - rdfs:subClassOf direct (URI) : relation is_a classique
      - rdfs:subClassOf complexe (BNode) : restrictions, intersections, unions
      - owl:equivalentClass direct et complexe

    Cet index permet ensuite au BFS de get_domain_terms() de ne parcourir
    que les voisins réels sans itérer sur tout le graphe à chaque étape.
    """
    log_progress("  [Index] Construction de l'index inverse du domaine ...")
    t0 = time.time()

    reverse_links = defaultdict(set)

    # Collecte des classes candidates (typées + présentes dans subClassOf/equivalentClass)
    candidate_terms = {s for s in g.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef)}
    for s, _, _ in g.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, URIRef):
            candidate_terms.add(s)
    for s, _, _ in g.triples((None, OWL.equivalentClass, None)):
        if isinstance(s, URIRef):
            candidate_terms.add(s)

    total     = len(candidate_terms)
    processed = 0

    for child in candidate_terms:
        processed += 1
        if processed % 10000 == 0:
            log_progress(f"    [Index] {processed:,}/{total:,} classes analysees ...")

        # subClassOf
        for expr in g.objects(child, RDFS.subClassOf):
            if isinstance(expr, URIRef):
                if str(expr).startswith(str(OBO)) and "GO_" in str(expr):
                    reverse_links[expr].add(child)
            else:
                for parent in collect_domain_parents_from_expression(
                    g, expr, domain_relations
                ):
                    reverse_links[parent].add(child)

        # equivalentClass
        for expr in g.objects(child, OWL.equivalentClass):
            if isinstance(expr, URIRef):
                if str(expr).startswith(str(OBO)) and "GO_" in str(expr):
                    reverse_links[expr].add(child)
            else:
                for parent in collect_domain_parents_from_expression(
                    g, expr, domain_relations
                ):
                    reverse_links[parent].add(child)

    elapsed = time.time() - t0
    log_progress(
        f"  [Index] Termine en {elapsed:.1f}s -- {len(reverse_links):,} parents indexes"
    )
    return reverse_links


# ─── Extraction du domaine (BFS) ─────────────────────────────────────────────
def get_domain_terms(g: Graph, root_id: str) -> set:
    """
    Retourne l'ensemble de tous les termes du domaine apoptose
    (racine GO:0012501 incluse) par BFS sur l'index inverse.

    Couvre :
      - Descendants is_a classiques
      - Descendants via restrictions OWL (part_of, regulates, etc.)
      - Descendants définis via expressions OWL complexes (intersectionOf, etc.)
    """
    root_uri      = uri(root_id)
    reverse_links = build_reverse_domain_index(g, DOMAIN_EXPANSION_RELATIONS)

    visited = set()
    queue   = deque([root_uri])

    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        for child in reverse_links.get(current, set()):
            if child not in visited:
                queue.append(child)

    return visited


# ─── Construction du sous-graphe ─────────────────────────────────────────────
def construire_sous_graphe(g: Graph, domain_terms: set, label: str) -> Graph:
    """
    Construit un sous-graphe RDF fidèle du domaine apoptose.

    Stratégie d'inclusion :
      1. Tous les triplets dont le sujet est un terme du domaine
      2. Récursivement, tous les blank nodes reliés à ces termes
         (restrictions OWL, listes RDF, structures imbriquées)
      3. Axiomes owl:Axiom annotant des triplets du domaine
      4. Déclarations minimales (type, label, définition, deprecated)
         des classes externes référencées

    Le sous-graphe résultant est autonome : il peut être chargé dans
    Protégé ou utilisé par le raisonneur sans l'ontologie complète.
    """
    log_progress(f"  [{label}] Construction du sous-graphe apoptose ...")
    g_sub = Graph()

    for prefix, ns in g.namespaces():
        g_sub.bind(prefix, ns)

    referenced_uris = set()
    visited_bnodes  = set()

    def expand_bnode(node):
        """
        Copie récursive d'un blank node et de tous ses descendants.
        Conserve les restrictions OWL, listes RDF, axiomes imbriqués.
        """
        if not isinstance(node, BNode) or node in visited_bnodes:
            return
        visited_bnodes.add(node)
        for _, p, o in g.triples((node, None, None)):
            g_sub.add((node, p, o))
            if isinstance(o, URIRef) and o not in domain_terms:
                referenced_uris.add(o)
            elif isinstance(o, BNode):
                expand_bnode(o)

    # Triplets des termes du domaine
    for term in domain_terms:
        for _, p, o in g.triples((term, None, None)):
            g_sub.add((term, p, o))
            if isinstance(o, URIRef) and o not in domain_terms:
                referenced_uris.add(o)
            elif isinstance(o, BNode):
                expand_bnode(o)

    # Axiomes owl:Axiom annotant des triplets du domaine
    for ax in g.subjects(RDF.type, OWL.Axiom):
        annotated_source = g.value(ax, OWL.annotatedSource)
        if annotated_source in domain_terms or annotated_source in visited_bnodes:
            for _, p, o in g.triples((ax, None, None)):
                g_sub.add((ax, p, o))
                if isinstance(o, URIRef) and o not in domain_terms:
                    referenced_uris.add(o)
                elif isinstance(o, BNode):
                    expand_bnode(o)

    # Déclarations minimales des ressources externes
    EXTERNAL_MIN_PROPS = {
        RDF.type,
        RDFS.label,
        RDFS.comment,
        OWL.deprecated,
        DEFINITION,
        OBO["oboInOwl/id"],
        OBO["oboInOwl/hasExactSynonym"],
        OBO["oboInOwl/hasBroadSynonym"],
        OBO["oboInOwl/hasNarrowSynonym"],
        OBO["oboInOwl/hasRelatedSynonym"],
    }
    for cls in referenced_uris:
        for _, p, o in g.triples((cls, None, None)):
            if p in EXTERNAL_MIN_PROPS:
                g_sub.add((cls, p, o))
                if isinstance(o, BNode):
                    expand_bnode(o)

    log_progress(
        f"  [{label}] Sous-graphe : {len(g_sub):,} triplets "
        f"({len(domain_terms)} termes, {len(visited_bnodes)} blank nodes)"
    )
    return g_sub


def sauvegarder_sous_graphe(g_sub: Graph, output_path: Path, label: str):
    """
    Sérialise le sous-graphe RDF en fichier OWL (format RDF/XML).
    Le fichier généré peut être ouvert dans Protégé pour exploration manuelle.
    """
    log_progress(f"  [{label}] Sauvegarde -> {output_path.name} ...")
    t0 = time.time()
    g_sub.serialize(destination=str(output_path), format="xml")
    log_progress(f"  [{label}] Sauvegarde terminee en {time.time() - t0:.1f}s")


# ─── Fonctions de debug (usage ponctuel, non appelées en production) ──────────
def debug_term_links(g: Graph, go_term_id: str):
    """
    Affiche les liens structuraux d'un terme GO pour diagnostiquer
    son appartenance ou non au domaine extrait.
    Usage : appeler manuellement depuis un script de test, pas depuis main.py.
    """
    term = uri(go_term_id)
    print(f"\n=== DEBUG {go_term_id} ===")
    for o in g.objects(term, RDF.type):
        print(f"type -> {safe_go_id(o)}")
    for o in g.objects(term, RDFS.subClassOf):
        if isinstance(o, URIRef):
            print(f"subClassOf -> {safe_go_id(o)}")
        else:
            prop  = g.value(o, OWL.onProperty)
            some  = g.value(o, OWL.someValuesFrom)
            allv  = g.value(o, OWL.allValuesFrom)
            inter = g.value(o, OWL.intersectionOf)
            union = g.value(o, OWL.unionOf)
            print("subClassOf -> [blank node]")
            if prop  is not None: print(f"  onProperty      -> {safe_go_id(prop)}")
            if some  is not None: print(f"  someValuesFrom  -> {safe_go_id(some)}")
            if allv  is not None: print(f"  allValuesFrom   -> {safe_go_id(allv)}")
            if inter is not None:
                print("  intersectionOf ->")
                for item in iter_rdf_list(g, inter):
                    print(f"    - {safe_go_id(item)}")
            if union is not None:
                print("  unionOf ->")
                for item in iter_rdf_list(g, union):
                    print(f"    - {safe_go_id(item)}")
    for o in g.objects(term, OWL.equivalentClass):
        if isinstance(o, URIRef):
            print(f"equivalentClass -> {safe_go_id(o)}")
        else:
            inter = g.value(o, OWL.intersectionOf)
            union = g.value(o, OWL.unionOf)
            print("equivalentClass -> [blank node]")
            if inter is not None:
                print("  intersectionOf ->")
                for item in iter_rdf_list(g, inter):
                    if isinstance(item, BNode):
                        prop = g.value(item, OWL.onProperty)
                        some = g.value(item, OWL.someValuesFrom)
                        allv = g.value(item, OWL.allValuesFrom)
                        print("    - [restriction]")
                        if prop is not None: print(f"      onProperty     -> {safe_go_id(prop)}")
                        if some is not None: print(f"      someValuesFrom -> {safe_go_id(some)}")
                        if allv is not None: print(f"      allValuesFrom  -> {safe_go_id(allv)}")
                    else:
                        print(f"    - {safe_go_id(item)}")
            if union is not None:
                print("  unionOf ->")
                for item in iter_rdf_list(g, union):
                    print(f"    - {safe_go_id(item)}")


def debug_domain_membership(g: Graph, domain_terms: set, go_term_id: str):
    """
    Affiche si un terme GO est dans le domaine extrait ou non.
    Usage : appeler manuellement depuis un script de test, pas depuis main.py.
    """
    term   = uri(go_term_id)
    status = "DANS LE DOMAINE" if term in domain_terms else "ABSENT DU DOMAINE"
    print(f"[CHECK] {go_term_id} -> {status}")


# ─── Pipeline complète de chargement ──────────────────────────────────────────
def charger_et_preparer() -> dict:
    """
    Pipeline principale de chargement et préparation des données.
    Appelée une seule fois par main.py.

    Étapes :
      1. Vérification des fichiers source
      2. Chargement des deux ontologies complètes
      3. Extraction du domaine apoptose (BFS via index inverse)
      4. Construction des sous-graphes apoptose
      5. Sauvegarde des sous-graphes en .owl

    Retourne un dictionnaire contenant :
      g_full_v1, g_full_v2  : graphes complets (pour analyse_go structure générale)
      g_sub_v1,  g_sub_v2   : sous-graphes apoptose (pour analyse quant/qual + raisonneur)
      domain_v1, domain_v2  : sets d'URIRef des termes du domaine
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    for f in [FILE_V1, FILE_V2]:
        if not f.exists():
            log_progress(f"Fichier introuvable : {f}")
            log_progress(f"Placez les fichiers dans : {DATA_DIR.resolve()}")
            sys.exit(1)

    log_progress("\n--- Chargement des ontologies completes ---")
    g_full_v1 = load_graph(FILE_V1, "Oct 2025")
    g_full_v2 = load_graph(FILE_V2, "Jan 2026")

    log_progress("\n--- Extraction du domaine apoptose (GO:0012501) ---")
    log_progress("  Extraction Oct 2025 ...")
    t0        = time.time()
    domain_v1 = get_domain_terms(g_full_v1, ROOT_ID)
    log_progress(f"  {len(domain_v1)} termes trouves (Oct 2025) en {time.time() - t0:.1f}s")

    log_progress("  Extraction Jan 2026 ...")
    t0        = time.time()
    domain_v2 = get_domain_terms(g_full_v2, ROOT_ID)
    log_progress(f"  {len(domain_v2)} termes trouves (Jan 2026) en {time.time() - t0:.1f}s")

    log_progress("\n--- Construction et sauvegarde des sous-graphes ---")
    g_sub_v1 = construire_sous_graphe(g_full_v1, domain_v1, "Oct 2025")
    sauvegarder_sous_graphe(g_sub_v1, FILE_SUB_V1, "Oct 2025")

    g_sub_v2 = construire_sous_graphe(g_full_v2, domain_v2, "Jan 2026")
    sauvegarder_sous_graphe(g_sub_v2, FILE_SUB_V2, "Jan 2026")

    return {
        "g_full_v1": g_full_v1,
        "g_full_v2": g_full_v2,
        "g_sub_v1":  g_sub_v1,
        "g_sub_v2":  g_sub_v2,
        "domain_v1": domain_v1,
        "domain_v2": domain_v2,
    }
