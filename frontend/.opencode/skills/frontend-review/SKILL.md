---
name: Revue Frontend
description: Utiliser pour relire une PR ou un diff frontend ; rend un retour court, actionnable et classé par sévérité.
---

# Revue Frontend

Utiliser pour une revue de PR, une auto-revue ou une demande de vérification d’un changement frontend. Les règles projet sont dans `../../../AGENTS.md`.

## Entrées

- Objectif et périmètre de la PR.
- Diff et fichiers concernés.
- Commandes déjà exécutées.
- Captures ou étapes de reproduction pour l’UI.

## Grille de revue

### Périmètre et mainlevée

- Le diff correspond-il à la tâche annoncée ? Signaler le hors périmètre.
- Un bénévole peut-il comprendre pourquoi le changement existe et comment le tester ?
- Les limites connues et le travail restant sont-ils écrits ?

### Next.js / React

- Le boundary serveur/client est-il délibéré et minimal ? `"use client"` se propage aux modules importés.
- L’état est-il local et dérivé quand c’est possible ? Y a-t-il des effets inutiles ?
- Les props et contrats publics sont-ils typés ? Y a-t-il un `any` injustifié ?
- Les états `loading`, `error` et `empty` sont-ils traités ?
- Pour une API non triviale, les docs installées de Next et `react.dev` ont-elles été consultées avant Context7 ?

### Code propre et commentaires

- Noms clairs, composants/fonctions focalisés.
- Pas de code mort, duplication ou abstraction prématurée.
- Les commentaires expliquent le pourquoi, pas l’évident.

### Accessibilité et sécurité

- HTML sémantique avant ARIA ; ARIA non redondant.
- Labels, accès clavier, focus visible, textes alternatifs utiles, titre de page unique.
- Aucun secret : `NEXT_PUBLIC_*` et props passées à un Client Component sont visibles dans le navigateur.
- Entrées validées, surtout les uploads. Pas de logique Python/ML copiée sans contrat documenté.

### Vérifications

Depuis `frontend/` :

- `npm run lint`
- `npm run format:check` : lancer le script s’il existe, sinon écrire explicitement `N/A — script absent`
- `npm run build`
- Tests ciblés sur la zone modifiée, s’il existe un runner ; sinon reproduction manuelle documentée

## Format de sortie

```md
## Bloquant

- [fichier:ligne] Problème. Correction proposée.

## À améliorer

- [fichier:ligne] Problème. Correction proposée.

## Optionnel

- [fichier:ligne] Idée ou détail.
```

Garder des commentaires courts et concrets. Dire aussi ce qui est correct quand cela aide le contributeur. S’il n’y a pas de bloquant, le dire clairement.
