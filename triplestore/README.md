# Triplestore Apache Jena Fuseki pour GO Evolution

Ce dossier contient la configuration pour déployer un triplestore Apache Jena Fuseki avec les données d'évolution de Gene Ontology.

## Fichiers

- `Dockerfile` : Image Docker pour Apache Jena Fuseki
- `docker-compose.yml` : Configuration Docker Compose
- `load_data.sh` : Script pour charger les données RDF ()
- `go_evo.ttl` : Données RDF générées par `evo_builder.py`
- `.dockerignore` : Fichiers à exclure de l'image Docker

## Utilisation

### Avec Docker Compose (recommandé)

```bash
# Démarrer le triplestore
docker-compose up -d

# Arrêter le triplestore
docker-compose down
```

### Avec Docker directement

```bash
# Construire l'image
docker build -t go-triplestore .

# Démarrer le conteneur
docker run -p 3030:3030 go-triplestore
```

## Accès

- **Interface web Fuseki** : http://localhost:3030
- **SPARQL endpoint** : http://localhost:3030/go_evolution/sparql
- **Dataset** : http://localhost:3030/go_evolution

## Chargement manuel des données

Si nécessaire, vous pouvez recharger les données après le démarrage :

### Sous Linux/Mac
```bash
./load_data.sh
```

### Sous Windows
```cmd
load_data.bat
```

## Requêtes SPARQL d'exemple

### Lister toutes les versions d'ontologie
```sparql
PREFIX evo: <http://example.org/evolution/>

SELECT ?version ?date ?notes
WHERE {
    ?version a evo:OntologyVersion ;
             evo:versionDate ?date ;
             evo:releaseNotes ?notes .
}
```

### Trouver les termes modifiés entre versions
```sparql
PREFIX evo: <http://example.org/evolution/>

SELECT ?termID ?v1 ?v2
WHERE {
    ?term1 evo:termID ?termID ;
           evo:version ?v1 .
    ?term2 evo:termID ?termID ;
           evo:version ?v2 ;
           evo:previousVersion ?term1 .
    FILTER(?v1 != ?v2)
}
```