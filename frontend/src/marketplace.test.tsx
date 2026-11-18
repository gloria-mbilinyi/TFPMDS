import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { Marketplace } from "./Marketplace";
import { api } from "./api";
import { csvCell } from "./AdminPages";

beforeEach(() => {
  sessionStorage.clear();
  vi.stubGlobal("fetch", vi.fn());
});
afterEach(() => vi.unstubAllGlobals());

it("submits filters to the API and presents an empty marketplace result", async () => {
  vi.mocked(fetch).mockImplementation(
    async () => new Response("[]", { status: 200 }),
  );
  render(
    <MemoryRouter>
      <Marketplace />
    </MemoryRouter>,
  );
  await userEvent.type(await screen.findByLabelText("Search produce"), "rice");
  await userEvent.selectOptions(screen.getByLabelText("Region"), "Morogoro");
  await userEvent.type(screen.getByLabelText("Min. quantity (kg)"), "100");
  await userEvent.click(screen.getByRole("button", { name: "Apply filters" }));
  expect(fetch).toHaveBeenLastCalledWith(
    expect.stringContaining("q=rice&region=Morogoro&min_quantity=100"),
    expect.anything(),
  );
  expect(await screen.findByText(/No produce matches/)).toBeInTheDocument();
});

it("translates validation errors into useful field messages", async () => {
  vi.mocked(fetch).mockResolvedValue(
    new Response(
      JSON.stringify({
        detail: [
          {
            loc: ["body", "quantity_kg"],
            msg: "Input should be greater than 0",
          },
        ],
      }),
      { status: 422 },
    ),
  );
  await expect(api("/orders")).rejects.toThrow(
    "quantity_kg: Input should be greater than 0",
  );
});

it("escapes CSV cells and neutralizes spreadsheet formulas", () => {
  expect(csvCell('A "quoted" crop')).toBe('"A ""quoted"" crop"');
  expect(csvCell('=HYPERLINK("bad")')).toBe('"\'=HYPERLINK(""bad"")"');
  expect(csvCell(2200)).toBe('"2200"');
});
