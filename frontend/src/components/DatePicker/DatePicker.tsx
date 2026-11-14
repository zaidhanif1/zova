import { useState } from "react";
import * as Popover from "@radix-ui/react-popover";
import { DayPicker } from "react-day-picker";
import type { DateRange } from "react-day-picker";
import { format, parseISO } from "date-fns";
// @ts-ignore CSS is loaded by Vite.
import "react-day-picker/style.css";
// @ts-ignore CSS is loaded by Vite.
import "./DatePicker.css";

interface DatePickerProps
{
    startDate: string;
    endDate: string;
    disabled?: boolean;
    onChange: (startDate: string, endDate: string) => void;
}

function describeRange(startDate: string, endDate: string): string
{
    if (!startDate && !endDate)
    {
        return "Any dates";
    }

    if (!startDate)
    {
        return `Until ${format(parseISO(endDate), "MMM d, yyyy")}`;
    }

    const start = parseISO(startDate);

    if (!endDate)
    {
        return `From ${format(start, "MMM d, yyyy")}`;
    }

    const end = parseISO(endDate);

    if (startDate === endDate)
    {
        return format(start, "MMM d, yyyy");
    }

    if (start.getFullYear() !== end.getFullYear())
    {
        return `${format(start, "MMM d, yyyy")} – ${format(end, "MMM d, yyyy")}`;
    }

    return `${format(start, "MMM d")} – ${format(end, "MMM d, yyyy")}`;
}

// Adapted from shadcn/ui's Popover + Calendar composition, using local CSS.
export default function DatePicker({ startDate, endDate, disabled, onChange }: DatePickerProps)
{
    const [open, setOpen] = useState(false);
    const [draft, setDraft] = useState<DateRange | undefined>();

    function changeOpen(nextOpen: boolean)
    {
        if (nextOpen)
        {
            setDraft(startDate || endDate ?
            {
                from: startDate ? parseISO(startDate) : undefined,
                to: endDate ? parseISO(endDate) : undefined,
            } : undefined);
        }

        setOpen(nextOpen);
    }

    return (
        <div className="date-picker-summary">
            <p id="event-date-summary" aria-live="polite">{describeRange(startDate, endDate)}</p>

            <Popover.Root open={open && !disabled} onOpenChange={changeOpen}>
                <Popover.Trigger asChild>
                    <button type="button" className="date-picker-trigger" disabled={disabled} aria-describedby="event-date-summary">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
                            <rect x="3" y="5" width="18" height="16" rx="2" />
                            <path d="M16 3v4M8 3v4M3 11h18" />
                        </svg>
                        Change dates
                    </button>
                </Popover.Trigger>

                <Popover.Portal>
                    <Popover.Content className="date-picker-popover" align="start" sideOffset={8} collisionPadding={12} aria-label="Event dates">
                        <p className="date-picker-help">Choose a start and end date, then apply.</p>
                        <DayPicker
                            mode="range"
                            selected={draft}
                            defaultMonth={draft?.from ?? draft?.to}
                            autoFocus
                            showOutsideDays
                            onSelect={setDraft}
                        />
                        <div className="date-picker-actions">
                            <button
                                type="button"
                                className="date-picker-clear"
                                onClick={() =>
                                {
                                    onChange("", "");
                                    setOpen(false);
                                }}
                            >
                                Clear dates
                            </button>
                            <button
                                type="button"
                                onClick={() =>
                                {
                                    // Keep calendar days intact rather than converting through UTC.
                                    onChange(
                                        draft?.from ? format(draft.from, "yyyy-MM-dd") : "",
                                        draft?.to ? format(draft.to, "yyyy-MM-dd") : ""
                                    );
                                    setOpen(false);
                                }}
                            >
                                Apply dates
                            </button>
                        </div>
                    </Popover.Content>
                </Popover.Portal>
            </Popover.Root>
        </div>
    );
}
