# Icônes de l'extension

Pour générer les icônes PNG à partir du fichier SVG, vous pouvez utiliser un outil en ligne comme:
- https://cloudconvert.com/svg-to-png
- https://www.adobe.com/express/feature/image/convert/svg-to-png

Ou utiliser ImageMagick en ligne de commande:

```bash
# Installer ImageMagick si nécessaire
# Windows: choco install imagemagick (gestionnaire de packets chocolatey nécessaire)
# Mac: brew install imagemagick
# Linux: sudo apt-get install imagemagick

# Générer les différentes tailles
convert icon.svg -resize 16x16 icon16.png
convert icon.svg -resize 32x32 icon32.png
convert icon.svg -resize 48x48 icon48.png
convert icon.svg -resize 128x128 icon128.png
```

Alternativement, vous pouvez créer des icônes PNG simples avec n'importe quel éditeur d'images.
