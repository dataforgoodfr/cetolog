<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# Règles de contribution frontend

## Documentation d’abord

- Pour Next.js, lire en priorité les guides de la version installée dans `node_modules/next/dist/docs/` depuis `frontend/` et tenir compte des avertissements de dépréciation.
- Pour React, consulter `react.dev` pour les hooks, les Server/Client Components et les patterns.
- La documentation en ligne et Context7 servent à confirmer une API récente ou une lib tierce ; elles ne remplacent pas la version installée.
- Suivre les conventions déjà présentes dans `frontend/` plutôt que des exemples génériques.
- Si des skills OpenCode sont présents dans `.opencode/skills/`, les charger comme aide au cadrage, à l’implémentation, à la qualité et à la revue ; ces règles restent la source de vérité.

## Travail petit et facile à relire

- Une tâche = un contexte = une branche courte = une PR ciblée.
- Préférer `feat/frontend-*`, `fix/frontend-*`, `test/frontend-*` ou `docs/frontend-*`.
- Garder les diffs petits. Ne pas mélanger refactor, feature, formatage et documentation sauf nécessité.
- Une PR indique : pourquoi le changement existe, ce qui change, comment tester, les checks réellement exécutés, les captures d’écran si l’UI change, les limites connues, et l’état/blocants/prochaine étape si le travail est inachevé.

## Qualité du code

- Server Components par défaut. Ajouter `use client` seulement pour l’état navigateur, les événements, les effets/hooks ou les libs tierces qui en ont besoin ; garder les props sérialisables.
- Garder l’état au plus près de son usage ; dériver les valeurs au lieu de dupliquer l’état.
- Typer explicitement les props et les contrats de données publics ; laisser l’inférence pour les variables locales évidentes. Garder `strict: true` et éviter `any` sans justification.
- Gérer les états `loading`, `error` et `empty` pour les données visibles.
- Accessibilité : HTML sémantique, labels, focus visible, textes alternatifs utiles, titre de page unique. Ajouter ARIA seulement quand le HTML ne suffit pas.
- Sécurité : jamais de secrets, clés ni données dans Git ; pas de photos Miraceti publiées sans accord ni de noms de personnes. Respecter `../README.md#les-règles`. Aucune variable `NEXT_PUBLIC_*` sensible et aucune prop secrète passée à un Client Component. Valider les entrées, surtout les uploads.
- Ne pas réimplémenter la logique Python/ML en JavaScript. Consommer un artefact ou un contrat documenté. Le POC Next.js + ONNX côté navigateur reste possible si le contrat, la taille du modèle et les limites sont cadrés.

## Commentaires

- Commenter le pourquoi : règles métier, contraintes non évidentes, arbitrages.
- Ne pas commenter le code évident ligne par ligne.
- Garder les commentaires courts et les mettre à jour ou les supprimer avec le code.

## Tests

- Si un runner de test existe, écrire un test d’abord pour un bugfix, un helper pur, du parsing/formatage ou un contrat de données ; tester aussi les états et interactions importants.
- S’il n’existe pas encore, documenter une reproduction manuelle et proposer l’ajout d’un harnais dans une tâche séparée.
- Avant une PR, depuis `frontend/` : `npm run lint`, `npm run format:check` si le script existe, `npm run build`, puis les tests ciblés présents.
- Ne pas imposer une couverture élevée au départ ; couvrir d’abord les chemins critiques.

## Triage S/M/L et tokens

- **S** : typo, formatage, renommage, petite doc, bug évident avec reproduction. Contexte minimal ; si un modèle rapide est configuré, l’utiliser, sinon noter la limite.
- **M** : composant, bug non trivial, petite feature avec tests. Contexte et modèle standards.
- **L** : architecture, gros refactor, ambiguïté, risque sécurité/perf. Découper avant implémentation ; modèle plus fort seulement en cas de blocage, d’ambiguïté ou de risque élevé.
- Charger seulement les fichiers et sections nécessaires. Préférer un brief court : objectif, fichiers concernés, critère de terminé, commande de validation.
