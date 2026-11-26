export type Side = "D" | "G" | "";
export type CatalogueSide = "D" | "G";

export interface DemoPhoto {
  individu: string;
  cote: Side;
  /** Nom de fichier possiblement personnel : absent des données réelles. */
  fichier_origine?: string;
  /** Identifiant opaque résolu côté serveur vers le bucket, jamais un chemin brut. */
  imageId: string;
  sha256?: string;
}

export interface DemoCandidate {
  individu: string;
  score: number;
  D?: number;
  G?: number;
}

export interface DemoProposition {
  photos: DemoPhoto[];
  candidats: DemoCandidate[];
  reponse: string[];
}

export interface DemoPayload {
  bestOf: string;
  catalogue: string;
  individus: string[];
  propositions: Record<string, DemoProposition>;
  cataloguePhotos: Record<string, Partial<Record<CatalogueSide, string>>>;
  pagination: { pageSize: number; totalPages: number };
}

export const SIDES: readonly CatalogueSide[] = ["D", "G"];

export function sideLabel(side: Side | CatalogueSide): string {
  if (side === "D") return "droite";
  if (side === "G") return "gauche";
  return "?";
}

export function formatScore(score: number | undefined): string {
  return score === undefined ? "–" : score.toFixed(2);
}

/** Même ordre que `by_number` dans la démo : IND2 avant IND10. */
export function byNumber(a: string, b: string): number {
  const digits = (value: string) => Number(value.replace(/\D/g, "") || 0);
  return digits(a) - digits(b) || a.localeCompare(b, "fr");
}

/** Ne renvoie que les identifiants présents dans le contrat, jamais un chemin brut. */
export function photoLabel(
  payload: DemoPayload,
  imageId: string,
): string | null {
  for (const proposition of Object.values(payload.propositions)) {
    const photo = proposition.photos.find((item) => item.imageId === imageId);
    if (photo) return `${photo.individu} · ${sideLabel(photo.cote)}`;
  }

  for (const [individu, photos] of Object.entries(payload.cataloguePhotos)) {
    for (const side of SIDES) {
      if (photos[side] === imageId) return `${individu} · ${sideLabel(side)}`;
    }
  }

  return null;
}
