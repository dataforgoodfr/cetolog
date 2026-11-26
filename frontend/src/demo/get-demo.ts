import { createHash } from "node:crypto";
import { connection } from "next/server";
import {
  byNumber,
  SIDES,
  type CatalogueSide,
  type DemoCandidate,
  type DemoPayload,
  type DemoProposition,
  type DemoPhoto,
  type Side,
} from "./contract";
import { parseCsv } from "./csv";
import { listObjects, readText } from "./s3";

const PAGE_SIZE = 12;
const imageKeys = new Map<string, string>();
let cached: Promise<DemoPayload> | undefined;

/** Le contrat est chargé une fois par processus ; les vignettes utilisent la même table. */
export function getDemoPayload(): Promise<DemoPayload> {
  cached ??= load().catch((error) => {
    cached = undefined;
    throw error;
  });
  return cached;
}

/** Seuls les identifiants du contrat sont résolvables : pas d'accès S3 arbitraire. */
export function resolveImageKey(imageId: string): string | undefined {
  return imageKeys.get(imageId);
}

function registerImage(kind: string, key: string): string {
  const imageId = createHash("sha256")
    .update(`${kind}\n${key}`)
    .digest("hex")
    .slice(0, 24);
  imageKeys.set(imageId, key);
  return imageId;
}

function toPhoto(
  kind: "best_of" | "catalogue",
  delivery: string,
  row: Record<string, string>,
): DemoPhoto | null {
  const file = row.fichier_origine;
  if (!file) return null;
  const side: Side = row.cote === "D" || row.cote === "G" ? row.cote : "";
  const key = `curated/${kind}/photos/${delivery}/${row.individu}/${file}`;
  return {
    individu: row.individu,
    cote: side,
    imageId: registerImage(kind, key),
    sha256: row.sha256 || undefined,
    // fichier_origine est volontairement omis : il peut contenir un nom de personne.
  };
}

function numberOrUndefined(value: string | undefined): number | undefined {
  return value ? Number(value) : undefined;
}

async function load(): Promise<DemoPayload> {
  // S3 n'est accessible qu'à la requête : empêche la lecture au build.
  await connection();
  const propositionKeys = (await listObjects("derived/propositions/"))
    .filter((key) => key.endsWith(".csv"))
    .sort();
  const configured = process.env.DEMO_PROPOSITIONS_KEY;
  const key =
    configured && propositionKeys.includes(configured)
      ? configured
      : propositionKeys.at(-1);
  if (!key) {
    throw new Error("Aucune proposition disponible dans derived/propositions/");
  }

  const rows = parseCsv(await readText(key));
  if (rows.length === 0) throw new Error("Fichier de propositions vide");
  const required = [
    "best_of",
    "catalogue",
    "individu",
    "rang",
    "candidat",
    "score",
    "cosinus_D",
    "cosinus_G",
    "deja_au_catalogue",
  ];
  const missing = required.filter((column) => !(column in rows[0]));
  if (missing.length > 0) {
    throw new Error(
      `Colonne de propositions manquante : ${missing.join(", ")}`,
    );
  }

  // Les livraisons viennent du CSV, pas de latest() : deux démos ne changent pas de jeu.
  const bestOf = rows[0].best_of;
  const catalogue = rows[0].catalogue;
  if (!bestOf || !catalogue) throw new Error("Livraisons absentes du CSV");

  const bestPhotos = parseCsv(
    await readText(`derived/embeddings/best_of/${bestOf}/photos.csv`),
  );
  const cataloguePhotosRows = parseCsv(
    await readText(`derived/embeddings/catalogue/${catalogue}/photos.csv`),
  );

  const grouped = new Map<string, Record<string, string>[]>();
  for (const row of rows) {
    const group = grouped.get(row.individu) ?? [];
    group.push(row);
    grouped.set(row.individu, group);
  }

  const propositions: Record<string, DemoProposition> = {};
  for (const [individu, group] of grouped) {
    const candidats: DemoCandidate[] = group
      .slice()
      .sort((a, b) => Number(a.rang) - Number(b.rang))
      .map((row) => ({
        individu: row.candidat,
        score: Number(row.score),
        ...(numberOrUndefined(row.cosinus_D) === undefined
          ? {}
          : { D: Number(row.cosinus_D) }),
        ...(numberOrUndefined(row.cosinus_G) === undefined
          ? {}
          : { G: Number(row.cosinus_G) }),
      }));
    const photos = bestPhotos
      .filter((row) => row.individu === individu)
      .map((row) => toPhoto("best_of", bestOf, row))
      .filter((photo): photo is DemoPhoto => photo !== null);

    propositions[individu] = {
      photos,
      candidats,
      reponse: (group[0].deja_au_catalogue ?? "").split(" ; ").filter(Boolean),
    };
  }

  const cataloguePhotos: DemoPayload["cataloguePhotos"] = {};
  for (const row of cataloguePhotosRows) {
    if (!SIDES.includes(row.cote as CatalogueSide)) continue;
    const photo = toPhoto("catalogue", catalogue, row);
    if (!photo) continue;
    const side = row.cote as CatalogueSide;
    const entry = (cataloguePhotos[row.individu] ??= {});
    // Première ligne gagnante, comme setdefault() dans catalogue_photos().
    entry[side] ??= photo.imageId;
  }

  const withPhotos = Object.values(cataloguePhotos).filter((photos) =>
    SIDES.some((side) => photos[side]),
  ).length;

  return {
    bestOf,
    catalogue,
    individus: Object.keys(propositions).sort(byNumber),
    propositions,
    cataloguePhotos,
    pagination: {
      pageSize: PAGE_SIZE,
      totalPages: Math.max(1, Math.ceil(withPhotos / PAGE_SIZE)),
    },
  };
}
