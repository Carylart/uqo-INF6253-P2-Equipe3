# Dockerfile pour Apache Jena Fuseki avec triplestore GO Evolution
FROM eclipse-temurin:17-jre

# Installer wget et unzip pour télécharger Fuseki
RUN apt-get update && apt-get install -y wget unzip && rm -rf /var/lib/apt/lists/*

# Télécharger et installer Apache Jena Fuseki
ENV FUSEKI_VERSION=4.10.0
RUN wget -q https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-${FUSEKI_VERSION}.zip && \
    unzip apache-jena-fuseki-${FUSEKI_VERSION}.zip && \
    mv apache-jena-fuseki-${FUSEKI_VERSION} /opt/fuseki && \
    rm apache-jena-fuseki-${FUSEKI_VERSION}.zip

# Créer répertoire pour les données
RUN mkdir -p /opt/fuseki/data /opt/fuseki/logs

# Copier le fichier RDF
COPY go_evo.ttl /opt/fuseki/data/

# Script de démarrage qui charge les données
RUN echo '#!/bin/bash\n\
# Démarrer Fuseki en arrière-plan\n\
/opt/fuseki/fuseki-server --port 3030 --mem /go_evolution > /opt/fuseki/logs/fuseki.log 2>&1 &\n\
FUSEKI_PID=$!\n\
\n\
# Attendre que Fuseki démarre\n\
sleep 10\n\
\n\
# Charger les données RDF\n\
echo "Chargement des données GO Evolution..."\n\
curl -X POST --data-binary @/opt/fuseki/data/go_evo.ttl \
     -H "Content-Type: text/turtle" \
     http://localhost:3030/go_evolution/data\n\
\n\
# Garder le conteneur en vie\n\
wait $FUSEKI_PID' > /opt/fuseki/start.sh && chmod +x /opt/fuseki/start.sh

# Exposer le port SPARQL
EXPOSE 3030

# Démarrer Fuseki avec chargement des données
CMD ["/opt/fuseki/start.sh"]