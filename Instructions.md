# Instructions

# 4. Construction de la base de connaissances et service web

## 4.1 Modélisation RDF/OWL

Vous devez concevoir un modèle pour représenter l´évolution de GO. Voici une proposition de structure :

```python
@prefix go: <http://purl.obolibrary.org/obo/> .
@prefix evo: <http://example.org/evolution/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# Un terme dans une version spécifique
go:GO_0006281 a evo:TermVersion ;
evo:termID "GO:0006281" ;
evo:version go:version/2026-01 ;
evo:label "DNA repair"@en ;
evo:definition "The process of restoring DNA..."@en ;
evo:isDeprecated false ;
evo:parent go:GO_0006974 .

# Une version de l’ontologie
go:version/2026-01 a evo:OntologyVersion ;
evo:versionDate "2026-01-15"^^xsd:date ;
evo:releaseNotes "..." .
# Relation entre versions d’un même terme
go:GO_0006281 evo:previousVersion go:GO_0006281/2025-07 .
```

# Relation entre versions d’un même terme

go:GO_0006281 evo:previousVersion go:GO_0006281/2025-07 .

1. Définissez votre vocabulaire (namespace evo:) avec les classes et propriétés
nécessaires
2. Justifiez vos choix de modélisation dans le rapport
3. Documentez les patterns ontologiques utilisés

## 4.2 Construction de la base RDF

A partir des fichiers OWL fournis, vous devez construire une base RDF contenant les `
deux versions comparées.

1. Extraction des données : Développez un script Python qui :
- Parse les fichiers OWL (utilisez rdflib ou owlready2)
- Pour chaque terme de votre domaine, extrait ses m´etadonn´ees
- Génère des triplets RDF selon votre modèle
2. Chargement dans un triplestore :
- Installez Apache Jena Fuseki ou GraphDB
- Créez deux graphes nommés : go:version/2025-07 et go:version/2026-01
- Chargez les données correspondantes
3. Enrichissement avec des inférences :
- Utilisez les capacités d’inférence de votre triplestore
- Générez automatiquement les relations evo:previousVersion en comparant
les IDs

## 4.3 Développement du service web d’analyse

Créez une API REST (avec Flask ou FastAPI) qui expose les fonctionnalités suivantes :

#### Endpoints à implémenter :

### GET /api/term/{go_id}

- Retourne les informations d’un terme dans ses deux versions

### GET /api/term/{go_id}/diff

- Retourne les différences entre les versions (JSON structuré)

### GET /api/domain/{domain_id}/stats

- Statistiques d’évolution pour un domaine (ex: DNA repair)

### GET /api/search?q={query}

- Recherche de termes par label ou définition

Le service doit interroger le triplestore via SPARQL pour répondre aux requêtes.
Chaque endpoint doit être documenté (Swagger/OpenAPI).