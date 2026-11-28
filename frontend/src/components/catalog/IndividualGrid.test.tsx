import { render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { IndividualGrid } from "./IndividualGrid";
import type { CatalogIndividual } from "@/types/catalog";

function individual(code: string): CatalogIndividual {
  return {
    code,
    photo: {
      id: code,
      url: `/api/catalog/photos/${code}`,
      alt: `Photo de ${code}`,
    },
    observationsLabel: "X observations",
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("IndividualGrid", () => {
  it("affiche les cartes dans l'ordre reçu avec des clés stables", () => {
    const errors = vi.spyOn(console, "error").mockImplementation(() => {});
    const codes = Array.from(
      { length: 15 },
      (_, index) => `TUTR${String(index).padStart(4, "0")}`,
    );

    render(<IndividualGrid items={codes.map(individual)} />);

    const cards = screen.getAllByRole("article");
    expect(cards).toHaveLength(15);
    expect(within(cards[0]).getByText("TUTR0000")).toBeInTheDocument();
    expect(within(cards[14]).getByText("TUTR0014")).toBeInTheDocument();
    expect(errors).not.toHaveBeenCalled();
  });
});
