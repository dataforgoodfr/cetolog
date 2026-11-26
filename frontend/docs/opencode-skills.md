# Skills OpenCode du frontend

Ce document présente les skills OpenCode légers du frontend Cetolog. Il est volontairement hors de `.opencode/skills/` : seul un dossier `SKILL.md` y est enregistré comme skill.

## Utilisation

Lancer OpenCode depuis `frontend/`. Les skills sont alors découverts automatiquement dans `frontend/.opencode/skills/` sans configuration globale. Depuis la racine du monorepo, ils ne sont pas visibles sans configuration supplémentaire.

Les règles du projet restent dans `frontend/AGENTS.md` : elles sont la source de vérité. Les skills ci-dessous sont des aides au travail, pas des remplacements.

## Skills disponibles

- `frontend-workflow` — cadrage, triage S/M/L, branches courtes et mainlevée.
- `frontend-next-react` — implémentation docs-first, boundary serveur/client, types et accessibilité.
- `frontend-quality` — tests légers, vérifications et PR facile à relire.
- `frontend-review` — revue courte, classée par sévérité.

Les invoquer explicitement avec `@frontend-workflow`, `@frontend-next-react`, `@frontend-quality` ou `@frontend-review`, ou laisser l’agent les choisir selon leur description.

## Règles communes

1. Pour Next.js, lire d’abord les docs de la version installée dans `node_modules/next/dist/docs/` depuis `frontend/` ; pour React, consulter `react.dev`. Context7 ensuite seulement.
2. Une tâche, un contexte, une branche courte, une PR ciblée.
3. Garder le contexte petit. Le modèle de la session n’est pas changé par un skill : si un modèle rapide est configuré pour une tâche S bien décrite, l’utiliser, sinon signaler la limite.
4. Commenter le pourquoi, pas l’évident.
5. Garder la frontière Python/ML explicite, pas de secret ni de logique ML dupliquée côté client.

Les fichiers dans `frontend-workflow/references/` sont des références chargées à la demande, pas des sous-skills.
