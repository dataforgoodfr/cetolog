---
name: Frontend Next React
description: Utiliser pour créer ou modifier un composant, une page, une route, de l’état ou de la logique client dans frontend/.
---

# Frontend Next React

Utiliser pour l’implémentation dans `frontend/`. Les règles détaillées du projet sont dans `../../../AGENTS.md` (depuis ce skill) ou `AGENTS.md` depuis `frontend/`.

## Ordre des documentation

1. Pour Next.js, lire d’abord les guides de la version installée : `../../../node_modules/next/dist/docs/` depuis ce skill, ou `node_modules/next/dist/docs/` depuis `frontend/`.
2. Pour React, consulter `react.dev` pour les hooks et les patterns Server/Client.
3. Vérifier les conventions existantes dans `frontend/` et `../../../AGENTS.md`.
4. Utiliser Context7 ensuite seulement, pour confirmer une API récente ou une lib tierce.

Ne pas se fier uniquement à des exemples mémorisés : la version installée peut différer.

## Points d’attention

- Server Components par défaut. `use client` seulement pour l’état navigateur, événements, effets/hooks, libs tierces ou APIs navigateur. Le boundary se propage aux modules importés ; garder les props sérialisables.
- Garder l’état près de son usage ; dériver les valeurs au lieu de les dupliquer.
- Typer explicitement les props et contrats publics ; laisser l’inférence pour les locaux évidents. Garder `strict: true`, éviter `any` sans justification.
- Gérer `loading`, `error` et `empty` pour les données visibles.
- HTML sémantique d’abord : `button`, `label`, `nav`, `main`, listes, titres. Ajouter ARIA seulement si nécessaire. Vérifier labels, focus visible, textes alternatifs et titre de page unique.
- Valider les entrées, surtout les uploads. Aucun secret : `NEXT_PUBLIC_*` et les props passées à un Client Component sont visibles dans le navigateur.
- Ne pas réimplémenter le Python/ML en JS. Consommer un artefact ou contrat documenté ; le POC Next.js + ONNX reste possible s’il est cadré.
- Noms clairs, fonctions courtes, early returns, abstractions seulement quand elles sont justifiées.
- Commenter le pourquoi, pas l’évident.

## Définition de terminé

- Ordre des docs respecté pour les choix d’API non triviaux.
- Boundary serveur/client délibéré et minimal.
- Types publics, états UI et accessibilité de base traités.
- Aucun secret, aucune logique ML dupliquée, aucune entrée non validée introduite.
- `npm run lint`, `npm run format:check` si le script existe, et `npm run build` passent.
