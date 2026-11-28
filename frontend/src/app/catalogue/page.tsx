import { CatalogFiltersBar } from "@/components/catalog/CatalogFiltersBar";
import { CatalogHeader } from "@/components/catalog/CatalogHeader";
import { CatalogResults } from "@/components/catalog/CatalogResults";
import { Sidebar } from "@/components/catalog/Sidebar";
import { catalogGateway } from "@/lib/catalog";
import { parseCatalogQuery } from "@/lib/catalog/params";

export type CatalogPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function CataloguePage({
  searchParams,
}: CatalogPageProps) {
  const query = parseCatalogQuery(await searchParams);
  const catalogPage = await catalogGateway.list(query);

  return (
    <main className="catalog-screen">
      <Sidebar />
      <div className="catalog-content">
        <CatalogHeader />
        <CatalogFiltersBar filters={query} />
        <CatalogResults items={catalogPage.items} />
      </div>
    </main>
  );
}
