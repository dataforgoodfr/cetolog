import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Sidebar } from "./Sidebar";

describe("Sidebar", () => {
  it("affiche la navigation et marque Catalogue comme page courante", () => {
    render(<Sidebar />);

    expect(screen.getByText("Cetolog")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /lancer un matching/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Catalogue" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByText("Observations")).toBeInTheDocument();
    expect(screen.getByText("Historique")).toBeInTheDocument();
    expect(screen.getByText("Qualité")).toBeInTheDocument();
  });
});
