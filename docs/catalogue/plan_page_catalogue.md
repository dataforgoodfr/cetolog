# Plan — page « 5 · Catalogue des individus »

## Pourquoi

Construire l'écran catalogue du frontend à partir du frame Figma « 5 · Catalogue des individus », en consommant la base PostgreSQL introduite par la PR #92. Le portage de la démo Gradio est abandonné : on repart d'un frontend vierge, avec une API Next.js volontairement minimale pour valider rapidement le contrat avec les équipes. Une API FastAPI pourra remplacer cette couche plus tard, une fois le contrat stabilisé.

## Ce que dit le Figma

Frame `5 · Catalogue des individus`, 1280 × 860, dans la section « Catalogue, historique et qualité », juste avant `6 · Fiche individu`.

| Zone                                                                                  | Contenu lu sur le frame                                                                                                                                                                   |
| ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Sidebar (240 × 860, fond blanc, bordure droite 2 px `#222222`, padding 24/16, gap 24) | Logo `Cetolog` ; CTA `+ Lancer un matching` ; navigation `Observations`, `Catalogue`, `Historique`, `Qualité`                                                                             |
| Title row                                                                             | Titre `Catalogue des individus` ; sous-titre `Tous les individus connus, avec leur photo de référence.` ; `Importer catalogue existant`                                                   |
| Filtres                                                                               | `Rechercher` avec placeholder `Identifiant, nom...` ; `Trier par` → `Dernière observation` ; `+ Nouvel individu`                                                                          |
| Container                                                                             | Grille de 5 colonnes × 3 lignes visibles (15 cartes). Chaque carte : emplacement photo `Aileron`, identifiant (`TT-0008`, `TT-0012`, `TT-0042`… sur la maquette), texte `12 observations` |
| Actions                                                                               | Pagination du catalogue (groupe identifié comme tel par le porteur du frame)                                                                                                              |

Le texte `12 observations` est identique sur toutes les cartes : c'est un placeholder. Le groupe `Actions` est la pagination : elle est donc incluse dès la première version, avec 15 cartes par page.

Les libellés et la structure ci-dessus proviennent des noms de calques Figma et d'une lecture OCR du frame ; les couleurs non citées n'ont pas été relevées.

## Données disponibles (PR #92)

La base contient `individuals` (`id`, `code`) et `photos` (`id`, `delivery`, `original_filename`, `individual_id`, `side`, `date`, `site`, `sha256`). Requêtes de contrôle faites en lecture seule :

- 1 529 individus, 2 457 photos ;
- 7 photos sans `individual_id` (noms ne respectant pas `TUTR\d{4}`), exclues des jointures ;
- tous les `side` sont `D` ou `G` (1 205 / 1 252) ;
- 293 dates et 692 sites vides.

Les identifiants `TT-0008` de la maquette ne sont pas ceux de la base (`TUTR0008`). On affiche le `code` de la base **tel quel** : aucune transformation vers `TT-xxxx`, décision confirmée. Le wireframe reste une référence de mise en page, pas de nommage.

Les clés du bucket sont de la forme `curated/catalogue/photos/<livraison>/<code>/<nom-fichier>`. Deux écarts sont à résoudre avant de servir les images :

1. la livraison en base (`catalogue_20261029_miraceti`) ne correspond pas au dossier du bucket (`2026-11-06_catalogue_tt`) ;
2. les noms en base contiennent une date (`D_TUTR0001_20090421_img_8940.jpg`) absente de la clé bucket (`DD_TUTR0001_img_8940.jpg`), et le préfixe de côté passe de `D`/`G` en base à `DD`/`DG` dans le bucket.

Un résolveur de clé explicite est donc nécessaire ; il sera documenté dans la PR images, sans deviner les clés côté navigateur.

## Décisions prises

