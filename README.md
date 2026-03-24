# uqo-INF6253-P2-Equipe3

## Exécution

1. Installer les dépendances Python pour l'analyse et le service web :
   - `pip install -r requirements.txt`

2. Générer la base RDF EVO depuis les fichiers OWL :
   - `python analyse/evo_builder.py`

3. Démarrer l'API REST :
   - `uvicorn service_web.app.main:app --reload --host 0.0.0.0 --port 8000`

4. Points d'accès :
   - `GET /api/term/{go_id}`
   - `GET /api/term/{go_id}/diff`
   - `GET /api/domain/{domain_id}/stats`
   - `GET /api/search?q={query}`
