import { catalogGateway } from "@/lib/catalog";
import { parseCatalogQuery, type RawCatalogParams } from "@/lib/catalog/params";
import type { CatalogErrorBody } from "@/types/catalog";

export async function GET(request: Request): Promise<Response> {
  const params = Object.fromEntries(
    new URL(request.url).searchParams.entries(),
  ) as RawCatalogParams;
  const query = parseCatalogQuery(params);

  try {
    const page = await catalogGateway.list(query);
    return Response.json(page, {
      headers: { "Cache-Control": "private, no-store" },
    });
  } catch (error) {
    console.error("catalog: lecture impossible", error);
    const body: CatalogErrorBody = {
      code: "UPSTREAM_UNAVAILABLE",
      message: "Le catalogue est temporairement indisponible.",
    };
    return Response.json(body, { status: 503 });
  }
}
