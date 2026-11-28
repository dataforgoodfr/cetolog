import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { IndividualCard } from "./IndividualCard";
import type { CatalogIndividual } from "@/types/catalog";

const individual: CatalogIndividual = {
  code: "TUTR0008",
  photo: {
    id: "42",
    url: "/api/catalog/photos/42",
    alt: "Photo de TUTR0008",
  },
  observationsLabel: "X observations",
};

describe("IndividualCard", () => {
  it("affiche le code de la base sans le transformer", () => {
    render(<IndividualCard {...individual} />);

    expect(screen.getByText("TUTR0008")).toBeInTheDocument();
    expect(screen.queryByText(/TT-0008/)).not.toBeInTheDocument();
    expect(screen.getByText("X observations")).toBeInTheDocument();
  });

  it("affiche l'URL opaque du gateway en image différée", () => {
    render(<IndividualCard {...individual} />);

    const image = screen.getByRole("img", { name: "Photo de TUTR0008" });
    expect(image).toHaveAttribute("src", "/api/catalog/photos/42");
    expect(image).toHaveAttribute("loading", "lazy");
    expect(image).toHaveAttribute("decoding", "async");
  });
});
