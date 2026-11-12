import { useState } from "react";
import type { FormEvent } from "react";

interface TicketmasterEvent
{
    name?: string;
    dates?:
    {
        start?: { localDate?: string; localTime?: string; dateTBD?: boolean; timeTBA?: boolean; noSpecificTime?: boolean };
        timezone?: string;
    };
    _embedded?: { venues?: { name?: string }[] };
}

function readEvents(payload: unknown): TicketmasterEvent[]
{
    if (!payload || typeof payload !== "object" || Array.isArray(payload))
    {
        throw new Error("The event service returned an invalid response. Please try again.");
    }

    const embedded = (payload as { _embedded?: { events?: unknown } })._embedded;

    // Ticketmaster can omit _embedded entirely when no events match.
    if (embedded === undefined)
    {
        return [];
    }

    if (!embedded || !Array.isArray(embedded.events) || embedded.events.some((event) =>
    {
        return !event || typeof event !== "object" || Array.isArray(event);
    }))
    {
        throw new Error("The event service returned an invalid response. Please try again.");
    }

    return embedded.events.slice(0, 5) as TicketmasterEvent[];
}

function textOrFallback(value: unknown, fallback: string)
{
    return typeof value === "string" && value.trim() ? value : fallback;
}

export default function EventSearch()
{
    const [city, setCity] = useState("");
    const [submittedCity, setSubmittedCity] = useState("");
    const [events, setEvents] = useState<TicketmasterEvent[] | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");

    async function searchEvents(event: FormEvent<HTMLFormElement>)
    {
        event.preventDefault();

        if (isLoading)
        {
            return;
        }

        const queryCity = city.trim();

        setError("");
        setEvents(null);

        if (!queryCity)
        {
            setError("Enter a city to search for events.");
            return;
        }

        setSubmittedCity(queryCity);
        setIsLoading(true);

        try
        {
            const response = await fetch(`/get_events?${new URLSearchParams(
            {
                city: queryCity,
            })}`);

            if (!response.ok)
            {
                throw new Error(response.status === 503
                    ? "Event search is unavailable. Check that the backend has a Ticketmaster API key configured."
                    : `Could not load events (HTTP ${response.status}). Please try again.`);
            }

            setEvents(readEvents(await response.json()));
        }
        catch (requestError)
        {
            setError(requestError instanceof TypeError
                ? "Could not reach event search. Make sure FastAPI is running on port 8000, then try again."
                : requestError instanceof SyntaxError
                    ? "The event service returned an invalid response. Please try again."
                    : requestError instanceof Error
                        ? requestError.message
                        : "Could not load events. Please try again.");
        }
        finally
        {
            setIsLoading(false);
        }
    }

    return (
        <section className="event-search" id="events" aria-labelledby="event-search-title">
            <div className="planner-intro">
                <p className="eyebrow">DISCOVER SOMETHING LIVE</p>
                <h2 id="event-search-title">Find events in your city</h2>
                <p>Showing up to five events in the order Ticketmaster returns them. No additional ranking is applied.</p>
            </div>
            <div className="planner-layout">
                <form className="preferences-card" onSubmit={searchEvents}>
                    <label htmlFor="event-city">City</label>
                    <div className="budget-input">
                        <input
                            id="event-city"
                            type="text"
                            placeholder="e.g. New York"
                            required
                            value={city}
                            disabled={isLoading}
                            onChange={(event) => setCity(event.target.value)}
                        />
                    </div>
                    <p className="input-help">Search by city name.</p>
                    <button type="submit" disabled={isLoading}>
                        {isLoading ? "Searching events…" : "Find events"}
                    </button>
                    <p className="fixture-note">Live Ticketmaster search · Separate from the synthetic planner.</p>
                </form>
                <div aria-live="polite" aria-busy={isLoading}>
                    {isLoading && <p role="status">Searching Ticketmaster…</p>}
                    {error && <p className="error-message" role="alert">{error}</p>}
                    {!isLoading && !error && events === null && <p>Enter a city to discover events.</p>}
                    {events && (
                        <>
                            <h3 className="results-heading">{events.length} events for {submittedCity}</h3>
                            {events.length === 0 && <p>No events found. Try another city.</p>}
                            <ol className="activity-list" aria-label="Ticketmaster events">
                                {events.map((event, index) =>
                                {
                                    const start = event.dates?.start;
                                    const date = start?.dateTBD ? "Date to be confirmed" : textOrFallback(start?.localDate, "Date unavailable");
                                    const time = start?.timeTBA || start?.noSpecificTime ? "Time to be confirmed" : textOrFallback(start?.localTime, "Time unavailable");

                                    return (
                                        <li className="activity-card" key={index}>
                                            <span className="stop-number">{index + 1}</span>
                                            <div className="activity-details">
                                                <h3>{textOrFallback(event.name, "Untitled event")}</h3>
                                                <p>{textOrFallback(event._embedded?.venues?.[0]?.name, "Venue unavailable")}</p>
                                                <p className="muted">{date} · {time}</p>
                                                <p className="muted">Event local time · {textOrFallback(event.dates?.timezone, "Timezone unavailable")}</p>
                                            </div>
                                        </li>
                                    );
                                })}
                            </ol>
                            <p className="result-note">Source: Ticketmaster. Event details may change; no reservation is implied.</p>
                        </>
                    )}
                </div>
            </div>
        </section>
    );
}
