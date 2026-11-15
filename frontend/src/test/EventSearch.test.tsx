// @vitest-environment jsdom
import { afterEach, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import EventSearch from "../components/EventSearch/EventSearch";

afterEach(() =>
{
    cleanup();
    vi.unstubAllGlobals();
});

function submitCity(city = "New York")
{
    fireEvent.change(screen.getByLabelText("City"),
    {
        target: { value: city },
    });
    fireEvent.submit(screen.getByLabelText("City").closest("form")!);
}

function response(body: unknown, status = 200)
{
    return new Response(JSON.stringify(body),
    {
        status,
    });
}

test("requests an encoded trimmed city and preserves the first five results in order", async () =>
{
    const events = ["Zebra", "Alpha", "Third", "Fourth", "Fifth", "Sixth"].map((name) =>
    {
        return {
            name,
            dates: { start: { localDate: "2026-12-01", localTime: "19:00:00" }, timezone: "America/New_York" },
            _embedded: { venues: [{ name: "Demo venue" }] },
        };
    });
    const fetchMock = vi.fn().mockResolvedValue(response({ _embedded: { events } }));

    vi.stubGlobal("fetch", fetchMock);
    render(<EventSearch />);
    expect(fetchMock).not.toHaveBeenCalled();
    submitCity("  New York & Boston  ");

    await screen.findByText("Zebra");
    expect(fetchMock).toHaveBeenCalledWith("/get_events?city=New+York+%26+Boston");
    expect(screen.getAllByRole("listitem").map((item) => item.querySelector("h3")?.textContent))
        .toEqual(["Zebra", "Alpha", "Third", "Fourth", "Fifth"]);
    expect(screen.queryByText("Sixth")).toBeNull();
    expect(screen.getAllByText("Demo venue")).toHaveLength(5);
    expect(screen.getAllByText(/2026-12-01/)).toHaveLength(5);
});

test.each([{}, { _embedded: { events: [] } }])("handles empty results %j", async (body) =>
{
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(body)));
    render(<EventSearch />);
    submitCity();
    expect(await screen.findByText(/No events found/)).toBeTruthy();
});

test("renders fewer than five events with missing details", async () =>
{
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response({ _embedded: { events: [{}] } })));
    render(<EventSearch />);
    submitCity();
    expect(await screen.findByText("Untitled event")).toBeTruthy();
    expect(screen.getByText("Venue unavailable")).toBeTruthy();
    expect(screen.getByText(/Date unavailable/)).toBeTruthy();
    expect(screen.getAllByRole("listitem")).toHaveLength(1);
});

test("rejects whitespace without fetching", async () =>
{
    const fetchMock = vi.fn();

    vi.stubGlobal("fetch", fetchMock);
    render(<EventSearch />);
    submitCity("   ");
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(fetchMock).not.toHaveBeenCalled();
});

test.each([500, 503])("handles HTTP %s and permits a successful retry", async (status) =>
{
    const fetchMock = vi.fn().mockResolvedValueOnce(response({}, status)).mockResolvedValueOnce(response({}));

    vi.stubGlobal("fetch", fetchMock);
    render(<EventSearch />);
    submitCity();
    await screen.findByRole("alert");
    submitCity("Boston");
    expect(await screen.findByText(/No events found/)).toBeTruthy();
    expect(screen.queryByRole("alert")).toBeNull();
});

test("explains a network failure", async () =>
{
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    render(<EventSearch />);
    submitCity();
    expect(await screen.findByRole("alert")).toHaveProperty("textContent", expect.stringContaining("FastAPI"));
});

test("rejects malformed event data", async () =>
{
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response({ _embedded: { events: "bad" } })));
    render(<EventSearch />);
    submitCity();
    expect(await screen.findByRole("alert")).toHaveProperty("textContent", expect.stringContaining("invalid response"));
});

