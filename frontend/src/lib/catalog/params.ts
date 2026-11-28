import type { CatalogQuery, CatalogSort } from "@/types/catalog";

export const CATALOG_PAGE_SIZE = 15;

export type RawCatalogParams = Record<string, string | string[] | undefined>;

const DEFAULT_SORT: CatalogSort = "lastObservation";

function first(value: string | string[] | undefined): string {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
}

function positiveInteger(value: string, fallback: number): number {
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed > 0 ? parsed : fallback;
}

export function parseCatalogQuery(params: RawCatalogParams): CatalogQuery {
  const sort = first(params.sort);
  const page = positiveInteger(first(params.page), 1);

  return {
    search: first(params.search).trim(),
    sort: sort === "lastObservation" ? sort : DEFAULT_SORT,
    page,
    pageSize: CATALOG_PAGE_SIZE,
  };
}

export function buildCatalogUrl(query: CatalogQuery): string {
  const params = new URLSearchParams({
    search: query.search,
    sort: query.sort,
    page: String(query.page),
    pageSize: String(query.pageSize),
  });
  return `/catalogue?${params.toString()}`;
}
