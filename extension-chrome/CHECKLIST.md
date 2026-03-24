# Checklist - Extension GO Evolution Tracker

## ✅ Fichiers créés

### Fichiers principaux
- [x] `manifest.json` - Configuration Manifest V3
- [x] `content.js` - Script d'injection dans les pages
- [x] `background.js` - Service worker (gestion API et cache)
- [x] `styles.css` - Styles CSS pour l'injection visuelle

### Interface popup
- [x] `popup.html` - Structure HTML de la popup
- [x] `popup.css` - Styles de la popup
- [x] `popup.js` - Logique JavaScript de la popup

### Icônes
- [x] `icons/icon.svg` - Icône vectorielle source
- [x] `icons/README.md` - Instructions pour générer les PNG
- [ ] `icons/icon16.png` - À générer
- [ ] `icons/icon32.png` - À générer
- [ ] `icons/icon48.png` - À générer
- [ ] `icons/icon128.png` - À générer

### Documentation
- [x] `README.md` - Documentation complète
- [x] `INSTALLATION.md` - Guide d'installation
- [x] `.gitignore` - Fichiers à ignorer

## 📋 Fonctionnalités implémentées

### Tâche 3a: Structure de base de l'extension
- [x] Manifest V3 configuré
- [x] Permissions définies
- [x] Content scripts configurés
- [x] Background service worker
- [x] Popup d'action

### Tâche 3b: Détection des termes GO
- [x] Patterns de détection d'URL
- [x] Extraction depuis l'URL
- [x] Extraction depuis le contenu de la page
- [x] Support QuickGO
- [x] Support AmiGO
- [x] Support OLS

### Tâche 3c: Connexion au service web
- [x] Fonction fetchFromAPI
- [x] Gestion des erreurs
- [x] Support des endpoints:
  - [x] `/api/term/{go_id}`
  - [x] `/api/term/{go_id}/diff`
  - [x] `/api/domain/{domain_id}/stats`
  - [x] `/api/search?q={query}`

### Tâche 3d: Interface utilisateur
- [x] Badge visuel avec 4 statuts:
  - [x] Stable (vert)
  - [x] Modifié (orange)
  - [x] Déprécié (rouge)
  - [x] Nouveau (bleu)
- [x] Modal de détails avec:
  - [x] Comparaison des définitions
  - [x] Comparaison de la hiérarchie
  - [x] Relations ajoutées/supprimées
  - [x] Métadonnées et date
- [x] Popup de configuration avec:
  - [x] Configuration URL API
  - [x] Sélection du domaine
  - [x] Activation/désactivation cache
  - [x] Test de connexion

### Tâche 3e: Cache local
- [x] Stockage avec chrome.storage.local
- [x] Durée de validité: 24h
- [x] Fonction getCachedData
- [x] Fonction setCachedData
- [x] Fonction clearCache
- [x] Statistiques du cache:
  - [x] Nombre d'entrées totales
  - [x] Entrées valides
  - [x] Entrées expirées
  - [x] Taille en KB

### Tâche 3f: Tests sur les sites
- [ ] Test sur QuickGO
- [ ] Test sur AmiGO
- [ ] Test de détection automatique
- [ ] Test du badge
- [ ] Test de la modal
- [ ] Test du cache
- [ ] Test de la configuration

## 🔧 Actions à faire avant utilisation

1. **Générer les icônes PNG**
   - Utiliser un convertisseur SVG vers PNG
   - Créer les 4 tailles: 16, 32, 48, 128 pixels
   - Placer dans le dossier `icons/`

2. **Démarrer le service web**
   ```bash
   cd ../service_web
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Charger l'extension**
   - Ouvrir `chrome://extensions/`
   - Activer le mode développeur
   - Charger l'extension non empaquetée
   - Sélectionner le dossier `extension-chrome`

4. **Configurer l'extension**
   - Cliquer sur l'icône de l'extension
   - Vérifier l'URL: `http://localhost:8000`
   - Enregistrer les paramètres

5. **Tester**
   - Visiter https://www.ebi.ac.uk/QuickGO/term/GO:0006281
   - Vérifier l'apparition du badge
   - Tester la modal de détails

## 📊 Métriques de performance attendues

- Temps de détection: < 100ms
- Temps de réponse API (sans cache): 200-500ms
- Temps de réponse (avec cache): < 10ms
- Taille du cache (100 entrées): ~50-100 KB

## 🐛 Points de vérification

- [ ] Le badge apparaît sur QuickGO
- [ ] Le badge apparaît sur AmiGO
- [ ] La modal s'ouvre correctement
- [ ] Les données sont correctement affichées
- [ ] Le cache fonctionne
- [ ] Les statistiques du cache sont exactes
- [ ] La configuration se sauvegarde
- [ ] Le test de connexion fonctionne

## 📝 Notes importantes

- Les icônes PNG doivent être générées manuellement
- Le service web doit être démarré avant d'utiliser l'extension
- L'extension nécessite une connexion au service web
- Le cache améliore significativement les performances
- Compatible Chrome 88+ (Manifest V3)

## 🔄 Version Firefox

Une version Firefox est également disponible dans `../extension-firefox/` avec:
- Manifest V2 (compatible Firefox)
- API `browser.*` au lieu de `chrome.*`
- Même fonctionnalités que la version Chrome
