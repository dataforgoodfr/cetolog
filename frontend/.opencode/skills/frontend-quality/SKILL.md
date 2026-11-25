---
name: Qualité Frontend
description: Utiliser avant de terminer une tâche frontend pour choisir des tests légers, lancer les vérifications et rendre la PR facile à relire.
---

# Qualité Frontend

Utiliser en fin d’implémentation, sur un bugfix et avant de proposer une PR. Les règles projet sont dans `../../../AGENTS.md`.

## Tests

- Si un runner de test existe :
  - écrire le test d’abord pour un bugfix, un helper pur, du parsing/formatage ou un contrat de données ;
  - tester aussi les états et interactions importants : `loading`, `error`, `empty`, formulaire, upload.
- S’il n’existe pas encore :
  - documenter une reproduction manuelle ;
  - proposer l’ajout d’un harnais dans une tâche séparée.
- Plus tard, si le POC se stabilise : E2E Playwright sur les parcours critiques.
- Ne pas imposer une couverture élevée au départ ; couvrir d’abord les chemins critiques.

## Vérifications minimales

Depuis `frontend/` :

```sh
npm run lint
npm run format:check   # si le script existe dans package.json, sinon écrire N/A
npm run build
# npm test si un runner est configuré
```

Puis lancer les tests ciblés sur la zone modifiée, s’ils existent.

## Auto-revue

- Le diff correspond au périmètre annoncé, sans changement sans rapport.
- Pas de code mort, de code commenté ou de commentaire obsolète.
- Contrats publics typés, pas de `any` injustifié.
- États `loading` / `error` / `empty` couverts.
- HTML sémantique et clavier préservés.
- Pas de secret ni de donnée sensible côté client.
- Pas de logique Python/ML dupliquée en JS/TS.

## PR prête

La description doit contenir : contexte, changements, comment tester, checks réellement exécutés, captures si UI change, limites connues et suite à faire. Voir `../frontend-workflow/references/handoff.md`.

## Définition de terminé

- Comportement critique couvert par un test ou une reproduction manuelle documentée.
- Lint, build, formatage et tests présents passent.
- Diff petit enough pour être relu.
- Limites connues écrites, pas cachées.
