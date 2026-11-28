import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import CatalogError from "./error";

describe("CatalogError", () => {
  it("propose de réessayer", async () => {
    const reset = vi.fn();
    const user = userEvent.setup();

    render(<CatalogError error={new Error("boom")} reset={reset} />);

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Le catalogue n'a pas pu être chargé.",
    );
    await user.click(screen.getByRole("button", { name: "Réessayer" }));
    expect(reset).toHaveBeenCalledOnce();
  });
});
