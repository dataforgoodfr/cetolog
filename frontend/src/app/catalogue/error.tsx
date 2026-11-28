"use client";

export type CatalogErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function CatalogError({ reset }: CatalogErrorProps) {
  return (
    <div className="catalog-error-boundary" role="alert">
      <p>Le catalogue n&apos;a pas pu être chargé.</p>
      <button type="button" onClick={reset}>
        Réessayer
      </button>
    </div>
  );
}
