import Link from "next/link";

import type { CatalogPage } from "@/types/catalog";

export type PaginationProps = Pick<
  CatalogPage,
  "page" | "pageSize" | "total" | "totalPages"
> & { buildHref: (page: number) => string };

export function Pagination({
  page,
  total,
  totalPages,
  buildHref,
}: PaginationProps) {
  return (
    <nav className="catalog-pagination" aria-label="Pagination du catalogue">
      {page > 1 ? (
        <Link href={buildHref(page - 1)}>Précédent</Link>
      ) : (
        <span aria-disabled="true">Précédent</span>
      )}

      <span className="catalog-pagination-status">
        {total} individus — page{" "}
        <Link href={buildHref(page)} aria-current="page">
          {page}
        </Link>{" "}
        sur {totalPages}
      </span>

      {page < totalPages ? (
        <Link href={buildHref(page + 1)}>Suivant</Link>
      ) : (
        <span aria-disabled="true">Suivant</span>
      )}
    </nav>
  );
}
