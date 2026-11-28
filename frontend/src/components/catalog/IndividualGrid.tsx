import { IndividualCard } from "./IndividualCard";
import type { CatalogPage } from "@/types/catalog";

export type IndividualGridProps = { items: CatalogPage["items"] };

export function IndividualGrid({ items }: IndividualGridProps) {
  return (
    <div className="catalog-grid">
      {items.map((individual) => (
        <IndividualCard key={individual.code} {...individual} />
      ))}
    </div>
  );
}
