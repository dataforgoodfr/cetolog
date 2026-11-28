import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CatalogResults } from "./CatalogResults";
import type { CatalogIndividual } from "@/types/catalog";

const item: CatalogIndividual = {
  code: "TUTR0008",
  photo: { id: "42", url: "/api/catalog/photos/42", alt: "Photo de TUTR0008" },
  observationsLabel: "X observations",
};

describe("CatalogResults", () => {
  it("affiche la grille quand il y a des résultats", () => {
    render(<CatalogResults items={[item]} />);
    expect(screen.getByRole("article")).toBeInTheDocument();
  });

  it("affiche un état vide distinct quand la liste est vide", () => {
    render(<CatalogResults items={[]} />);
    expect(screen.queryByRole("article")).not.toBeInTheDocument();
    expect(
      screen.getByText(/aucun individu ne correspond/i),
    ).toBeInTheDocument();
  });

  it("affiche l'erreur avec un role alert", () => {
    render(<CatalogResults items={[]} error="Catalogue indisponible" />);
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Catalogue indisponible",
    );
    expect(screen.queryByRole("article")).not.toBeInTheDocument();
  });
});
