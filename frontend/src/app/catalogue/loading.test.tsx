import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Loading from "./loading";

describe("Loading", () => {
  it("expose un statut de chargement accessible", () => {
    render(<Loading />);
    expect(screen.getByRole("status")).toHaveAttribute(
      "aria-label",
      "Chargement du catalogue",
    );
  });
});