test("clears old results and disables submission while searching", async () =>
{
    let finish = (_value: Response) =>
    {
    };
    const fetchMock = vi.fn().mockResolvedValueOnce(response({ _embedded: { events: [{ name: "Old event" }] } }))
        .mockImplementationOnce(() => new Promise<Response>((resolve) =>
        {
            finish = resolve;
        }));

    vi.stubGlobal("fetch", fetchMock);
    render(<EventSearch />);
    submitCity();
    await screen.findByText("Old event");
    submitCity("Boston");
    expect(screen.queryByText("Old event")).toBeNull();
    expect((screen.getByRole("button", { name: "Searching events…" }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByRole("status")).toBeTruthy();
    fireEvent.submit(screen.getByLabelText("City").closest("form")!);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    finish(response({}));
    await screen.findByText(/No events found/);
});


test.each([
    ["  jazz & blues  ", "/get_events?city=Boston&keyword=jazz+%26+blues"],
    ["   ", "/get_events?city=Boston"],
])("handles optional keyword %j", async (keyword, expectedUrl) =>
{
    const fetchMock = vi.fn().mockResolvedValue(response({}));

    vi.stubGlobal("fetch", fetchMock);
    render(<EventSearch />);

    fireEvent.change(screen.getByLabelText("Keyword (optional)"),
    {
        target: { value: keyword },
    });
    submitCity("Boston");

    await screen.findByText(/No events found/);
    expect(fetchMock).toHaveBeenCalledWith(expectedUrl);
});

test("selects, applies, and clears a date range", async () =>
{
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(response({})));

    vi.stubGlobal("fetch", fetchMock);
    render(<EventSearch />);
    expect(screen.getByText("Any dates")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Change dates" }));
    const dialog = await screen.findByRole("dialog", { name: "Event dates" });
    const days = dialog.querySelectorAll<HTMLButtonElement>(".rdp-day:not(.rdp-outside) .rdp-day_button");
    const start = days[9].closest("[data-day]")!.getAttribute("data-day");
    const end = days[14].closest("[data-day]")!.getAttribute("data-day");
    fireEvent.click(days[9]);
    fireEvent.click(days[14]);
    expect(screen.getByText("Any dates")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Apply dates" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.queryByText("Any dates")).toBeNull();
    submitCity("Boston");
    await screen.findByText(/No events found/);
    expect(fetchMock).toHaveBeenLastCalledWith(`/get_events?city=Boston&start_date=${start}&end_date=${end}`);

    fireEvent.click(screen.getByRole("button", { name: "Change dates" }));
    fireEvent.click(await screen.findByRole("button", { name: "Clear dates" }));
    expect(screen.getByText("Any dates")).toBeTruthy();
    submitCity("Boston");
    await screen.findByText(/No events found/);
    expect(fetchMock).toHaveBeenLastCalledWith("/get_events?city=Boston");
});

test("Escape discards a draft date selection", async () =>
{
    render(<EventSearch />);
    fireEvent.click(screen.getByRole("button", { name: "Change dates" }));
    const dialog = await screen.findByRole("dialog", { name: "Event dates" });
    fireEvent.click(dialog.querySelector<HTMLButtonElement>(".rdp-day_button")!);
    fireEvent.keyDown(dialog, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByText("Any dates")).toBeTruthy();
});

test("forwards optional filters with exact parameter names and preserves zero radius", async () =>
{
    const fetchMock = vi.fn().mockResolvedValue(response({}));

    vi.stubGlobal("fetch", fetchMock);
    render(<EventSearch />);

    for (const [label, value] of [
        ["State/province code", " NY "],
        ["Country code", "US"],
        ["Postal/ZIP code", " 10001 "],
        ["Search radius", "0"],
        ["Results per page", "7"],
    ])
    {
        fireEvent.change(screen.getByLabelText(`${label} (optional)`),
        {
            target: { value },
        });
    }

    submitCity("Boston");
    await screen.findByText(/No events found/);
    expect(fetchMock).toHaveBeenCalledWith(
        "/get_events?city=Boston&stateCode=NY&countryCode=US&postalCode=10001&radius=0&size=7"
    );
});

test.each([
    ["Search radius", "-1", "nonnegative"],
    ["Results per page", "0", "positive integer"],
    ["Results per page", "1.5", "positive integer"],
])("rejects invalid %s %s before fetching", async (label, value, message) =>
{
    const fetchMock = vi.fn();

    vi.stubGlobal("fetch", fetchMock);
    render(<EventSearch />);
    fireEvent.change(screen.getByLabelText(`${label} (optional)`),
    {
        target: { value },
    });
    submitCity();
    expect(await screen.findByRole("alert")).toHaveProperty("textContent", expect.stringContaining(message));
    expect(fetchMock).not.toHaveBeenCalled();
});

test("omits whitespace location filters", async () =>
{
    const fetchMock = vi.fn().mockResolvedValue(response({}));

    vi.stubGlobal("fetch", fetchMock);
    render(<EventSearch />);

    for (const label of ["State/province code", "Country code", "Postal/ZIP code"])
    {
        fireEvent.change(screen.getByLabelText(`${label} (optional)`),
        {
            target: { value: "  " },
        });
    }

    submitCity("Boston");
    await screen.findByText(/No events found/);
    expect(fetchMock).toHaveBeenCalledWith("/get_events?city=Boston");
});
