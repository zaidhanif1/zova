// @vitest-environment jsdom
import { afterEach, expect, test, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import App from "../components/App/App";

afterEach(() =>
{
    cleanup();
    vi.unstubAllGlobals();
});

test("welcomes visitors and links to the clearly labeled local demo without fetching", () =>
{
    const fetchMock = vi.fn();

    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    expect(screen.getByRole("heading",
    {
        level: 1,
    }).textContent).toContain("Your weekend.");

    for (const name of [/Try the planner/, /Try the demo/, /How it works/, /Take a look around/])
    {
        const link = screen.getByRole("link",
        {
            name,
        });
        const target = link.getAttribute("href");

        expect(target?.startsWith("#")).toBe(true);
        expect(document.getElementById(target!.slice(1))).toBeTruthy();
    }

    expect(screen.getByText(/Only the budget is editable/)).toBeTruthy();
    expect(screen.getByText("Fixed demo commitment")).toBeTruthy();
    expect(fetchMock).not.toHaveBeenCalled();
});
