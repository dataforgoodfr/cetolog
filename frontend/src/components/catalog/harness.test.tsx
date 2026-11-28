import { render, screen } from "@testing-library/react";
import { it } from "vitest";

// Garde le harnais vivant : sans ce test, une régression de config passerait inaperçue.
it("rend un composant avec Testing Library", () => {
  render(<p>Catalogue</p>);
  screen.getByText("Catalogue");
});
