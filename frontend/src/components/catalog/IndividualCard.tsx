import type { CatalogIndividual } from "@/types/catalog";

export type IndividualCardProps = CatalogIndividual;

export function IndividualCard({
  code,
  photo,
  observationsLabel,
}: IndividualCardProps) {
  return (
    <article className="catalog-card">
      {/* next/image contournerait l'allowlist de la route proxy. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        className="catalog-card-photo"
        src={photo.url}
        alt={photo.alt}
        loading="lazy"
        decoding="async"
        width={240}
        height={160}
      />
      <p className="catalog-card-code">{code}</p>
      <p className="catalog-card-observations">{observationsLabel}</p>
    </article>
  );
}
