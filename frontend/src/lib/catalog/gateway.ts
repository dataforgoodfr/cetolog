import type { CatalogPage, CatalogQuery } from "@/types/catalog";

// L'affichage dépend de cette interface, jamais de PostgreSQL ni de Next.
export interface CatalogGateway {
  list(query: CatalogQuery): Promise<CatalogPage>;
}
