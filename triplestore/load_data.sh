#!/bin/bash

# Script pour charger les données RDF dans Apache Jena Fuseki
# Utilisation: ./load_data.sh [fuseki_url] [dataset_name] [rdf_file]

FUSEKI_URL=${1:-http://localhost:3030}
DATASET=${2:-go_evolution}
RDF_FILE=${3:-go_evo.ttl}

echo "Chargement de $RDF_FILE dans le dataset $DATASET sur $FUSEKI_URL..."

# Attendre que Fuseki soit prêt
echo "Attente du démarrage de Fuseki..."
until curl -f -s "$FUSEKI_URL/$/ping" > /dev/null; do
    echo "Fuseki pas encore prêt, attente..."
    sleep 2
done

echo "Fuseki est prêt. Chargement des données..."

# Charger le fichier RDF
curl -X POST \
     --data-binary @"$RDF_FILE" \
     -H "Content-Type: text/turtle" \
     "$FUSEKI_URL/$DATASET/data"

if [ $? -eq 0 ]; then
    echo "Données chargées avec succès!"
    echo "Interface web disponible sur: $FUSEKI_URL"
    echo "SPARQL endpoint: $FUSEKI_URL/$DATASET/sparql"
else
    echo "Erreur lors du chargement des données"
    exit 1
fi