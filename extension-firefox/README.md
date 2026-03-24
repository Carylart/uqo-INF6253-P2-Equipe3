# Extension Firefox - GO Evolution Tracker

Extension de navigateur pour suivre l'évolution des termes Gene Ontology (GO) entre différentes versions.

## 📋 Description

Version Firefox de l'extension GO Evolution Tracker. Cette extension utilise Manifest V2 pour la compatibilité avec Firefox.

## 🚀 Installation

### Prérequis
- Firefox (version 60+)
- Service web API en cours d'exécution

### Installation temporaire (développement)

1. **Préparer les icônes**
   - Suivre les instructions dans `icons/README.md`
   - Générer les fichiers PNG nécessaires

2. **Charger l'extension dans Firefox**
   - Ouvrir Firefox et naviguer vers `about:debugging`
   - Cliquer sur "Ce Firefox" dans le menu de gauche
   - Cliquer sur "Charger un module complémentaire temporaire"
   - Naviguer vers le dossier `extension-firefox`
   - Sélectionner le fichier `manifest.json`

3. **Configurer l'extension**
   - Cliquer sur l'icône de l'extension dans la barre d'outils
   - Configurer l'URL du service web: `http://localhost:8000`
   - Choisir votre domaine d'intérêt
   - Enregistrer les paramètres

### Installation permanente

Pour installer l'extension de manière permanente, vous devez la signer:

1. **Créer un compte développeur Firefox**
   - Aller sur https://addons.mozilla.org/developers/

2. **Empaqueter l'extension**
   ```bash
   cd extension-firefox
   zip -r ../go-evolution-tracker-firefox.zip *
   ```

3. **Soumettre pour signature**
   - Uploader le fichier ZIP sur addons.mozilla.org
   - Attendre la validation et la signature

## 📖 Utilisation

Identique à la version Chrome. Voir le README principal pour plus de détails.

## 🔧 Différences avec la version Chrome

### API utilisée
- **Chrome**: `chrome.*` API avec Manifest V3
- **Firefox**: `browser.*` API avec Manifest V2

### Service Worker vs Background Script
- **Chrome**: Utilise un service worker (`service_worker`)
- **Firefox**: Utilise un background script classique (`scripts`)

### Permissions
- **Chrome**: `host_permissions` séparées
- **Firefox**: Permissions intégrées dans `permissions`

### Browser Action
- **Chrome**: `action`
- **Firefox**: `browser_action`

## 🐛 Dépannage

### L'extension ne se charge pas
1. Vérifier que tous les fichiers sont présents
2. Vérifier le format du manifest.json
3. Consulter les erreurs dans `about:debugging`

### Erreur de permissions
Firefox peut être plus strict sur les permissions. Vérifier:
- Les URLs dans `permissions`
- Les Content Security Policy

### L'extension disparaît au redémarrage
C'est normal pour une extension temporaire. Pour une installation permanente, elle doit être signée.

## 📚 Ressources

- [Firefox Extension Workshop](https://extensionworkshop.com/)
- [WebExtensions API](https://developer.mozilla.org/fr/docs/Mozilla/Add-ons/WebExtensions)
- [Manifest V2 Documentation](https://developer.mozilla.org/fr/docs/Mozilla/Add-ons/WebExtensions/manifest.json)

## 🔄 Migration vers Manifest V3

Firefox prévoit de supporter Manifest V3 dans le futur. Pour migrer:

1. Changer `manifest_version` à 3
2. Remplacer `browser_action` par `action`
3. Convertir le background script en service worker
4. Mettre à jour les permissions

## 📝 Notes

- Cette extension est compatible avec Firefox 60+
- Les icônes doivent être générées manuellement (voir `icons/README.md`)
- Le cache utilise `browser.storage.local` (limité à 5MB par défaut)

## 👥 Support

Pour toute question, consulter le README principal du projet.
