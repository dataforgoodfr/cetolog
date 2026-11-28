import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Pagination } from "./Pagination";

const buildHref = (page: number) => `/catalogue?search=tutr&page=${page}`;

describe("Pagination", () => {
  it("désactive le précédent en première page et garde les filtres", () => {
    render(
      <Pagination
        page={1}
        pageSize={15}
        total={1529}
        totalPages={102}
        buildHref={buildHref}
      />,
    );

    expect(screen.getByText(/précédent/i)).toHaveAttribute(
      "aria-disabled",
      "true",
    );
    expect(screen.getByRole("link", { name: /suivant/i })).toHaveAttribute(
      "href",
      "/catalogue?search=tutr&page=2",
    );
    expect(screen.getByRole("link", { current: "page" })).toHaveAttribute(
      "href",
      "/catalogue?search=tutr&page=1",
    );
  });

  it("désactive le suivant à la dernière page", () => {
    render(
      <Pagination
        page={102}
        pageSize={15}
        total={1529}
        totalPages={102}
        buildHref={buildHref}
      />,
    );

    expect(screen.getByText(/suivant/i)).toHaveAttribute(
      "aria-disabled",
      "true",
    );
    expect(screen.getByRole("link", { name: /précédent/i })).toHaveAttribute(
      "href",
      "/catalogue?search=tutr&page=101",
    );
  });
});