| Sujet                 | Décision                                                                        |
| --------------------- | ------------------------------------------------------------------------------- |
| API                   | Route handler Next.js pour valider vite ; FastAPI plus tard si le contrat tient |
| Identifiant affiché   | `code` de la base tel quel (`TUTR0008`), pas de `TT-xxxx` dérivé                |
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
      "photo": {
        "id": "<identifiant opaque>",
        "url": "/api/catalog/photos/<identifiant opaque>",
        "alt": "Photo de TUTR0008"
      },
      "observationsLabel": "X observations"
    }
  ],
  "total": 1529,
  "page": 1,
  "pageSize": 15,
  "totalPages": 102
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

## Indépendance vis-à-vis de l'API et typage

L'affichage ne connaît ni Next ni FastAPI : il consomme des types et une interface. Le jour où FastAPI remplace la route Next, seule l'implémentation du gateway change.

```ts
// src/types/catalog.ts — aucun import Next/FastAPI, valeurs sérialisables
export type CatalogSort = "lastObservation";

export type CatalogQuery = {
  search: string;
  sort: CatalogSort;
  page: number;
  pageSize: number;
};

export type CatalogPhoto = { id: string; url: string; alt: string };

export type CatalogIndividual = {
  code: string;
  photo: CatalogPhoto;
  observationsLabel: string;
};

export type CatalogPage = {
  items: readonly CatalogIndividual[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
};

export type CatalogErrorBody = {
  code: "INVALID_QUERY" | "UPSTREAM_UNAVAILABLE";
  message: string;
};
```

`photo.url` est une URL relative **opaque** fournie par le gateway : l'UI fait `<img src={photo.url}>` sans savoir qu'elle pointe aujourd'hui vers `/api/catalog/photos/[imageId]`. C'est ce qui permet de remplacer le transport sans toucher aux composants.

```ts
// src/lib/catalog/gateway.ts — frontière unique entre l'UI et la source de données
export interface CatalogGateway {
  list(query: CatalogQuery): Promise<CatalogPage>;
}
```

Implémentations :

- `src/lib/catalog/postgres-gateway.ts` (`import 'server-only'`) : `pg`, requête SQL et mapping vers `CatalogPage`. C'est l'implémentation utilisée aujourd'hui.
- `src/lib/catalog/http-gateway.ts` (plus tard) : `fetch` vers FastAPI, avec validation de la réponse par `parseCatalogPage(payload: unknown): CatalogPage`. Pas de `as CatalogPage` aveugle à la frontière réseau.
- `src/lib/catalog/index.ts` : un seul point qui choisit le gateway ; c'est la seule ligne à modifier pour la migration.

La route Next.js reste un **adaptateur-mince** pour valider le contrat avec les équipes : `GET` parse la query, appelle le même gateway et répond avec `satisfies CatalogPage`. La page serveur appelle le gateway directement, sans `fetch` HTTP interne. Les composants n'importent jamais `pg`, `next/server` ni une URL d'API.

Typage des frontières :

- `page.tsx` : `searchParams: Promise<Partial<Record<string, string | string[] | undefined>>>`, puis `parseCatalogQuery()` retourne un `CatalogQuery` validé ;
- route individus : `GET(request: Request): Promise<Response>` ; réponses d'erreur typées `CatalogErrorBody` ;
- route image : `context: { params: Promise<{ imageId: string }> }` (les `params` sont une Promise dans Next 16), `Promise<Response>` en retour ;
- `tsconfig.json` reste en `strict: true`, sans `any` dans le code de l'écran ; les seules conversions se font après validation explicite aux frontières (URL, JSON, lignes SQL).

## Recommandations pour l'API définitive (plus tard)

Relevé en lecture seule sur `cetolog-db-dev` : `pg_trgm`, `unaccent`, `citext` et `vector` sont déjà installés ; les seuls index sont `individuals(id)`, `individuals(code)` et `photos(id)`. Il n'y a **aucun index** sur `photos.individual_id`, `side`, `date`, `sha256` ou `delivery`, toutes les colonnes textuelles sont nullable, et 6 groupes de `sha256` dupliqués représentent 6 lignes redondantes. La requête d'écran actuelle fait un `DISTINCT ON` + comptage + `ILIKE` sans index : correct à 1 529 individus, fragile ensuite.

### 1. Séparer écriture et lecture (CQRS-lite)

