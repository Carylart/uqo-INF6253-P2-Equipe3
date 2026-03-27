@echo off
REM Script pour charger les données RDF dans Apache Jena Fuseki
REM Utilisation: load_data.bat [fuseki_url] [dataset_name] [rdf_file]

setlocal enabledelayedexpansion

set FUSEKI_URL=%1
if "%FUSEKI_URL%"=="" set FUSEKI_URL=http://localhost:3030

set DATASET=%2
if "%DATASET%"=="" set DATASET=go_evolution

set RDF_FILE=%3
if "%RDF_FILE%"=="" set RDF_FILE=go_evo.ttl

echo Chargement de %RDF_FILE% dans le dataset %DATASET% sur %FUSEKI_URL%...

REM Attendre que Fuseki soit prêt
echo Attente du démarrage de Fuseki...
:wait_loop
curl -f -s "%FUSEKI_URL%/$/ping" >nul 2>&1
if errorlevel 1 (
    echo Fuseki pas encore prêt, attente...
    timeout /t 2 /nobreak >nul
    goto wait_loop
)

echo Fuseki est prêt. Chargement des données...

REM Charger le fichier RDF
curl -X POST --data-binary @%RDF_FILE% -H "Content-Type: text/turtle" "%FUSEKI_URL%/%DATASET%/data"

if %errorlevel% equ 0 (
    echo Données chargées avec succès!
    echo Interface web disponible sur: %FUSEKI_URL%
    echo SPARQL endpoint: %FUSEKI_URL%/%DATASET%/sparql
) else (
    echo Erreur lors du chargement des données
    exit /b 1
)