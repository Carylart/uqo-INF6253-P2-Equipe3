from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from rdflib import Graph, Literal, URIRef

from triplestore.evo_builder import build_evo_graph

app = FastAPI(
    title="GO Evolution API",
    description="API REST pour explorer les versions GO et leur évolution via un modèle evo.",
    version="1.0.0",
)

ROOT_DIR = Path(__file__).resolve().parents[2]
EVO_FILE = ROOT_DIR / "triplestore" / "go_evo.ttl"

if not EVO_FILE.exists():
    build_evo_graph(EVO_FILE)

GRAPH = Graph()
GRAPH.parse(str(EVO_FILE), format="turtle")


class TermVersionData(BaseModel):
    uri: str
    version_node: str | None
    label: str | None
    definition: str | None
    isDeprecated: bool | None
    parents: list[str]
    previousVersion: str | None


class TermResponse(BaseModel):
    go_id: str
    versions: list[TermVersionData]


def execute_sparql(query: str):
    return GRAPH.query(query)


def normalize_go_id(go_id: str) -> str:
    if go_id.startswith("GO:"):
        return go_id
    if go_id.startswith("GO_"):
        return go_id.replace("_", ":", 1)
    raise ValueError("Identifiant GO invalide")


def get_term_versions(go_id: str) -> list[TermVersionData]:
    go_id_norm = normalize_go_id(go_id)
    query = f"""
        PREFIX evo: <http://example.org/evolution/>
        SELECT ?term ?version ?label ?definition ?isDeprecated ?parent ?prev
        WHERE {{
            ?term evo:termID "{go_id_norm}" .
            OPTIONAL {{ ?term evo:version ?version . }}
            OPTIONAL {{ ?term evo:label ?label . }}
            OPTIONAL {{ ?term evo:definition ?definition . }}
            OPTIONAL {{ ?term evo:isDeprecated ?isDeprecated . }}
            OPTIONAL {{ ?term evo:parent ?parent . }}
            OPTIONAL {{ ?term evo:previousVersion ?prev . }}
        }}
    """

    rows = list(execute_sparql(query))
    if not rows:
        return []

    data = {}
    for row in rows:
        term_uri = str(row.term)
        record = data.setdefault(term_uri, {
            "uri": term_uri,
            "version_node": None,
            "label": None,
            "definition": None,
            "isDeprecated": False,
            "parents": [],
            "previousVersion": None,
        })

        if row.version is not None:
            record["version_node"] = str(row.version)
        if row.label is not None:
            record["label"] = str(row.label)
        if row.definition is not None:
            record["definition"] = str(row.definition)
        if row.isDeprecated is not None:
            record["isDeprecated"] = str(row.isDeprecated).lower() in ("true", "1")
        if row.parent is not None:
            record["parents"].append(str(row.parent))
        if row.prev is not None:
            record["previousVersion"] = str(row.prev)

    return [TermVersionData(**v) for v in data.values()]


@app.get("/api/term/{go_id}", response_model=TermResponse)
def get_term(go_id: str):
    versions = get_term_versions(go_id)
    if not versions:
        raise HTTPException(status_code=404, detail=f"Terme {go_id} introuvable")
    return TermResponse(go_id=normalize_go_id(go_id), versions=versions)


@app.get("/api/term/{go_id}/diff")
def get_term_diff(go_id: str):
    versions = get_term_versions(go_id)
    if len(versions) < 2:
        raise HTTPException(status_code=404, detail=f"Diff non disponible pour {go_id} (moins de 2 versions)")

    def norm(v: TermVersionData):
        return {
            "label": v.label or "",
            "definition": v.definition or "",
            "isDeprecated": v.isDeprecated,
            "parents": sorted(v.parents),
        }

    v1, v2 = sorted(versions, key=lambda x: x.version_node or "")[:2]
    d1 = norm(v1)
    d2 = norm(v2)

    changes = {}
    for key in d1.keys():
        if d1[key] != d2[key]:
            changes[key] = {"from": d1[key], "to": d2[key]}

    return {
        "go_id": normalize_go_id(go_id),
        "version_from": v1.version_node,
        "version_to": v2.version_node,
        "changes": changes,
    }


@app.get("/api/domain/{domain_id}/stats")
def get_domain_stats(domain_id: str):
    go_id_norm = normalize_go_id(domain_id)
    go_uri = URIRef(f"http://purl.obolibrary.org/obo/{go_id_norm.replace(':', '_')}")

    # recherche tous termes descendants via property path evo:parent+
    query = f"""
        PREFIX evo: <http://example.org/evolution/>
        SELECT ?term ?termID ?version ?isDeprecated ?parent
        WHERE {{
            ?term evo:termID ?termID ; evo:version ?version .
            ?term evo:parent+ <{go_uri}> .
            OPTIONAL {{ ?term evo:isDeprecated ?isDeprecated . }}
            OPTIONAL {{ ?term evo:parent ?parent . }}
        }}
    """
    rows = list(execute_sparql(query))
    if not rows:
        raise HTTPException(status_code=404, detail=f"Aucun terme trouve pour domaine {domain_id}")

    terms = {}
    for row in rows:
        tid = str(row.termID)
        info = terms.setdefault(tid, {"versions": {}, "parents": {}})
        ver = str(row.version)
        info["versions"].setdefault(ver, []).append(str(row.term))
        if row.isDeprecated is not None and str(row.isDeprecated).lower() in ("true", "1"):
            info.setdefault("deprecated", set()).add(ver)
        if row.parent:
            info["parents"].setdefault(ver, set()).add(str(row.parent))

    total = len(terms)
    per_version = {}
    deprecated = {}
    changed_hierarchy = 0

    for tid, info in terms.items():
        for ver, ids in info["versions"].items():
            per_version[ver] = per_version.get(ver, 0) + len(ids)
        for ver in info.get("deprecated", set()):
            deprecated[ver] = deprecated.get(ver, 0) + 1

        if len(info["parents"]) > 1:
            sets = list(info["parents"].values())
            if any(s != sets[0] for s in sets[1:]):
                changed_hierarchy += 1

    return {
        "domain_id": normalize_go_id(domain_id),
        "term_count": total,
        "terms_per_version": per_version,
        "deprecated_per_version": deprecated,
        "hierarchy_changed_terms": changed_hierarchy,
    }


@app.get("/api/search")
def search_terms(q: str = Query(..., min_length=1)):
    pattern = q.lower().replace('"', '\\"')
    query = f"""
        PREFIX evo: <http://example.org/evolution/>
        SELECT DISTINCT ?termID ?label ?definition ?version
        WHERE {{
            ?term evo:termID ?termID ; evo:version ?version .
            OPTIONAL {{ ?term evo:label ?label . }}
            OPTIONAL {{ ?term evo:definition ?definition . }}
            FILTER(
                contains(lcase(str(?label)), "{pattern}")
                || contains(lcase(str(?definition)), "{pattern}")
            )
        }}
        ORDER BY ?termID
        LIMIT 100
    """

    rows = list(execute_sparql(query))
    return [
        {
            "go_id": str(row.termID),
            "label": str(row.label) if row.label else None,
            "definition": str(row.definition) if row.definition else None,
            "version": str(row.version),
        }
        for row in rows
    ]