- **Écriture** : l'ingestion Python (Alembic + script de chargement) reste l'unique propriétaire des tables sources.
- **Lecture** : une vue `catalog_cards` expose une ligne par individu avec `individual_id`, `code`, `reference_photo_id`, `last_observation_date`, `photo_count` et `search_text`. Le gateway ne requête que cette vue.
- Commencer par une **vue simple** ; passer en `MATERIALIZED VIEW` avec index uniquement si la latence devient un problème. Le contrat d'API ne change pas dans l'un ou l'autre cas.
- Index utiles côté-source : `(individual_id, date desc)` pour le `DISTINCT ON`, `(last_observation_date desc, code)` pour le tri, `gin (search_text gin_trgm_ops)` pour la recherche.

### 2. Compléter le modèle dans une migration Alembic dédiée

- `deliveries(id, label, imported_at, manifest_key, is_active)` et `photos.delivery_id` : la livraison devient une entité, plus une simple chaîne libre.
- `sites(id, code, label)` et `photos.site_id` : permet de filtrer par site sans comparer des textes.
- `observations(id, individual_id, date, site_id)` et `photos.observation_id` : le compteur d'observations deviendra un vrai `count(*)` le jour où Miraceti valide la règle. Le placeholder `X observations` reste jusqu'à cette migration.
- `photos` : ajouter `storage_key` (unique, non nul), `content_type`, `width`, `height`, `is_reference`, index partiel `unique (individual_id) where is_reference` et index sur `sha256`. La règle droite puis gauche est appliquée **à l'ingestion**, pas à chaque requête d'affichage.
- `individuals` : ajouter `display_name` (nullable) et `search_text` entretenu par trigger (`lower(unaccent(code || ' ' || display_name))`). `unaccent` n'étant pas immutable, on évite la colonne générée et l'index d'expression direct.
- `ingest_errors` : y placer les 7 noms non reconnus (`TTGC2050`, `TUTR05558`, `TUTR1260-fa`…) au lieu de laisser `individual_id` à `NULL`. Une fois la table nettoyée, `photos.individual_id` peut devenir `NOT NULL`.

Aucune modification de la migration déjà fusionnée `0879077b4f35` ; une seule personne applique les migrations ; `spatial_ref_sys` reste intact.

### 3. Recherche en deux niveaux

- **Niveau 1, suffisant pour le catalogue** : préfixe du code + trigramme sur `search_text` avec `pg_trgm` (`search_text % :q` ou `ILIKE '%:q%'`), insensible aux accents grâce à `unaccent`. Le placeholder `Identifiant, nom...` suppose d'ajouter `display_name` avant de promettre la recherche par nom.
- **Niveau 2, plus tard seulement** : `tsvector` entretenu par trigger pour la recherche plein texte (config `french`) et, si le besoin se confirme, `pgvector` pour une similarité sémantique. La extension `vector` est déjà là, mais elle ne doit pas servir à filtrer le catalogue.
- Garder un tri déterministe `last_observation_date desc nulls last, code asc` pour que la pagination ne saute pas de carte.

### 4. Contrat d'API stable

- Versionner les routes : `/api/v1/catalog/individuals`, `/api/v1/catalog/individuals/[code]` (fiche individu du frame 6), `/api/v1/catalog/photos/[id]`, puis `/observations` et `/filters/sites` quand les tables existent.
- Conserver l'enveloppe `{ items, total, page, pageSize, totalPages }` et les types `src/types/catalog.ts` comme source de vérité tant que l'API est Next. Le jour de FastAPI, générer les types TypeScript depuis le schéma OpenAPI (`openapi-typescript`) et garder `CatalogGateway` inchangé : aucun composant ne doit bouger.
- Erreurs typées `CatalogErrorBody` (400 query invalide, 404 inconnu, 503 source indisponible), `ETag` sur les listes, `Cache-Control: private, no-store` sur les images.
- Rôle PostgreSQL **lecture seule** pour l'API ; aucune écriture depuis le frontend ; pool dimensionné pour l'offre DEV à 5 connexions.
- Si les pages deviennent profondes, remplacer `OFFSET` par une pagination par curseur sur `(last_observation_date, code)` sans changer le contrat d'affichage.

