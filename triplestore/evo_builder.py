"""
Module de conversion GO -> modèle évolutif evo (RDF/OWL). 
Génère un dataset RDF comparant deux versions de GO.
"""
from pathlib import Path
import sys

# Pour exécuter ce script depuis n'importe quel dossier et retrouver le module analyse/
SYS_PATH_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SYS_PATH_ROOT))

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD

from analyse.traitement_go import (
    DATA_DIR,
    FILE_V1,
    FILE_V2,
    OBO,
    DEFINITION,
    IS_DEPRECATED,
    go_id_from_uri,
    log_progress,
)

EVO = Namespace("http://example.org/evolution/")

# Fichier de sortie RDF consolidé
default_output = Path("triplestore/go_evo.ttl")


def normalize_version_tag(filename: str) -> str:
    # ex: go-base-20251010.owl -> 2025-10-10
    tag = Path(filename).stem.split("-")[-1]
    if len(tag) == 8 and tag.isdigit():
        return f"{tag[0:4]}-{tag[4:6]}-{tag[6:8]}"
    return tag


def term_version_uri(term_uri: URIRef, version_tag: str) -> URIRef:
    term_id = str(term_uri).split("/")[-1]  # GO_0006281
    return URIRef(f"{str(OBO)}{term_id}/{version_tag}")


def load_owl_graph(path: Path) -> Graph:
    log_progress(f"[EVO] Chargement OWL {path}")
    g = Graph()
    g.parse(str(path), format="xml")
    return g


def build_evo_graph(output_path: Path = default_output) -> Graph:
    """Construit un graphe EVO comparant deux versions de GO et sauvegarde TTL."""
    g_out = Graph()
    g_out.bind("go", OBO)
    g_out.bind("evo", EVO)
    g_out.bind("rdfs", RDFS)
    g_out.bind("owl", OWL)

    versions = []

    owl_v1 = FILE_V1 if FILE_V1.exists() else DATA_DIR / "apoptose-20251010.owl"
    owl_v2 = FILE_V2 if FILE_V2.exists() else DATA_DIR / "apoptose-20260123.owl"

    for owl_file in [owl_v1, owl_v2]:
        if not owl_file.exists():
            raise FileNotFoundError(f"Fichier introuvable : {owl_file}")

        version_tag = normalize_version_tag(owl_file.name)
        version_node = URIRef(f"{str(OBO)}version/{version_tag}")
        versions.append((owl_file, version_tag, version_node))

        g_src = load_owl_graph(owl_file)

        # Métadonnées de version
        g_out.add((version_node, RDF.type, EVO.OntologyVersion))
        g_out.add((version_node, EVO.versionDate, Literal(version_tag, datatype=XSD.date)))
        g_out.add((version_node, EVO.releaseNotes, Literal(f"Import automatique depuis {owl_file.name}")))

        # Termes GO
        for term in g_src.subjects(RDF.type, OWL.Class):
            if not isinstance(term, URIRef):
                continue
            if not str(term).startswith(str(OBO)) or "GO_" not in str(term):
                continue

            term_v = _term_version_uri(term, version_tag)
            g_out.add((term_v, RDF.type, EVO.TermVersion))
            g_out.add((term_v, EVO.termID, Literal(go_id_from_uri(term))))
            g_out.add((term_v, EVO.version, version_node))

            label = g_src.value(term, RDFS.label)
            if label is not None:
                g_out.add((term_v, EVO.label, label))

            definition = g_src.value(term, DEFINITION)
            if definition is None:
                definition = g_src.value(term, RDFS.comment)
            if definition is not None:
                g_out.add((term_v, EVO.definition, definition))

            deprecated = g_src.value(term, IS_DEPRECATED)
            if deprecated is not None:
                bool_val = Literal(bool(deprecated in (Literal(True), "true", "1")))
            else:
                bool_val = Literal(False)
            g_out.add((term_v, EVO.isDeprecated, bool_val))

            # Parents (is_a)
            for parent in g_src.objects(term, RDFS.subClassOf):
                if isinstance(parent, URIRef) and str(parent).startswith(str(OBO)) and "GO_" in str(parent):
                    g_out.add((term_v, EVO.parent, parent))

    # Enrichissement previousVersion en comparant termID
    all_terms = {}
    for term_v in g_out.subjects(RDF.type, EVO.TermVersion):
        term_id = g_out.value(term_v, EVO.termID)
        version_uri = g_out.value(term_v, EVO.version)
        if term_id is None or version_uri is None:
            continue
        key = str(term_id)
        all_terms.setdefault(key, []).append((term_v, str(version_uri)))

    for term_id, term_list in all_terms.items():
        if len(term_list) < 2:
            continue
        # tri sur version date pour trouver previous
        term_list_sorted = sorted(term_list, key=lambda x: x[1])
        for prev, curr in zip(term_list_sorted, term_list_sorted[1:]):
            g_out.add((curr[0], EVO.previousVersion, prev[0]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    g_out.serialize(destination=str(output_path), format="turtle")
    log_progress(f"[EVO] TTL genere: {output_path} ({len(g_out):,} triplets)")
    return g_out


if __name__ == "__main__":
    build_evo_graph()
