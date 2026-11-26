import {
  byNumber,
  type DemoCandidate,
  type DemoPayload,
  type DemoPhoto,
  type Side,
} from "./contract";

const BEST_OF = "best-of-fictif-2026-11";
const CATALOGUE = "catalogue-fictif-2026-11";
const PAGE_SIZE = 12;
const CATALOGUE_IDS = Array.from(
  { length: 24 },
  (_, index) => `TUTR${String(index + 1).padStart(3, "0")}`,
);
const SCORES = [0.92, 0.9, 0.88, 0.86, 0.84, 0.82, 0.8, 0.78, 0.76, 0.74];

function round3(value: number): number {
  return Math.round(value * 1000) / 1000;
}

function bestOfPhotos(individu: string, sides: Side[]): DemoPhoto[] {
  return sides.map((cote, index) => {
    const suffix = cote === "" ? "x" : cote.toLowerCase();
    return {
      individu,
      cote,
      fichier_origine: `fictif-${individu.toLowerCase()}-${suffix}-${index + 1}.jpg`,
      imageId: `b-${individu.toLowerCase()}-${suffix}-${index + 1}`,
    };
  });
}

// Les scores sont déjà classés : la phase 2 remplacera ceci par le CSV Python.
function candidates(offset: number): DemoCandidate[] {
  return SCORES.map((base, index) => {
    const score = round3(base + offset);
    return {
      individu: CATALOGUE_IDS[index],
      score,
      ...(index % 3 === 2 ? {} : { D: round3(score - 0.01) }),
      ...(index % 4 === 3 ? {} : { G: score }),
    };
  });
}

// Une empreinte de côté n'existe que si la photo du catalogue existe.
const cataloguePhotos = Object.fromEntries(
  CATALOGUE_IDS.map((individu, index) => [
    individu,
    {
      ...(index % 3 === 2 ? {} : { D: `c-${individu.toLowerCase()}-d` }),
      ...(index % 4 === 3 ? {} : { G: `c-${individu.toLowerCase()}-g` }),
    },
  ]),
) as DemoPayload["cataloguePhotos"];

export const fixturePayload: DemoPayload = {
  bestOf: BEST_OF,
  catalogue: CATALOGUE,
  individus: ["IND10", "IND2", "IND1"].sort(byNumber),
  propositions: {
    IND1: {
      photos: bestOfPhotos("IND1", ["D", "G"]),
      candidats: candidates(0),
      reponse: [],
    },
    IND2: {
      photos: bestOfPhotos("IND2", ["", "D", "G"]),
      candidats: candidates(0.01),
      reponse: ["TUTR024"],
    },
    IND10: {
      photos: bestOfPhotos("IND10", ["D"]),
      candidats: candidates(-0.01),
      reponse: [],
    },
  },
  cataloguePhotos,
  pagination: {
    pageSize: PAGE_SIZE,
    totalPages: Math.ceil(CATALOGUE_IDS.length / PAGE_SIZE),
  },
};
