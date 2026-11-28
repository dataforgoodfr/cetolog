import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CatalogHeader } from "./CatalogHeader";

describe("CatalogHeader", () => {
  it("affiche le titre, le sous-titre et l'action d'import", () => {
    render(<CatalogHeader />);

    expect(
      screen.getByRole("heading", { name: "Catalogue des individus" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/tous les individus connus/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Importer catalogue existant" }),
    ).toBeInTheDocument();
  });
});
