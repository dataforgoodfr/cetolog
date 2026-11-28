# Plan — page « 5 · Catalogue des individus »

## Pourquoi

Construire l'écran catalogue du frontend à partir du frame Figma « 5 · Catalogue des individus », en consommant la base PostgreSQL introduite par la PR #92. Le portage de la démo Gradio est abandonné : on repart d'un frontend vierge, avec une API Next.js volontairement minimale pour valider rapidement le contrat avec les équipes. Une API FastAPI pourra remplacer cette couche plus tard, une fois le contrat stabilisé.

## Ce que dit le Figma

Frame `5 · Catalogue des individus`, 1280 × 860, dans la section « Catalogue, historique et qualité », juste avant `6 · Fiche individu`.

| Zone                                                                                  | Contenu lu sur le frame                                                                                                                                                   |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Sidebar (240 × 860, fond blanc, bordure droite 2 px `#222222`, padding 24/16, gap 24) | Logo `Cetolog` ; CTA `+ Lancer un matching` ; navigation `Observations`, `Catalogue`, `Historique`, `Qualité`                                                             |
| Title row                                                                             | Titre `Catalogue des individus` ; sous-titre `Tous les individus connus, avec leur photo de référence.` ; `Importer catalogue existant`                                   |
| Filtres                                                                               | `Rechercher` avec placeholder `Identifiant, nom...` ; `Trier par` → `Dernière observation` ; `+ Nouvel individu`                                                          |
| Container                                                                             | Grille de 5 colonnes × 3 lignes visibles (15 cartes). Chaque carte : emplacement photo `Aileron`, identifiant (`TT-0008`, `TT-0012`, `TT-0042`…), texte `12 observations` |
| Actions                                                                               | Boutons du haut de page (`+ Nouvel individu`, `Importer catalogue existant`)                                                                                              |

Le texte `12 observations` est identique sur toutes les cartes : c'est un placeholder. La pagination n'est pas visible dans la portion capturée, à confirmer en bas du frame.

Les libellés et la structure ci-dessus proviennent des noms de calques Figma et d'une lecture OCR du frame ; les couleurs non citées n'ont pas été relevées.

## Données disponibles (PR #92)

La base contient `individuals` (`id`, `code`) et `photos` (`id`, `delivery`, `original_filename`, `individual_id`, `side`, `date`, `site`, `sha256`). Requêtes de contrôle faites en lecture seule :

- 1 529 individus, 2 457 photos ;
- 7 photos sans `individual_id` (noms ne respectant pas `TUTR\d{4}`), exclues des jointures ;
- tous les `side` sont `D` ou `G` (1 205 / 1 252) ;
- 293 dates et 692 sites vides.

Les identifiants du Figma (`TT-0008`) ne sont pas ceux de la base (`TUTR0008`). Hypothèse de travail : afficher `TT-0008` dérivé de `TUTR0008`, à confirmer avec l'association.

Les clés du bucket sont de la forme `curated/catalogue/photos/<livraison>/<code>/<nom-fichier>`. Deux écarts sont à résoudre avant de servir les images :

1. la livraison en base (`catalogue_20261029_miraceti`) ne correspond pas au dossier du bucket (`2026-11-06_catalogue_tt`) ;
2. les noms en base contiennent une date (`D_TUTR0001_20090421_img_8940.jpg`) absente de la clé bucket (`DD_TUTR0001_img_8940.jpg`), et le préfixe de côté passe de `D`/`G` en base à `DD`/`DG` dans le bucket.

Un résolveur de clé explicite est donc nécessaire ; il sera documenté dans la PR images, sans deviner les clés côté navigateur.

## Décisions prises

| Sujet                 | Décision                                                                        |
| --------------------- | ------------------------------------------------------------------------------- |
| API                   | Route handler Next.js pour valider vite ; FastAPI plus tard si le contrat tient |
| Photo de référence    | Côté droit par défaut, sinon gauche                                             |
| Nombre d'observations | Texte placeholder `X observations`, aucun comptage pour l'instant               |
| Taille de page        | 15 cartes, pour coller au frame                                                 |
| Données visibles      | Serveur uniquement ; aucune variable `NEXT_PUBLIC_*` sensible                   |

## Contrat d'API envisagé

`GET /api/catalog/individuals?search=&sort=lastObservation&page=1&pageSize=15`

