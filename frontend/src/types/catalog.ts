export type CatalogSort = "lastObservation";

export type CatalogQuery = {
  search: string;
  sort: CatalogSort;
  page: number;
  pageSize: number;
};

export type CatalogPhoto = {
  id: string;
  url: string;
  alt: string;
};

export type CatalogIndividual = {
  code: string;
  photo: CatalogPhoto;
  observationsLabel: string;
};

export type CatalogPage = {
  items: readonly CatalogIndividual[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
};

export type CatalogErrorBody = {
  code: "INVALID_QUERY" | "UPSTREAM_UNAVAILABLE";
  message: string;
};
