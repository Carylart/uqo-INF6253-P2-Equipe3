"""
INF6253 - Projet P2 : Pipeline principale d'analyse GO
-------------------------------------------------------
Point d'entrée unique du projet. Orchestre les 4 tâches de la Partie 1 :

  Tâche 1 (analyse_go.py)    — Structure générale des deux versions
  Tâche 2 (analyse_go.py)    — Analyse quantitative du domaine apoptose
  Tâche 3 (analyse_go.py)    — Analyse qualitative sur 5 termes
  Tâche 4 (raisonneur_go.py) — Raisonnement OWL + détection d'incohérences

Principe : les fichiers .owl ne sont chargés qu'une seule fois par
traitement_go.charger_et_preparer(), puis les graphes sont transmis
par référence à toutes les étapes suivantes.

Structure attendue :
    analyse/
      main.py
      traitement_go.py
      analyse_go.py
      raisonneur_go.py
      data/
        go-base-20251010.owl     <- fichiers source à fournir
        go-base-20260123.owl
      reports/                   <- créé automatiquement

Fichiers générés :
    analyse/data/
      apoptose-20251010.owl      <- sous-graphe apoptose Oct 2025
      apoptose-20260123.owl      <- sous-graphe apoptose Jan 2026

    analyse/reports/
      structure_oct2025.txt      <- tâche 1
      structure_jan2026.txt      <- tâche 1
      rapport_quantitatif.txt    <- tâche 2
      rapport_qualitatif.txt     <- tâche 3
      raisonnement_oct2025.txt   <- tâche 4
      raisonnement_jan2026.txt   <- tâche 4

Usage (depuis le dossier qui contient analyse/) :
    python analyse/main.py

Prérequis :
    pip install rdflib owlrl
"""

import sys
import time
from pathlib import Path

# Ajout du dossier analyse/ au path Python pour les imports locaux
sys.path.insert(0, str(Path(__file__).parent))

try:
    from traitement_go import charger_et_preparer, log_progress
    from analyse_go    import run_analyse
    from raisonneur_go import run_raisonnement
except ImportError as e:
    print(f"Erreur d'import : {e}")
    print("Assurez-vous que tous les scripts sont dans le meme dossier que main.py")
    sys.exit(1)


def main():
    """
    Orchestre la pipeline complète des 4 tâches de la Partie 1.

    Étape 1 — traitement_go.charger_et_preparer()
      Charge go-base-20251010.owl et go-base-20260123.owl une seule fois.
      Extrait les descendants de GO:0012501 (BFS via index inverse).
      Construit et sauvegarde les sous-graphes apoptose en .owl.

    Étape 2 — analyse_go.run_analyse()
      Tâche 1 : structure générale de chaque version (graphes complets)
      Tâche 2 : analyse quantitative du domaine (sous-graphes)
      Tâche 3 : analyse qualitative des 5 termes (sous-graphes)

    Étape 3 — raisonneur_go.run_raisonnement()
      Tâche 4 : raisonnement owlrl/RDFS_Semantics sur chaque sous-graphe
               temps de raisonnement noté, incohérences détectées et reportées

    Les graphes ne sont chargés qu'une seule fois et transmis par référence.
    """
    t_start = time.time()

    log_progress("=" * 65)
    log_progress("  INF6253 - Pipeline d'analyse Gene Ontology - Partie 1")
    log_progress("  Domaine : Apoptose (programmed cell death - GO:0012501)")
    log_progress("=" * 65)

    # Étape 1 : chargement et préparation (vérification des fichiers incluse)
    log_progress("\n[ETAPE 1/3] Chargement et preparation")
    log_progress("-" * 65)
    data = charger_et_preparer()

    # Étape 2 : tâches 1, 2, 3
    log_progress("\n[ETAPE 2/3] Analyses comparative (taches 1, 2, 3)")
    log_progress("-" * 65)
    run_analyse(data)

    # Étape 3 : tâche 4
    log_progress("\n[ETAPE 3/3] Raisonnement OWL (tache 4)")
    log_progress("-" * 65)
    run_raisonnement(data)

    # Résumé
    elapsed = time.time() - t_start
    log_progress("\n" + "=" * 65)
    log_progress(f"  Pipeline terminee en {elapsed:.1f}s")
    log_progress("=" * 65)
    log_progress("\nFichiers generes dans analyse/data/ :")
    log_progress("  - apoptose-20251010.owl")
    log_progress("  - apoptose-20260123.owl")
    log_progress("\nRapports generes dans analyse/reports/ :")
    log_progress("  - structure_oct2025.txt      (tache 1)")
    log_progress("  - structure_jan2026.txt      (tache 1)")
    log_progress("  - rapport_quantitatif.txt    (tache 2)")
    log_progress("  - rapport_qualitatif.txt     (tache 3)")
    log_progress("  - raisonnement_oct2025.txt   (tache 4)")
    log_progress("  - raisonnement_jan2026.txt   (tache 4)")


if __name__ == "__main__":
    main()