```json
{
  "items": [
    {
      "code": "TUTR0008",
      "label": "TT-0008",
      "photo": { "imageId": "<id opaquement dérivé de la clé>" },
      "observationsLabel": "X observations"
    }
  ],
  "total": 1529,
  "page": 1,
  "pageSize": 15
}
```

`GET /api/catalog/photos/[imageId]` sert l'image du bucket via une allowlist construite côté serveur, `Content-Type` JPEG/PNG, `Cache-Control: private, no-store`. Aucune URL signée exposée au navigateur.

Esquisse de requête, avec la règle droite puis gauche :

```sql
with reference as (
  select distinct on (p.individual_id)
         p.individual_id, p.id as photo_id,
         p.original_filename, p.delivery
    from photos p
   order by p.individual_id,
            case p.side when 'D' then 0 when 'G' then 1 else 2 end,
            p.date desc nulls last, p.id
)
select i.code, r.original_filename, r.delivery
  from individuals i
  join reference r on r.individual_id = i.id
 where i.code ilike '%' || $1 || '%'
 order by (select max(date) from photos where individual_id = i.id) desc nulls last, i.code
 limit $2 offset $3;
```

Le pool PostgreSQL restera très petit (offre DEV à 5 connexions). Aucune écriture depuis le frontend.

## Découpage en composants et réactivité

### Source de vérité unique

- L'URL est la seule source de vérité pour `search`, `sort` et `page` : pas de copie dans un store, un contexte ou un `useState` qui vivrait à côté.
- `parseCatalogFilters()` et `buildCatalogUrl()` vivent dans `lib/catalog/params.ts` et sont utilisés par la page **et** par la route API : une seule définition des valeurs par défaut, du tri autorisé et de la taille de page.
- Les données renvoyées par `getCatalog()` restent des props. On ne les copie jamais dans un state et on ne les resynchronise jamais avec un `useEffect`.
- Les valeurs dérivées (`label` `TT-xxxx`, `observationsLabel`) sont produites côté serveur dans la réponse API. Le navigateur n'a aucun calcul à faire sur la liste.

### Arborescence

```text
app/catalogue/page.tsx                    Server, async : await searchParams → parse → getCatalog
app/catalogue/loading.tsx                 Server : squelette pendant la navigation
app/catalogue/error.tsx                   Client : message d'erreur + bouton « réessayer »
components/catalog/Sidebar.tsx            Server, statique (à remonter dans le layout partagé plus tard)
components/catalog/CatalogHeader.tsx      Server : titre, sous-titre, « Importer catalogue existant »
components/catalog/CatalogFiltersBar.tsx  Client : le seul composant interactif des filtres
components/catalog/CatalogResults.tsx     Server : choix résultat / vide / erreur
components/catalog/IndividualGrid.tsx     Server : grille 5 colonnes
components/catalog/IndividualCard.tsx     Server : vignette + identifiant + `X observations`
components/catalog/Pagination.tsx         Server : liens `<Link>` vers la page suivante
lib/catalog/params.ts                     parse / build d'URL, partagé page ↔ API
lib/catalog/get-catalog.ts                `import 'server-only'`, lecture PostgreSQL
```

Flux :

```text
?search=&sort=lastObservation&page=1
  → page.tsx (await searchParams) → parseCatalogFilters → getCatalog(filters)
  → CatalogResults (props sérialisables) → IndividualGrid → IndividualCard
  → CatalogFiltersBar → router.replace(buildCatalogUrl(nextFilters))
```

### Réactivité sans duplication

Mode par défaut : la page est un Server Component, la recherche part via un `<form method="get">` et le tri / la pagination via des `<Link>`. Zéro state client pour les filtres ; `loading.tsx` couvre l'attente. C'est le mode le plus simple à valider avec les équipes.

Si une recherche instantanée est demandée ensuite, un seul Client Component (`CatalogFiltersBar`) gère l'interaction :

- `<input>` **non contrôlé** (`defaultValue={filters.search}`) : le DOM porte la valeur saisie, il n'existe pas de second state React pour la même donnée ;
- `onChange` → `startTransition(() => router.replace(buildCatalogUrl({ ...filters, search, page: 1 }), { scroll: false }))` : la frappe reste prioritaire, la navigation peut être interrompue ;
- `useTransition().isPending` alimente `aria-busy` et un léger grisage, sans désactiver le champ ;
- la remise à zéro de la page à `1` à chaque changement de recherche est faite au même endroit, pour éviter deux chemins qui écrivent l'URL ;
- `useDeferredValue` n'est ajouté que si la grille passe un jour côté client et que son rendu devient lent ; il n'y a pas de timer de debounce à maintenir.

