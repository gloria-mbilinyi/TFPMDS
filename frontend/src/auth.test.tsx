import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { SessionProvider } from "./session";
import { App } from "./App";

beforeEach(() => {
  sessionStorage.clear();
  vi.stubGlobal("fetch", vi.fn());
});
afterEach(() => vi.unstubAllGlobals());

it("shows actionable API errors when login fails", async () => {
  vi.mocked(fetch).mockResolvedValue(
    new Response(
      JSON.stringify({
        detail: { message: "Incorrect credentials or inactive account." },
      }),
      { status: 401 },
    ),
  );
  render(
    <MemoryRouter initialEntries={["/login"]}>
      <SessionProvider>
        <App />
      </SessionProvider>
    </MemoryRouter>,
  );
  await userEvent.type(
    await screen.findByLabelText("Email address"),
    "buyer@tfpmds.demo",
  );
  await userEvent.type(screen.getByLabelText("Password"), "wrong-password");
  await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Incorrect credentials",
  );
});

it("fills the chosen demo credentials without submitting automatically", async () => {
  render(
    <MemoryRouter initialEntries={["/login"]}>
      <SessionProvider>
        <App />
      </SessionProvider>
    </MemoryRouter>,
  );
  await userEvent.selectOptions(
    await screen.findByLabelText("Choose a demo account"),
    "buyer",
  );
  expect(screen.getByLabelText("Email address")).toHaveValue(
    "buyer@tfpmds.demo",
  );
  expect(screen.getByLabelText("Password")).toHaveValue("DemoPass123!");
  expect(fetch).not.toHaveBeenCalled();
});
