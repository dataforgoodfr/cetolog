import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CatalogFiltersBar } from "./CatalogFiltersBar";
import type { CatalogQuery } from "@/types/catalog";

const replace = vi.hoisted(() => vi.fn());
const startTransition = vi.hoisted(() => (callback: () => void) => callback());

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace }) }));
vi.mock("react", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react")>();
  return { ...actual, useTransition: () => [true, startTransition] };
});

const filters: CatalogQuery = {
  search: "",
  sort: "lastObservation",
  page: 1,
  pageSize: 15,
};

beforeEach(() => {
  replace.mockClear();
});

describe("CatalogFiltersBar", () => {
  it("garde la saisie dans le DOM et remet la page à 1", async () => {
    const user = userEvent.setup();
    render(<CatalogFiltersBar filters={{ ...filters, page: 5 }} />);

    const input = screen.getByPlaceholderText("Identifiant, nom...");
    expect(input).toHaveValue("");
    await user.type(input, "tutr");

    expect(input).toHaveValue("tutr");
    expect(replace).toHaveBeenLastCalledWith(
      "/catalogue?search=tutr&sort=lastObservation&page=1&pageSize=15",
      { scroll: false },
    );
  });

  it("expose l'état de transition via aria-busy", () => {
    render(<CatalogFiltersBar filters={filters} />);
    expect(screen.getByRole("group", { name: /filtres/i })).toHaveAttribute(
      "aria-busy",
      "true",
    );
  });

  it("conserve le tri affiché", () => {
    render(<CatalogFiltersBar filters={filters} />);
    expect(screen.getByRole("combobox", { name: /trier par/i })).toHaveValue(
      "lastObservation",
    );
  });
});
