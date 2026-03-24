# Guide d'installation - Extension Chrome GO Evolution Tracker

## Installation rapide

### Étape 1: Préparer les icônes

L'extension nécessite des icônes PNG. Vous avez deux options:

#### Option A: Utiliser un outil en ligne (Recommandé)
1. Ouvrir https://cloudconvert.com/svg-to-png
2. Uploader le fichier `icons/icon.svg`
3. Convertir en PNG avec les tailles suivantes:
   - 16x16 pixels → sauvegarder comme `icon16.png`
   - 32x32 pixels → sauvegarder comme `icon32.png`
   - 48x48 pixels → sauvegarder comme `icon48.png`
   - 128x128 pixels → sauvegarder comme `icon128.png`
4. Placer tous les fichiers PNG dans le dossier `icons/`

#### Option B: Créer des icônes simples manuellement
1. Créer 4 images PNG carrées avec un fond violet/bleu et le texte "GO"
2. Tailles: 16x16, 32x32, 48x48, 128x128 pixels
3. Nommer les fichiers: `icon16.png`, `icon32.png`, `icon48.png`, `icon128.png`
4. Placer dans le dossier `icons/`

### Étape 2: Charger l'extension dans Chrome

1. **Ouvrir Chrome** et naviguer vers `chrome://extensions/`

2. **Activer le mode développeur**
   - Cliquer sur le bouton "Mode développeur" en haut à droite

3. **Charger l'extension**
   - Cliquer sur "Charger l'extension non empaquetée"
   - Naviguer vers le dossier `extension-chrome`
   - Sélectionner le dossier et cliquer sur "Sélectionner le dossier"

4. **Vérifier l'installation**
   - L'extension devrait apparaître dans la liste
   - Vous devriez voir l'icône dans la barre d'outils Chrome

### Étape 3: Configurer l'extension

1. **Démarrer le service web** (dans un terminal séparé)
   ```bash
   cd ../service_web
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Configurer l'extension**
   - Cliquer sur l'icône de l'extension dans la barre d'outils
   - Vérifier que l'URL du service web est correcte: `http://localhost:8000`
   - Choisir votre domaine d'intérêt (par défaut: DNA repair)
   - S'assurer que le cache est activé
   - Cliquer sur "Enregistrer les paramètres"

3. **Tester la connexion**
   - Dans la popup, aller à la section "Test de connexion"
   - Entrer un GO ID (exemple: `GO:0006281`)
   - Cliquer sur "Tester"
   - Vous devriez voir une réponse JSON avec les données du terme

### Étape 4: Tester l'extension

1. **Naviguer vers une page GO**
   - QuickGO: https://www.ebi.ac.uk/QuickGO/term/GO:0006281
   - AmiGO: http://amigo.geneontology.org/amigo/term/GO:0006281

2. **Vérifier le badge**
   - Un badge devrait apparaître en haut à droite de la page
   - Il indique le statut du terme (Stable, Modifié, Déprécié, ou Nouveau)

3. **Voir les détails**
   - Cliquer sur "Voir les détails" dans le badge
   - Une fenêtre modale s'ouvre avec la comparaison détaillée

## Dépannage

### Les icônes ne s'affichent pas
- Vérifier que les fichiers PNG existent dans `icons/`
- Vérifier que les noms correspondent exactement: `icon16.png`, `icon32.png`, etc.
- Recharger l'extension: cliquer sur le bouton de rechargement dans `chrome://extensions/`

### Le badge n'apparaît pas sur les pages GO
1. Vérifier que le service web est démarré
2. Ouvrir la console du navigateur (F12) et chercher des erreurs
3. Vérifier que l'URL contient bien un GO ID
4. Tester la connexion depuis la popup de configuration

### Erreur "Failed to fetch"
1. Vérifier que le service web est accessible à `http://localhost:8000`
2. Tester l'API directement dans le navigateur: `http://localhost:8000/api/term/GO:0006281`
3. Vérifier les permissions dans le manifest.json

### L'extension ne se charge pas
1. Vérifier que tous les fichiers sont présents
2. Vérifier qu'il n'y a pas d'erreurs de syntaxe dans les fichiers JS
3. Consulter les erreurs dans `chrome://extensions/`

## Désinstallation

1. Aller à `chrome://extensions/`
2. Trouver "GO Evolution Tracker"
3. Cliquer sur "Supprimer"
4. Confirmer la suppression

## Support

Pour plus d'informations, consulter le fichier README.md principal.