## Découpage en composants et réactivité

### Source de vérité unique

- L'URL est la seule source de vérité pour `search`, `sort` et `page` : pas de copie dans un store, un contexte ou un `useState` qui vivrait à côté.
- `parseCatalogQuery()` et `buildCatalogUrl()` vivent dans `src/lib/catalog/params.ts` et sont utilisés par la page **et** par la route API : une seule définition des valeurs par défaut, du tri autorisé et de la taille de page.
- Les données renvoyées par `gateway.list()` restent des props. On ne les copie jamais dans un state et on ne les resynchronise jamais avec un `useEffect`.
- Les valeurs dérivées (dont `observationsLabel`) sont produites côté serveur par le gateway. Le navigateur n'a aucun calcul à faire sur la liste.

### Arborescence

```text
src/app/catalogue/page.tsx                  Server, async : await searchParams → parse → gateway.list
src/app/catalogue/loading.tsx               Server : squelette pendant la navigation
src/app/catalogue/error.tsx                 Client : message d'erreur + bouton « réessayer »
src/components/catalog/Sidebar.tsx          Server, statique (à remonter dans le layout partagé plus tard)
src/components/catalog/CatalogHeader.tsx    Server : titre, sous-titre, « Importer catalogue existant »
src/components/catalog/CatalogFiltersBar.tsx Client : le seul composant interactif des filtres
src/components/catalog/CatalogResults.tsx   Server : choix résultat / vide / erreur
src/components/catalog/IndividualGrid.tsx   Server : grille 5 colonnes
src/components/catalog/IndividualCard.tsx   Server : vignette + identifiant + `X observations`
src/components/catalog/Pagination.tsx       Server : le groupe `Actions`, liens vers les pages
src/lib/catalog/params.ts                   parse / build d'URL, partagé page ↔ route API
src/lib/catalog/gateway.ts                  interface CatalogGateway
src/lib/catalog/index.ts                    choix de l'implémentation
src/lib/catalog/postgres-gateway.ts         `import 'server-only'`, lecture PostgreSQL
src/types/catalog.ts                        types sérialisables du contrat
```

Flux :

```text
?search=&sort=lastObservation&page=1
  → page.tsx (await searchParams) → parseCatalogQuery → gateway.list(query)
  → CatalogResults (props sérialisables) → IndividualGrid → IndividualCard
  → CatalogFiltersBar → router.replace(buildCatalogUrl(nextFilters))
```

### Pagination (groupe `Actions`)

La pagination est un composant serveur, alimenté par le `CatalogPage` renvoyé par le gateway :

```ts
type PaginationProps = Pick<
  CatalogPage,
  "page" | "pageSize" | "total" | "totalPages"
> & { buildHref: (page: number) => string };
```

- `totalPages` est calculé côté serveur (`Math.ceil(total / pageSize)`) : le composant ne refait pas le calcul et ne garde pas de state local.
- Précédent / suivant sont des `<Link>` construits par `buildCatalogUrl()`, donc l'URL reste la seule source de vérité. Boutons désactivés aux bornes, sans navigation morte.
- `aria-current="page"` sur la page courante ; les liens gardent `search` et `sort` pour qu'un changement de page ne perde pas les filtres.
- Un changement de recherche ou de tri remet `page` à `1` au même endroit (dans `buildCatalogUrl()`), pour éviter une page vide après filtrage.
- Le nombre total de pages avec 1 529 individus et 15 par page est de 102 : l'affichage reste une pagination compacte, sans liste exhaustive de liens.

Les props des autres composants sont typées depuis le contrat : `IndividualCardProps = CatalogIndividual`, `IndividualGridProps = { items: CatalogPage["items"] }`, `CatalogFiltersBarProps = { filters: CatalogQuery }`.

### Réactivité sans duplication

Mode par défaut : la page est un Server Component, la recherche part via un `<form method="get">` et le tri / la pagination via des `<Link>`. Zéro state client pour les filtres ; `loading.tsx` couvre l'attente. C'est le mode le plus simple à valider avec les équipes.

