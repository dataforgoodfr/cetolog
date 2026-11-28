// Correspondance entre la livraison en base et le dossier du bucket.
const DELIVERY_FOLDERS: Record<string, string> = {
  catalogue_20261029_miraceti: "2026-11-06_catalogue_tt",
};

export type PhotoKeySource = {
  delivery: string;
  original_filename: string;
};

// La livraison n'a pas normalisé les noms de fichiers : certains gardent la date,
// d'autres non. On produit les deux variantes possibles, toujours dérivées d'une
// ligne de base, puis le serveur vérifie laquelle existe réellement.
export function resolveS3KeyCandidates(
  photo: PhotoKeySource,
): readonly string[] | null {
  const deliveryFolder = DELIVERY_FOLDERS[photo.delivery];
  if (!deliveryFolder) return null;

  const blocks = photo.original_filename.split("_");
  const [side, code, dateBlock, ...rest] = blocks;
  if (!side || !code || !dateBlock || !/^[DG]$/.test(side)) return null;
  if (!/^TUTR\d{4}$/.test(code) || !/^\d{8}$/.test(dateBlock)) return null;
  if (rest.length === 0) return null;

  const prefix = side === "D" ? "DD" : "DG";
  const folder = `curated/catalogue/photos/${deliveryFolder}/${code}`;
  return [
    `${folder}/${prefix}_${code}_${dateBlock}_${rest.join("_")}`,
    `${folder}/${prefix}_${code}_${rest.join("_")}`,
  ];
}
