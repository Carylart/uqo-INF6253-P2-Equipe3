# uqo-INF6253-P2-Equipe3

Projet P2 : Évolution d'ontologies biomédicales - Extension de navigateur pour la veille sémantique sur Gene Ontology

## Description du projet

Ce projet vise à développer une solution complète pour suivre l'évolution de Gene Ontology (GO) entre différentes versions. Il comprend trois parties principales:

1. **Analyse comparative** des versions de GO
2. **Service web** d'analyse avec base de connaissances RDF
3. **Extension de navigateur** pour visualiser les changements en temps réel

## Structure du projet

```
uqo-INF6253-P2-Equipe3/
├── analyse/              # Scripts d'analyse comparative (Partie 1)
├── service_web/          # API REST et triplestore (Partie 2)
│   ├── app/
│   └── openapi.yml
├── extension-chrome/     # Extension Chrome (Partie 3)
│   ├── manifest.json
│   ├── content.js
│   ├── background.js
│   ├── popup.html/css/js
│   ├── styles.css
│   └── icons/
├── extension-firefox/    # Extension Firefox (Partie 3)
├── triplestore/          # Configuration et données RDF
├── requirement.txt       # Dépendances Python
└── README.md
```

## Installation et exécution

### Prérequis

- Python 3.8+
- Node.js (optionnel, pour certains outils)
- Chrome ou Firefox
- Apache Jena Fuseki ou GraphDB (triplestore)

### Étape 1: Installation des dépendances Python

```bash
pip install -r requirement.txt
```

### Étape 2: Générer la base RDF

```bash
python analyse/evo_builder.py
```

Cette commande analyse les fichiers OWL de Gene Ontology et génère la base de connaissances RDF représentant l'évolution entre les versions.

### Étape 3: Démarrer le triplestore avec Docker (optionnel)

Le projet inclut un Dockerfile pour Apache Jena Fuseki qui charge automatiquement les données RDF.

#### Option 1: Avec Docker Compose (recommandé)

```bash
cd triplestore
docker-compose up -d
```

#### Option 2: Avec Docker directement

```bash
# Construire l'image Docker
docker build -t go-triplestore triplestore/

# Démarrer le conteneur
docker run -p 3030:3030 go-triplestore
```

Le triplestore sera accessible sur `http://localhost:3030` avec l'interface web Fuseki.

#### Charger les données manuellement (si nécessaire)

Si vous voulez charger les données après le démarrage du conteneur:

Linux :
```bash
cd triplestore
./load_data.sh
```
OU Windows :
```bash
cd triplestore
./load_data.bat
```

### Étape 4: Démarrer le service web

```bash
cd service_web
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Le service web sera accessible à `http://localhost:8000`

Documentation API: `http://localhost:8000/docs`

### Étape 5: Installer l'extension de navigateur

#### Pour Chrome:

1. Ouvrir Chrome et aller à `chrome://extensions/`
2. Activer le "Mode développeur"
3. Cliquer sur "Charger l'extension non empaquetée"
4. Sélectionner le dossier `extension-chrome`
5. Configurer l'URL du service web dans la popup de l'extension

#### Pour Firefox:

1. Ouvrir Firefox et aller à `about:debugging`
2. Cliquer sur "Ce Firefox"
3. Cliquer sur "Charger un module complémentaire temporaire"
4. Sélectionner `extension-firefox/manifest.json`
5. Configurer l'URL du service web dans la popup de l'extension

## 📖 Utilisation

### Service Web - Points d'accès API

- `GET /api/term/{go_id}` - Informations sur un terme GO dans les deux versions
- `GET /api/term/{go_id}/diff` - Différences entre les versions pour un terme
- `GET /api/domain/{domain_id}/stats` - Statistiques d'évolution pour un domaine
- `GET /api/search?q={query}` - Recherche de termes par label ou définition

### Extension de navigateur

1. **Naviguer vers une page GO**
   - QuickGO: https://www.ebi.ac.uk/QuickGO/term/GO:0012501
   - AmiGO: http://amigo.geneontology.org/amigo/term/GO:0012501

2. **Observer le badge**
   - Un badge apparaît automatiquement en haut à droite
   - Indique le statut: Stable, Modifié, Déprécié, ou Nouveau

3. **Voir les détails**
   - Cliquer sur "Voir les détails" pour une comparaison complète
   - Visualiser les changements de définition, hiérarchie, et relations

## ✨ Fonctionnalités de l'extension

### Détection automatique
- Détecte les identifiants GO sur QuickGO, AmiGO et OLS
- Extraction intelligente depuis l'URL et le contenu

### Affichage visuel
- Badge coloré selon le statut du terme
- Modal détaillé avec comparaison côte à côte
- Visualisation des changements hiérarchiques

### Performance
- Cache local avec durée de validité de 24h
- Statistiques d'utilisation du cache
- Temps de réponse optimisé

### Configuration
- URL du service web personnalisable
- Domaine d'intérêt: Programmed cell death (GO:0012501)
- Activation/désactivation du cache
- Test de connexion intégré

## 🧪 Tests

### Tester le service web

```bash
# Test simple
curl http://localhost:8000/api/term/GO:0012501

# Test avec différences
curl http://localhost:8000/api/term/GO:0012501/diff

# Test de recherche
curl "http://localhost:8000/api/search?q=apoptosis"
```

### Tester l'extension

1. Ouvrir la popup de l'extension
2. Entrer un GO ID dans le champ de test (ex: GO:0012501)
3. Cliquer sur "Tester"
4. Vérifier la réponse JSON affichée

## 📊 Domaine d'étude

- **Programmed cell death** (GO:0012501)

## 🔧 Développement

### Structure du service web

```python
service_web/
├── app/
│   ├── main.py          # Point d'entrée FastAPI
│   ├── routes/          # Endpoints API
│   ├── models/          # Modèles de données
│   └── services/        # Logique métier
└── openapi.yml          # Spécification OpenAPI
```

### Structure de l'extension

```javascript
extension-chrome/
├── manifest.json        # Configuration Manifest V3
├── content.js          # Injection dans les pages
├── background.js       # Service worker (API + cache)
├── popup.html/css/js   # Interface de configuration
└── styles.css          # Styles injectés
```

## 🐛 Dépannage

### Le service web ne démarre pas
- Vérifier que le port 8000 est libre
- Vérifier l'installation des dépendances
- Consulter les logs d'erreur

### L'extension ne détecte pas les termes GO
- Vérifier que le service web est démarré
- Vérifier l'URL dans la configuration de l'extension
- Ouvrir la console du navigateur (F12) pour voir les erreurs

### Erreur de connexion API
- Tester l'API directement: `http://localhost:8000/docs`
- Vérifier les permissions CORS
- Vérifier la configuration de l'extension

## 👥 Équipe

Projet développé dans le cadre du cours INF6253 - Web sémantique (UQO, Hiver 2026)

## 📄 Licence

Projet éducatif - INF6253 UQO

## 🆘 Support

Pour toute question:
1. Consulter la documentation dans chaque dossier
2. Vérifier les logs et la console
3. Tester les composants individuellement
