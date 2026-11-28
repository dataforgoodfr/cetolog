"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

import { buildCatalogUrl } from "@/lib/catalog/params";
import type { CatalogQuery } from "@/types/catalog";

export type CatalogFiltersBarProps = { filters: CatalogQuery };

export function CatalogFiltersBar({ filters }: CatalogFiltersBarProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  function navigate(next: Partial<CatalogQuery>) {
    startTransition(() => {
      router.replace(buildCatalogUrl({ ...filters, ...next, page: 1 }), {
        scroll: false,
      });
    });
  }

  return (
    <div
      className="catalog-filters"
      role="group"
      aria-label="Filtres du catalogue"
      aria-busy={isPending}
    >
      <label className="catalog-search">
        <span>Rechercher</span>
        <input
          name="search"
          defaultValue={filters.search}
          placeholder="Identifiant, nom..."
          onChange={(event) => navigate({ search: event.target.value })}
        />
      </label>
      <label className="catalog-sort">
        <span>Trier par</span>
        <select
          name="sort"
          defaultValue={filters.sort}
          onChange={(event) => {
            const value = event.target.value;
            if (value === "lastObservation") navigate({ sort: value });
          }}
        >
          <option value="lastObservation">Dernière observation</option>
        </select>
      </label>
      <button type="button" className="catalog-new-individual">
        + Nouvel individu
      </button>
    </div>
  );
}
