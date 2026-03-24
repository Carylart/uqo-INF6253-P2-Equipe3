# Extension Chrome - GO Evolution Tracker

Extension de navigateur pour suivre l'évolution des termes Gene Ontology (GO) entre différentes versions.

## 📋 Description

Cette extension Chrome permet aux chercheurs de visualiser automatiquement les changements apportés aux termes Gene Ontology lorsqu'ils consultent des pages sur QuickGO, AmiGO ou Ontology Lookup Service. Elle affiche un badge indiquant si un terme est stable, modifié, déprécié ou nouveau, et permet d'accéder à une vue détaillée des différences entre versions.

## ✨ Fonctionnalités

### Détection automatique
- Détecte automatiquement les identifiants GO sur les pages web
- Supporte QuickGO, AmiGO 2 et Ontology Lookup Service
- Extraction intelligente depuis l'URL et le contenu de la page

### Affichage des informations
- **Badge visuel** avec 4 statuts possibles:
  - 🟢 **Stable**: Aucun changement entre les versions
  - 🟠 **Modifié**: Définition ou hiérarchie modifiée
  - 🔴 **Déprécié**: Terme marqué comme obsolète
  - 🔵 **Nouveau**: Terme absent de l'ancienne version

### Vue détaillée
- Comparaison côte à côte des définitions
- Visualisation des changements hiérarchiques (parents)
- Liste des relations ajoutées/supprimées
- Métadonnées et liens vers les release notes

### Cache local
- Stockage local des résultats pour améliorer les performances
- Durée de validité: 24 heures
- Statistiques d'utilisation du cache
- Possibilité de vider le cache manuellement

### Configuration
- URL du service web personnalisable
- Choix du domaine d'intérêt (DNA repair, Apoptosis, Lipid metabolism)
- Activation/désactivation du cache
- Test de connexion intégré

## 🚀 Installation

### Prérequis
- Google Chrome ou Chromium (version 88+)
- Service web API en cours d'exécution (voir `../service_web/`)

### Installation en mode développeur

1. **Cloner le projet**
   ```bash
   git clone https://github.com/Carylart/uqo-INF6253-P2-Equipe3.git
   cd uqo-INF6253-P2-Equipe3/extension-chrome
   ```

2. **Générer les icônes** (optionnel)
   ```bash
   cd icons
   # Suivre les instructions dans icons/README.md
   ```

3. **Charger l'extension dans Chrome**
   - Ouvrir Chrome et aller à `chrome://extensions/`
   - Activer le "Mode développeur" (en haut à droite)
   - Cliquer sur "Charger l'extension non empaquetée"
   - Sélectionner le dossier `extension-chrome`

4. **Configurer l'extension**
   - Cliquer sur l'icône de l'extension dans la barre d'outils
   - Configurer l'URL du service web (par défaut: `http://localhost:8000`)
   - Choisir votre domaine d'intérêt
   - Enregistrer les paramètres

## 📖 Utilisation

### Utilisation basique

1. **Démarrer le service web**
   ```bash
   cd ../service_web
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Naviguer vers une page GO**
   - QuickGO: https://www.ebi.ac.uk/QuickGO/term/GO:0006281
   - AmiGO: http://amigo.geneontology.org/amigo/term/GO:0006281

3. **Observer le badge**
   - Un badge apparaît automatiquement en haut à droite
   - Cliquer sur "Voir les détails" pour plus d'informations

### Configuration avancée

#### Modifier l'URL du service web
Si votre API est hébergée ailleurs:
1. Cliquer sur l'icône de l'extension
2. Modifier le champ "URL du service web"
3. Enregistrer

#### Choisir un domaine spécifique
Pour filtrer les résultats par domaine:
1. Ouvrir la popup de configuration
2. Sélectionner un domaine dans la liste déroulante
3. Enregistrer

#### Gérer le cache
Pour vider le cache:
1. Ouvrir la popup de configuration
2. Consulter les statistiques du cache
3. Cliquer sur "Vider le cache"

## 🏗️ Architecture

### Structure des fichiers
```
extension-chrome/
├── manifest.json          # Configuration Manifest V3
├── content.js            # Script injecté dans les pages web
├── background.js         # Service worker (gestion API et cache)
├── popup.html            # Interface de configuration
├── popup.css             # Styles de la popup
├── popup.js              # Logique de la popup
├── styles.css            # Styles injectés dans les pages
├── icons/                # Icônes de l'extension
│   ├── icon.svg
│   ├── icon16.png
│   ├── icon32.png
│   ├── icon48.png
│   └── icon128.png
└── README.md
```

### Flux de données

```
Page Web (QuickGO/AmiGO)
    ↓
Content Script (content.js)
    ↓ [Détection GO ID]
    ↓
Background Script (background.js)
    ↓ [Vérification cache]
    ↓
API REST (/api/term/{go_id}/diff)
    ↓
Triplestore (SPARQL)
    ↓