Un retour navigateur est géré par le routeur : l'URL change, la page serveur est re-rendue avec les nouvelles props. On évite ainsi le classique « state miroir synchronisé par useEffect ».

### Mémoïsation ciblée

- Les cartes et la grille sont des composants serveur : `React.memo` n'a rien à y faire, elles ne se re-rendent pas côté client.
- Si une carte devient interactive (client), l'envelopper dans `memo` avec des **props primitives** (`code`, `label`, `imageId`, `observationsLabel`). Pas d'objet littéral ni de callback inline en props, sinon `memo` ne compare plus rien d'utile.
- `useMemo` uniquement pour un calcul réellement coûteux. Ici les 15 cartes sont déjà prêtes à l'arrivée : aucun `useMemo` obligatoire, et le compilateur React peut prendre le relais.
- Clés React stables : le `code` de l'individu, jamais l'index du tableau.
- Vignettes `<img loading="lazy" decoding="async" width height>` servies par `/api/catalog/photos/[imageId]`, sans optimisation `next/image` pour ne pas contourner l'allowlist serveur.

## Découpage en PR

1. `docs/catalogue-contract` — ce plan, les décisions et le contrat d'API.
2. `feat/catalog-api` — dépendance `pg`, module de lecture serveur, route `/api/catalog/individuals`, contrat typé, `DATABASE_URL` lu depuis l'add-on. Reproduction manuelle documentée : recherche, tri, pagination, cas vide.
3. `feat/catalog-images` — résolveur de clé + route proxy allowlistée, 404 hors contrat, 503 si objet absent.
4. `feat/catalog-ui` — page `/catalogue` : Sidebar, Title row, Filtres, grille de 15 cartes, états loading / empty / error. Elle peut être découpée en trois PR si le diff grandit : (a) squelette serveur + grille à partir des props, (b) barre de filtres et navigation URL, (c) carte, vignette et pagination.
5. `style/catalog-wireframe` — tokens du wireframe centralisés dans `globals.css`, suppressibles en retirant leur import du layout.
6. `docs/catalog-env` — variables Clever Cloud, lien avec l'add-on PostgreSQL, rebuild.
7. `feat/catalog-auth` (si nécessaire) — Basic Auth côté serveur, même comportement que la démo Gradio.

Chaque PR reste ciblée, avec des commentaires courts expliquant le pourquoi. Pas de runner de tests dans le frontend : documenter la reproduction manuelle jusqu'à l'ajout d'un harnais.

## Dernière étape : PR globale et déploiement staging

Une fois les PR ci-dessus prêtes, créer une branche d'intégration et une PR « meta », comme pour la phase 2 abandonnée :

```bash
cd /Users/dams/Projects/cetolog
git switch -c test/catalogue-staging origin/main
for b in docs/catalogue-contract feat/catalog-api feat/catalog-images \
         feat/catalog-ui style/catalog-wireframe docs/catalog-env feat/catalog-auth; do
  git merge --no-edit "$b"
done
cd frontend && npm run format:check && npm run lint && npm run build
git push -u origin test/catalogue-staging
```

Ouvrir la PR meta vers `main`, puis déployer **la branche**, sans merger :

```bash
cd /Users/dams/Projects/cetolog
git switch test/catalogue-staging
clever deploy -a <app-staging>
```

À ce jour il n'existe pas d'app de staging dans l'organisation : seulement `cetolog-demo-ml` et `cetolog-web`. Deux options :

- **Recommandé** : créer `cetolog-web-staging`, y renseigner `DATABASE_URL` (add-on `cetolog-db-dev`), les variables S3 et l'auth, puis déployer la branche d'intégration dessus. Cela évite de toucher `cetolog-web`.
- **Temporaire** : déployer la branche sur `cetolog-web`, comme pour la PR #90, en prévenant l'équipe.

Vérifications attendues après déploiement : `GET /api/catalog/individuals` (401 sans identifiants si l'auth est active, puis 200), une vignette en `200 image/jpeg`, et la page `/catalogue` en 200. La PR meta est fermée après le test ; les PR individuelles restent la source de vérité pour la revue.

Le déploiement n'est pas encore exécuté : il n'existe pour l'instant que ce plan, sans code d'API ni d'écran à tester.
