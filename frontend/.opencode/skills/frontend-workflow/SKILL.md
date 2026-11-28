---
name: Workflow Frontend
description: Utiliser avant de démarrer ou reprendre une tâche frontend pour cadrer le travail, garder un petit diff et préparer la mainlevée.
---

# Workflow Frontend

Utiliser au début d’une tâche dans `frontend/` et avant de proposer une PR.

## Références à lire

- Lire `../../../AGENTS.md` : règles du projet, source de vérité.
- Lire `references/task-triage.md` pour classifier la tâche S/M/L.
- Lire `references/handoff.md` pour le format de PR et de reprise.

Ces fichiers sont des références chargées à la demande, pas des skills séparés.

## Étapes

1. **Classifier S/M/L** avec la référence `task-triage.md`.
2. **Cadrer** : objectif, hors périmètre, critères de terminé, commande de validation.
3. **Garder le contexte petit** : charger seulement les fichiers et sections nécessaires, pas tout le dépôt.
4. **Travailler sur une branche courte** :
   - `feat/frontend-<sujet>`
   - `fix/frontend-<sujet>`
   - `test/frontend-<sujet>`
   - `docs/frontend-<sujet>`
5. **Commiter par petites étapes** avec des messages clairs, sans changement sans rapport.
6. **Préparer la mainlevée** avec `references/handoff.md`.

## Règles

- Ne pas mélanger feature, refactor, formatage et documentation sauf nécessité.
- Si la tâche est ambiguë ou trop grosse, la découper avant d’implémenter.
- Le skill ne change pas le modèle de la session. Si un modèle rapide est configuré côté opérateur/agent, l’utiliser pour une tâche S bien décrite ; sinon signaler la limite au lieu de prétendre basculer.
- Ne pas toucher au Python/ML sans contrat clair ; le front consomme des contrats, pas des détails d’implémentation.

## Définition de terminé

- Taille S/M/L classée et brief court.
- Périmètre et validation explicites.
- Changements limités à une seule préoccupation.
- PR ou mainlevée assez complète pour un bénévole qui revient après plusieurs jours.