[Retour des données]
    ↓
Content Script
    ↓
Injection visuelle (Badge + Modal)
```

## 🔧 Développement

### Technologies utilisées
- **Manifest V3**: Dernière version du système d'extensions Chrome
- **Vanilla JavaScript**: Pas de framework externe
- **Chrome Storage API**: Pour la configuration et le cache
- **Fetch API**: Pour les appels HTTP
- **CSS Grid/Flexbox**: Pour les layouts responsives

### Personnalisation

#### Modifier les patterns de détection
Éditer `content.js`:
```javascript
const GO_ID_PATTERNS = [
  /GO[:_](\d{7})/gi,
  // Ajouter vos patterns ici
];
```

#### Changer la durée du cache
Éditer `background.js`:
```javascript
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 heures en ms
```

#### Personnaliser les styles
Éditer `styles.css` pour modifier l'apparence du badge et de la modal.

## 🧪 Tests

### Test manuel

1. **Test de détection**
   - Visiter https://www.ebi.ac.uk/QuickGO/term/GO:0006281
   - Vérifier que le badge apparaît

2. **Test de connexion API**
   - Ouvrir la popup de configuration
   - Entrer un GO ID (ex: GO:0006281)
   - Cliquer sur "Tester"
   - Vérifier la réponse JSON

3. **Test du cache**
   - Visiter une page GO deux fois
   - Vérifier dans la console que la deuxième requête utilise le cache
   - Consulter les statistiques dans la popup

### Sites de test recommandés

- **QuickGO**: https://www.ebi.ac.uk/QuickGO/term/GO:0006281
- **AmiGO**: http://amigo.geneontology.org/amigo/term/GO:0006281
- **OLS**: https://www.ebi.ac.uk/ols/ontologies/go/terms?iri=http://purl.obolibrary.org/obo/GO_0006281

## 📊 Performance

### Métriques typiques
- **Temps de détection**: < 100ms
- **Temps de réponse API** (sans cache): 200-500ms
- **Temps de réponse** (avec cache): < 10ms
- **Taille du cache** (100 entrées): ~50-100 KB

### Optimisations
- Cache local avec IndexedDB
- Requêtes asynchrones non-bloquantes
- Injection CSS minimale
- Lazy loading des détails

## 🐛 Dépannage

### Le badge n'apparaît pas
1. Vérifier que l'extension est activée
2. Vérifier que vous êtes sur un site supporté
3. Ouvrir la console (F12) et chercher des erreurs
4. Vérifier que le GO ID est bien dans l'URL

### Erreur de connexion API
1. Vérifier que le service web est démarré
2. Vérifier l'URL dans la configuration
3. Tester la connexion depuis la popup
4. Vérifier les CORS si l'API est sur un autre domaine

### Le cache ne fonctionne pas
1. Vérifier que le cache est activé dans la configuration
2. Vider le cache et réessayer
3. Vérifier les permissions de stockage dans `chrome://extensions/`

## 🔒 Sécurité et confidentialité

- **Aucune donnée personnelle collectée**
- **Stockage local uniquement** (pas de serveur tiers)
- **Permissions minimales** (storage + activeTab)
- **Requêtes HTTPS** recommandées pour l'API en production

## 📝 Limitations connues

1. **Domaine limité**: L'extension fonctionne mieux avec un sous-domaine spécifique de GO
2. **Offline**: Nécessite une connexion au service web
3. **Navigateurs**: Optimisé pour Chrome (adaptation nécessaire pour Firefox)
4. **Volume**: Performance réduite avec des milliers d'entrées en cache

## 🔮 Améliorations futures

- [ ] Support de Firefox (Manifest V2)
- [ ] Mode offline avec base de données locale
- [ ] Visualisation graphique de la hiérarchie
- [ ] Export des comparaisons en PDF
- [ ] Notifications pour les nouveaux changements
- [ ] Support de plusieurs ontologies (UBERON, CHEBI, etc.)
- [ ] Intégration avec d'autres outils bio-informatiques

## 👥 Contribution

Projet développé dans le cadre du cours INF6253 - Web sémantique (UQO, Hiver 2026).

### Équipe
- Voir le fichier principal README.md du projet

## 📄 Licence

Ce projet est développé à des fins éducatives dans le cadre du cours INF6253.

## 📚 Ressources

- [Chrome Extensions Documentation](https://developer.chrome.com/docs/extensions/)
- [Manifest V3 Migration Guide](https://developer.chrome.com/docs/extensions/mv3/intro/)
- [Gene Ontology](http://geneontology.org/)
- [QuickGO](https://www.ebi.ac.uk/QuickGO/)
- [AmiGO](http://amigo.geneontology.org/)

## 🆘 Support

Pour toute question ou problème:
1. Consulter ce README
2. Vérifier les logs dans la console Chrome
3. Tester la connexion API depuis la popup
4. Contacter l'équipe de développement
