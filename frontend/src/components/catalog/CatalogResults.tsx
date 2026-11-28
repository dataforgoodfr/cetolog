import { IndividualGrid } from "./IndividualGrid";
import type { CatalogPage } from "@/types/catalog";

export type CatalogResultsProps = {
  items: CatalogPage["items"];
  error?: string | null;
};

export function CatalogResults({ items, error }: CatalogResultsProps) {
  if (error) {
    return (
      <p className="catalog-results-error" role="alert">
        {error}
      </p>
    );
  }

  if (items.length === 0) {
    return (
      <p className="catalog-results-empty">
        Aucun individu ne correspond à cette recherche.
      </p>
    );
  }

  return <IndividualGrid items={items} />;
}