Si une recherche instantanée est demandée ensuite, un seul Client Component (`CatalogFiltersBar`) gère l'interaction :

- `<input>` **non contrôlé** (`defaultValue={query.search}`) : le DOM porte la valeur saisie, il n'existe pas de second state React pour la même donnée ;
- `onChange` → `startTransition(() => router.replace(buildCatalogUrl({ ...query, search, page: 1 }), { scroll: false }))` : la frappe reste prioritaire, la navigation peut être interrompue ;
- `useTransition().isPending` alimente `aria-busy` et un léger grisage, sans désactiver le champ ;
- la remise à zéro de la page à `1` à chaque changement de recherche est faite au même endroit, pour éviter deux chemins qui écrivent l'URL ;
- `useDeferredValue` n'est ajouté que si la grille passe un jour côté client et que son rendu devient lent ; il n'y a pas de timer de debounce à maintenir.

Un retour navigateur est géré par le routeur : l'URL change, la page serveur est re-rendue avec les nouvelles props. On évite ainsi le classique « state miroir synchronisé par useEffect ».

### Mémoïsation ciblée

- Les cartes et la grille sont des composants serveur : `React.memo` n'a rien à y faire, elles ne se re-rendent pas côté client.
- Si une carte devient interactive (client), l'envelopper dans `memo` avec des **props primitives** (`code`, `photoUrl`, `photoAlt`, `observationsLabel`). Pas d'objet `photo` ni de callback inline en props, sinon `memo` ne compare plus rien d'utile.
- `useMemo` uniquement pour un calcul réellement coûteux. Ici les 15 cartes sont déjà prêtes à l'arrivée : aucun `useMemo` obligatoire, et le compilateur React peut prendre le relais.
- Clés React stables : le `code` de l'individu, jamais l'index du tableau.
- Vignettes `<img loading="lazy" decoding="async" width height>` servies par l'URL opaque du gateway (aujourd'hui `/api/catalog/photos/[imageId]`), sans optimisation `next/image` pour ne pas contourner l'allowlist serveur.

## Phase de test des composants

Périmètre volontairement limité pour l'instant : **on teste les composants React, pas l'API ni les fonctions utilitaires**. Le parseur de query, le mapping SQL et les route handlers sont validés par la reproduction manuelle sur staging ; des tests unitaires pourront être ajoutés plus tard si le contrat se stabilise.

### Harnais (PR dédiée, avant l'UI)

Dépendances de dev : `vitest`, `jsdom`, `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`. Scripts : `test` (`vitest run`), `test:watch`, `test:coverage` avec `@vitest/coverage-v8`.

```ts
// frontend/vitest.config.ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
  },
});
```

```ts
// frontend/vitest.setup.ts
import "@testing-library/jest-dom/vitest";
```

`tsconfig.json` inclut `vitest.setup.ts` et déclare `types: ["vitest/globals", "@testing-library/jest-dom"]`. La CI ajoute `npm test` au job `build-frontend`, avant `npm run build` : une régression visuelle ou fonctionnelle bloque la PR. Le nettoyage DOM entre les tests est automatique avec `@testing-library/react`.

### Tests de composants

Avec `@testing-library/react` et `user-event`, en testant le comportement visible plutôt que l'implémentation :

- `IndividualCard.test.tsx` : affiche `TUTR0008` (jamais `TT-0008`), image `loading="lazy"` avec l'URL opaque et un `alt`, texte `X observations` ;
- `IndividualGrid.test.tsx` : 15 cartes dans l'ordre reçu, aucun avertissement React sur les clés, état vide distinct ;
- `Pagination.test.tsx` : précédent désactivé en page 1, suivant désactivé à la dernière page, liens qui conservent `search` et `sort`, `aria-current="page"` ;
- `CatalogFiltersBar.test.tsx` : input non contrôlé, `onChange` appelle `router.replace` avec `page: 1`, `isPending` pose `aria-busy` (routeur mocké) ;
- `CatalogResults.test.tsx` : aiguillage résultat / vide / erreur selon les props du gateway.

Exemple pour la pagination du groupe `Actions` :

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Pagination } from "./Pagination";

