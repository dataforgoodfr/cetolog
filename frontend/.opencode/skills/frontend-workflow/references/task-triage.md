# Triage des tâches

Classifier avant de charger des fichiers ou de parler de modèle.

| Taille | Exemples                                                              | Approche                                                                                                                               |
| ------ | --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **S**  | typo, formatage, renommage, petite doc, bug évident avec reproduction | Contexte minimal : fichiers cibles seulement. Si un modèle rapide est configuré côté opérateur, l’utiliser ; sinon signaler la limite. |
| **M**  | composant, bug non trivial, petite feature avec tests                 | Contexte et modèle standards.                                                                                                          |
| **L**  | architecture, gros refactor, ambiguïté, risque sécurité/perf          | Découper avant d’implémenter. Modèle plus fort seulement si le blocage, l’ambiguïté ou le risque le justifie.                          |

Un skill ne change pas le modèle de la session : il peut seulement recommander à l’opérateur ou à un agent dédié de le configurer.

## Brief minimal

Utiliser cette forme dans la description de tâche ou le premier commentaire de PR :

```md
Objectif :
Pourquoi maintenant :
Dans le périmètre :
Hors périmètre :
Terminé quand :
Commande de validation :
Questions ouvertes :
```

## Discipline des tokens

- Lire d’abord la plus petite section utile.
- Préférer `grep` et des lectures ciblées aux dumps complets.
- Réutiliser les helpers et conventions existants plutôt que d’inventer des abstractions parallèles.
- Arrêter dès que l’objectif est atteint ; ne pas explorer hors périmètre.
