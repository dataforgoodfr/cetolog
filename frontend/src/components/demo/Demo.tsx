import Form from "next/form";
import Link from "next/link";
import {
  byNumber,
  formatScore,
  SIDES,
  sideLabel,
  type Side,
} from "@/demo/contract";
import { getDemoPayload } from "@/demo/get-demo";
import { PhotoTile } from "./PhotoTile";

type SearchParams = Record<string, string | string[] | undefined>;

type DemoProps = {
  searchParams: Promise<SearchParams>;
};

// Même priorité que `sorted(PROPOSITIONS[...]["photos"])` de la démo Gradio.
const PHOTO_ORDER: Record<Side, number> = { "": 0, D: 1, G: 2 };

function firstValue(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function readPage(value: string | undefined, totalPages: number): number {
  const parsed = Number.parseInt(value ?? "", 10);
  if (!Number.isFinite(parsed)) return 1;
  return Math.min(Math.max(parsed, 1), totalPages);
}

function pageHref(individu: string, page: number): string {
  return `/?${new URLSearchParams({ individu, page: String(page) })}`;
}

export async function Demo({ searchParams }: DemoProps) {
  const payload = getDemoPayload();
  const params = await searchParams;
  const individus = [...payload.individus].sort(byNumber);
  // Comme `DOLPHINS_LIST` : seuls les individus ayant au moins une photo exploitables.
  const catalogueIds = Object.entries(payload.cataloguePhotos)
    .filter(([, photos]) => SIDES.some((side) => photos[side]))
    .map(([individu]) => individu)
    .sort(byNumber);
  const totalPages = Math.max(1, payload.pagination.totalPages);
  const page = readPage(firstValue(params.page), totalPages);

  const requested = firstValue(params.individu);
  const selected =
    requested && payload.propositions[requested]
      ? requested
      : (individus[0] ?? "");
  const proposition = selected ? payload.propositions[selected] : undefined;

  if (!proposition || catalogueIds.length === 0) {
    return (
      <p className="demo-empty">Aucune donnée de démonstration disponible.</p>
    );
  }

  const bestOfPhotos = [...proposition.photos].sort(
    (a, b) => PHOTO_ORDER[a.cote] - PHOTO_ORDER[b.cote],
  );

  const start = (page - 1) * payload.pagination.pageSize;
  const pageIds = catalogueIds.slice(
    start,
    start + payload.pagination.pageSize,
  );

  return (
    <>
      <div className="demo-columns">
        <div className="demo-column">
          <section className="demo-section" aria-labelledby="individu-title">
            <h2 id="individu-title" className="demo-section-title">
              Individu provisoire
            </h2>
            <Form action="/" className="demo-form">
              <div className="demo-field">
                <label htmlFor="individu">Choisir un individu</label>
                <select id="individu" name="individu" defaultValue={selected}>
                  {individus.map((individu) => (
                    <option key={individu} value={individu}>
                      {individu}
                    </option>
                  ))}
                </select>
              </div>
              <input type="hidden" name="page" value={page} />
              <button type="submit" className="demo-button">
                Afficher
              </button>
            </Form>
          </section>

          <section className="demo-section" aria-labelledby="photos-title">
            <h2 id="photos-title" className="demo-section-title">
              Ses photos dans le best-of
            </h2>
            {bestOfPhotos.length === 0 ? (
              <p className="demo-empty">Aucune photo disponible.</p>
            ) : (
              <ul className="photo-grid">
                {bestOfPhotos.map((photo, index) => (
                  <li key={`${photo.imageId}-${index}`}>
                    <PhotoTile
                      imageId={photo.imageId}
                      individu={photo.individu}
                      side={photo.cote}
                      caption={sideLabel(photo.cote)}
                    />
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>

        <section className="demo-section" aria-labelledby="candidats-title">
          <h2 id="candidats-title" className="demo-section-title">
            Candidats proposés
          </h2>
          <p className="demo-note">
            <strong>Score</strong> : meilleur cosinus entre les empreintes des
            dorsales, tous côtés confondus. Ce n’est pas une probabilité.
          </p>
          {proposition.candidats.length === 0 ? (
            <p className="demo-empty">Aucun candidat proposé.</p>
          ) : (
            <ol className="candidate-list">
              {proposition.candidats.map((candidat, index) => (
                <li key={candidat.individu} className="candidate">
                  <h3 className="candidate-title">
                    {index + 1}. {candidat.individu} · score{" "}
                    {formatScore(candidat.score)}
                  </h3>
                  <div className="candidate-sides">
                    {SIDES.map((side) => (
                      <PhotoTile
                        key={side}
                        imageId={
                          payload.cataloguePhotos[candidat.individu]?.[side]
                        }
                        individu={candidat.individu}
                        side={side}
                        score={candidat[side]}
                      />
                    ))}
                  </div>
                </li>
              ))}
            </ol>
          )}
        </section>
      </div>

      <details className="demo-accordion" open>
        <summary>Parcourir le catalogue</summary>
        <nav className="demo-pagination" aria-label="Pagination du catalogue">
          {page > 1 ? (
            <Link className="demo-button" href={pageHref(selected, page - 1)}>
              Précédent
            </Link>
          ) : (
            <span className="demo-button is-disabled" aria-disabled="true">
              Précédent
            </span>
          )}
          <span className="demo-page-position">
            Page {page} / {totalPages}
          </span>
          {page < totalPages ? (
            <Link className="demo-button" href={pageHref(selected, page + 1)}>
              Suivant
            </Link>
          ) : (
            <span className="demo-button is-disabled" aria-disabled="true">
              Suivant
            </span>
          )}
        </nav>
        <ul className="photo-grid">
          {pageIds.flatMap((individu) =>
            SIDES.map((side) => (
              <li key={`${individu}-${side}`}>
                <PhotoTile
                  imageId={payload.cataloguePhotos[individu]?.[side]}
                  individu={individu}
                  side={side}
                  caption={`${individu} · ${sideLabel(side)}`}
                />
              </li>
            )),
          )}
        </ul>
      </details>
    </>
  );
}
