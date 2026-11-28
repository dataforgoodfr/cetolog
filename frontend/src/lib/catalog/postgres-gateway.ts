import "server-only";

import { Pool } from "pg";

import type { CatalogGateway } from "./gateway";
import type {
  CatalogIndividual,
  CatalogPage,
  CatalogQuery,
} from "@/types/catalog";

type IndividualRow = {
  code: string;
  photo_id: number;
};

const LIST_SQL = `
  with reference as (
    select distinct on (p.individual_id)
           p.individual_id,
           p.id as photo_id
      from photos p
     order by p.individual_id,
              case p.side when 'D' then 0 when 'G' then 1 else 2 end,
              p.date desc nulls last,
              p.id
  ),
  activity as (
    select individual_id,
           max(date) as last_observation_date
      from photos
     group by individual_id
  )
  select i.code, r.photo_id
    from individuals i
    join reference r on r.individual_id = i.id
    left join activity a on a.individual_id = i.id
   where $1 = '' or i.code ilike '%' || $1 || '%'
   order by a.last_observation_date desc nulls last, i.code
   limit $2 offset $3
`;

const COUNT_SQL = `
  select count(*)::int as total
    from individuals i
   where $1 = '' or i.code ilike '%' || $1 || '%'
`;

let pool: Pool | undefined;

function getPool(): Pool {
  if (!process.env.DATABASE_URL) {
    throw new Error("DATABASE_URL est requise pour lire le catalogue");
  }
  pool ??= new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false },
    max: 2,
  });
  return pool;
}

function toIndividual(row: IndividualRow): CatalogIndividual {
  const photoId = String(row.photo_id);
  return {
    code: row.code,
    photo: {
      id: photoId,
      url: `/api/catalog/photos/${photoId}`,
      alt: `Photo de ${row.code}`,
    },
    observationsLabel: "X observations",
  };
}

export const postgresGateway: CatalogGateway = {
  async list(query: CatalogQuery): Promise<CatalogPage> {
    const client = await getPool().connect();
    try {
      const offset = (query.page - 1) * query.pageSize;
      const [rows, totals] = await Promise.all([
        client.query<IndividualRow>(LIST_SQL, [
          query.search,
          query.pageSize,
          offset,
        ]),
        client.query<{ total: number }>(COUNT_SQL, [query.search]),
      ]);
      const total = totals.rows[0]?.total ?? 0;

      return {
        items: rows.rows.map(toIndividual),
        total,
        page: query.page,
        pageSize: query.pageSize,
        totalPages: Math.ceil(total / query.pageSize) || 1,
      };
    } finally {
      client.release();
    }
  },
};
