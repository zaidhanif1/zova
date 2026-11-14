// @vitest-environment jsdom
import { afterEach, expect, test, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import DatePicker from "../components/DatePicker/DatePicker";

afterEach(cleanup);

test.each([
    ["2026-11-19", "2026-11-25", "Nov 19 – Nov 25, 2026"],
    ["2026-11-19", "2026-12-02", "Nov 19 – Dec 2, 2026"],
    ["2026-12-31", "2027-01-02", "Dec 31, 2026 – Jan 2, 2027"],
    ["2026-11-19", "2026-11-19", "Nov 19, 2026"],
    ["2026-11-19", "", "From Nov 19, 2026"],
    ["", "2026-11-25", "Until Nov 25, 2026"],
])("summarizes %s through %s", (startDate, endDate, summary) =>
{
    render(<DatePicker startDate={startDate} endDate={endDate} onChange={vi.fn()} />);
    expect(screen.getByText(summary)).toBeTruthy();
});

test("disables the calendar trigger during search", () =>
{
    render(<DatePicker startDate="" endDate="" onChange={vi.fn()} disabled />);
    expect((screen.getByRole("button", { name: "Change dates" }) as HTMLButtonElement).disabled).toBe(true);
});
