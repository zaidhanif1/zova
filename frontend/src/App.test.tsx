// @vitest-environment jsdom
import { afterEach, expect, test, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import App from "./App";
import profile from "../../src/zova/data/profile.json";
import activities from "../../src/zova/data/activities.json";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function mockResponse(status: number, body: unknown) {
  const fetchMock = vi
    .fn()
    .mockResolvedValue(new Response(JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

test("submits fixture data with the edited budget and displays the response", async () => {
  const fetchMock = mockResponse(200, {
    profile: { ...profile, budget: "30.00" },
    total_cost: "20.00",
    activities: [{ ...activities[0], currency: "USD" }],
    message: "Generated",
  });
  render(<App />);
  fireEvent.change(screen.getByLabelText(/Your activity budget/), {
    target: { value: "30.00" },
  });
  fireEvent.click(screen.getByRole("button", { name: /Generate Itinerary/ }));
  expect(await screen.findByText(activities[0].title)).toBeTruthy();
  expect(screen.getByText("9:00 AM")).toBeTruthy();
  expect(screen.getAllByText("$20.00")).toHaveLength(2);
  const [url, options] = fetchMock.mock.calls[0];
  expect(url).toBe("/itinerary");
  expect(options.method).toBe("POST");
  expect(JSON.parse(options.body)).toEqual({
    profile: { ...profile, budget: "30.00" },
    activities,
  });
});

test("shows loading, prevents duplicate submissions, and explains an empty plan", async () => {
  let finishRequest = (_response: Response) => {};
  vi.stubGlobal(
    "fetch",
    vi.fn(
      () =>
        new Promise<Response>((resolve) => {
          finishRequest = resolve;
        }),
    ),
  );
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: /Generate Itinerary/ }));
  expect(
    (
      screen.getByRole("button", {
        name: /Planning your day/,
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  finishRequest(
    new Response(
      JSON.stringify({
        profile,
        total_cost: "0.00",
        activities: [],
        message: "Generated",
      }),
    ),
  );
  expect(
    await screen.findByText("No activities fit this budget."),
  ).toBeTruthy();
  expect(screen.getByText("$0.00")).toBeTruthy();
});

test.each([422, 500])("handles HTTP %s and allows retry", async (status) => {
  mockResponse(status, { detail: "error" });
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: /Generate Itinerary/ }));
  expect(await screen.findByRole("alert")).toBeTruthy();
  await waitFor(() =>
    expect(
      (
        screen.getByRole("button", {
          name: /Generate Itinerary/,
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false),
  );
});

test("explains network failures", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
  );
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: /Generate Itinerary/ }));
  expect(await screen.findByText(/Make sure FastAPI is running/)).toBeTruthy();
});
