// @ts-ignore CSS is loaded by the bundler and has no TypeScript declarations.
import "../shared/PlannerShared.css";
// @ts-ignore CSS is loaded by the bundler and has no TypeScript declarations.

import "./EventSearch.css";
import { useState } from "react";
import type { FormEvent } from "react";

interface TicketmasterEvent
{
    name?: string;
    dates?:
    {
        start?:
        {
            localDate?: string;
            localTime?: string;
            dateTBD?: boolean;
            timeTBA?: boolean;
            noSpecificTime?: boolean;
        };
        timezone?: string;
    };
    // Related venue records included with this event.
    _embedded?:
    {
        venues?:
        {
            name?: string;
        }[];
    };
}

interface TicketmasterSearchResponse
{
    // Event records included with the search response.
    _embedded?:
    {
        events?: unknown;
    };
}

function readEvents(payload: unknown): TicketmasterEvent[]
{
    if (!payload || typeof payload !== "object" || Array.isArray(payload))
    {
        throw new Error("The event service returned an invalid response. Please try again.");
    }

    const response = payload as TicketmasterSearchResponse;
    const embedded = response._embedded;

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
    const [keyword, setKeyword] = useState("");

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
        const queryKeyword = keyword.trim();
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
            const searchParams = new URLSearchParams(
            {
                city: queryCity,
            });

            if (queryKeyword)
            {
                searchParams.set("keyword", queryKeyword);
            }

            const response = await fetch(`/get_events?${searchParams}`);

            if (!response.ok)
            {
                if (response.status === 503)
                {
                    throw new Error(
                        "Event search is unavailable. Check that the backend has a Ticketmaster API key configured."
                    );
                }

                throw new Error(`Could not load events (HTTP ${response.status}). Please try again.`);
            }

            setEvents(readEvents(await response.json()));
        }
        catch (requestError)
        {
            if (requestError instanceof TypeError)
            {
                setError("Could not reach event search. Make sure FastAPI is running on port 8000, then try again.");
            }
            else if (requestError instanceof SyntaxError)
            {
                setError("The event service returned an invalid response. Please try again.");
            }
            else if (requestError instanceof Error)
            {
                setError(requestError.message);
            }
            else
            {
                setError("Could not load events. Please try again.");
            }
        }
        finally
        {
            setIsLoading(false);
        }
    }

    return (
        <section
            className="event-search"
            id="events"
            aria-labelledby="event-search-title"
        >
            <div className="planner-intro">
                <p className="eyebrow">DISCOVER SOMETHING LIVE</p>

                <h2 id="event-search-title">Find events in your city</h2>

                <p>
                    Showing up to five events in the order Ticketmaster returns them.
                    No additional ranking is applied.
                </p>
            </div>

            <div className="planner-layout">

                <form className="preferences-card" onSubmit={searchEvents}>

                    <label htmlFor="event-city">City</label>

                    <div className="event-input">
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

                    <label htmlFor="event-keyword">Keyword (optional)</label>

                    <div className="keyword-input">
                        <input
                            id="event-keyword"
                            type="text"
                            placeholder="e.g. concerts, sports"
                            value={keyword}
                            disabled={isLoading}
                            onChange={(event) => setKeyword(event.target.value)}
                        />
                    </div>

                    <p className="input-help">Narrow your search, or leave blank for all events.</p>

                    <button type="submit" disabled={isLoading}>
                        {isLoading ? "Searching events…" : "Find events"}
                    </button>

                    <p className="fixture-note">
                        Live Ticketmaster search · Separate from the synthetic planner.
                    </p>
                </form>

                <div aria-live="polite" aria-busy={isLoading}>
                    {isLoading && (
                        <p role="status">Searching Ticketmaster…</p>
                    )}

                    {error && (
                        <p className="error-message" role="alert">
                            {error}
                        </p>
                    )}

                    {!isLoading && !error && events === null && (
                        <p>Enter a city to discover events.</p>
                    )}

                    {events && (
                        <>
                            <h3 className="results-heading">
                                {events.length} events for {submittedCity}
                            </h3>

                            {events.length === 0 && (
                                <p>No events found. Try another city.</p>
                            )}

                            <ol className="activity-list" aria-label="Ticketmaster events">
                                {events.map((event, index) =>
                                {
                                    const start = event.dates?.start;
                                    const venue = event._embedded?.venues?.[0];

                                    const date = start?.dateTBD
                                        ? "Date to be confirmed"
                                        : textOrFallback(start?.localDate, "Date unavailable");

                                    const time = start?.timeTBA || start?.noSpecificTime
                                        ? "Time to be confirmed"
                                        : textOrFallback(start?.localTime, "Time unavailable");

                                    return (
                                        <li className="activity-card" key={index}>
                                            <span className="stop-number">{index + 1}</span>

                                            <div className="activity-details">
                                                <h3>
                                                    {textOrFallback(event.name, "Untitled event")}
                                                </h3>

                                                <p>
                                                    {textOrFallback(venue?.name, "Venue unavailable")}
                                                </p>

                                                <p className="muted">
                                                    {date} · {time}
                                                </p>

                                                <p className="muted">
                                                    Event local time · {textOrFallback(
                                                        event.dates?.timezone,
                                                        "Timezone unavailable"
                                                    )}
                                                </p>
                                            </div>
                                        </li>
                                    );
                                })}
                            </ol>

                            <p className="result-note">
                                Source: Ticketmaster. Event details may change; no reservation is implied.
                            </p>
                        </>
                    )}
                </div>
            </div>
        </section>
    );
}