describe("Pagination", () => {
  it("désactive le précédent en première page et garde les filtres", () => {
    render(
      <Pagination
        page={1}
        pageSize={15}
        total={1529}
        totalPages={102}
        buildHref={(page) => `/catalogue?search=tutr&page=${page}`}
      />,
    );

    expect(screen.getByText(/précédent/i)).toHaveAttribute(
      "aria-disabled",
      "true",
    );
    expect(screen.getByRole("link", { name: /suivant/i })).toHaveAttribute(
      "href",
      "/catalogue?search=tutr&page=2",
    );
    expect(screen.getByRole("link", { current: "page" })).toHaveAttribute(
      "href",
      "/catalogue?search=tutr&page=1",
    );
  });
});
```

### Vérification manuelle (en plus)

Après déploiement staging : `GET /api/catalog/individuals` (401 sans identifiants si l'auth est active, puis 200), une vignette en `200 image/jpeg`, la page `/catalogue` en 200, et un aller-retour recherche → pagination → retour navigateur sans perte des filtres.

## Découpage en PR

1. `docs/catalogue-contract` — ce plan, les décisions et le contrat d'API.
2. `test/catalog-harness` — Vitest + Testing Library, scripts `npm test`, `vitest.config.ts`, `vitest.setup.ts`, ajout de `npm test` à la CI, plus un test de composant minimal pour valider le harnais.
3. `feat/catalog-api` — types sérialisables dans `src/types/catalog.ts`, interface `CatalogGateway`, implémentation PostgreSQL (`DATABASE_URL` depuis l'add-on), route `/api/catalog/individuals` comme adaptateur. Validation manuelle documentée : recherche, tri, pagination, cas vide.
4. `feat/catalog-images` — résolveur de clé + route proxy allowlistée, 404 hors contrat, 503 si objet absent. Validation manuelle du proxy.
5. `feat/catalog-ui` — page `/catalogue` : Sidebar, Title row, Filtres, grille de 15 cartes, pagination du groupe `Actions`, états loading / empty / error. **Chaque composant livré avec son test.** Elle peut être découpée en trois PR si le diff grandit : (a) squelette serveur + grille à partir des props, (b) barre de filtres et navigation URL, (c) carte, vignette et pagination.
6. `style/catalog-wireframe` — tokens du wireframe centralisés dans `globals.css`, suppressibles en retirant leur import du layout.
7. `docs/catalog-env` — variables Clever Cloud, lien avec l'add-on PostgreSQL, rebuild.
8. `feat/catalog-auth` (si nécessaire) — Basic Auth côté serveur, même comportement que la démo Gradio.

Chaque PR reste ciblée, avec des commentaires courts expliquant le pourquoi. **Aucun composant n'est considéré terminé sans son test** ; l'API et les utilitaires restent hors périmètre test pour cette phase. `npm run format:check`, `npm run lint`, `npm test` et `npm run build` doivent passer localement avant ouverture.

## Dernière étape : PR globale et déploiement staging

Une fois les PR ci-dessus prêtes, créer une branche d'intégration et une PR « meta », comme pour la phase 2 abandonnée :

```bash
cd /Users/dams/Projects/cetolog
git switch -c test/catalogue-staging origin/main
for b in docs/catalogue-contract test/catalog-harness feat/catalog-api \
         feat/catalog-images feat/catalog-ui style/catalog-wireframe \
         docs/catalog-env feat/catalog-auth; do
  git merge --no-edit "$b"
done
cd frontend && npm run format:check && npm run lint && npm test && npm run build
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

Vérifications attendues après déploiement : CI verte avec `npm test` (tests de composants), `GET /api/catalog/individuals` (401 sans identifiants si l'auth est active, puis 200), une vignette en `200 image/jpeg`, la page `/catalogue` en 200 et l'aller-retour recherche → pagination → retour navigateur. La PR meta est fermée après le test ; les PR individuelles restent la source de vérité pour la revue.

Le déploiement n'est pas encore exécuté : il n'existe pour l'instant que ce plan, sans code d'API ni d'écran à tester.
