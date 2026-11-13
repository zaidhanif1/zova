// @ts-ignore CSS is loaded by the bundler and has no TypeScript declarations.
import "../shared/PlannerShared.css";
// @ts-ignore CSS is loaded by the bundler and has no TypeScript declarations.
import "./WeekendPlanner.css";
import { useState } from "react";
import type { FormEvent } from "react";
import demoProfile from "../../../../src/zova/data/profile.json";
import demoActivities from "../../../../src/zova/data/activities.json";

interface TimeWindow
{
    start: string;
    end: string;
}

interface Profile
{
    name: string;
    destination: string;
    budget: string;
    currency: string;
    preferences: string[];
    trip: TimeWindow;
    unavailable: TimeWindow[];
}

interface Activity
{
    id: string;
    title: string;
    destination: string;
    categories: string[];
    cost: string;
    currency: string;
    duration_minutes: number;
    schedule: TimeWindow;
    source: string;
}

interface ItineraryResponse
{
    message: string;
    total_cost: string;
    profile: Profile;
    activities: Activity[];
}

// Show destination time, even when the browser is in another timezone.
function formatTime(timestamp: string)
{
    const formatter = new Intl.DateTimeFormat("en-US",
    {
        hour: "numeric",
        minute: "2-digit",
        timeZone: "America/New_York",
    })

    const res = formatter.format(new Date(timestamp));
    return res;
}

function formatMoney(amount: string, currency: string)
{
    // Formatting only: the backend still performs all budget arithmetic with Decimal.
    const formatter = new Intl.NumberFormat("en-US",
    {
        style: "currency",
        currency,
    });

    const res = formatter.format(Number(amount));

    return res;
}

export default function WeekendPlanner()
{
    // State remembers values between renders; updating it refreshes the screen.
    const [budget, setBudget] = useState(demoProfile.budget);
    const [itinerary, setItinerary] = useState<ItineraryResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");

    async function generateItinerary(event: FormEvent<HTMLFormElement>)
    {
        event.preventDefault(); // Submit with fetch instead of reloading the page.

        setIsLoading(true);
        setError("");
        setItinerary(null); // Never show an old plan as the result of a new request.

        try
        {
            const response = await fetch("/itinerary",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(
                {
                    profile: { ...demoProfile, budget },
                    activities: demoActivities,
                }),
            });

            // fetch rejects network failures, but HTTP errors need an explicit check.
            if (!response.ok)
            {
                if (response.status === 422)
                {
                    throw new Error(
                        "The planner could not validate these inputs. Check your budget and try again.",
                    );
                }

                throw new Error(
                    `The planner could not generate an itinerary (HTTP ${response.status}). Please try again.`,
                );
            }

            const result: ItineraryResponse = await response.json();

            setItinerary(result);
        }
        catch (requestError)
        {
            if (requestError instanceof TypeError)
            {
                setError("Could not reach the planner. Make sure FastAPI is running on port 8000, then try again.");
            }
            else if (requestError instanceof Error)
            {
                setError(requestError.message);
            }
            else
            {
                setError("Something went wrong. Please try again.");
            }
        }
        finally
        {
            setIsLoading(false);
        }
    }

    return (
        <>
            <section className="planner-intro" id="planner" aria-labelledby="planner-title">
                <p className="eyebrow">MEET YOUR NEXT SATURDAY</p>
                <h2 id="planner-title">A small demo. A day of possibilities.</h2>
                <p>Explore the weekend planner with synthetic data. Only the budget is editable;<br className="desktop-break" /> no live prices, reservations, or route estimates are included.</p>
            </section>

            <div className="planner-layout">
                <aside className="preferences-card">
                    <p className="eyebrow">YOUR STARTING POINT</p>
                    <h2>Saturday in New York</h2>
                    <p className="muted">October 24, 2026 · 9 AM – 6 PM</p>
                    <div className="preference-tags">
                        {demoProfile.preferences.map((preference) => (
                            <span key={preference}>{preference}</span>
                        ))}
                    </div>
                    <div className="commitment">
                        <span aria-hidden="true">◷</span>
                        <div>
                            <strong>Fixed demo commitment</strong>
                            <p>2:00 - 4:00 PM · Time kept free</p>
                        </div>
                    </div>

                    <form onSubmit={generateItinerary}>
                        <label htmlFor="budget">
                            Your activity budget <span>USD</span>
                        </label>
                        <div className="budget-input">
                            <span aria-hidden="true">$</span>
                            <input
                                id="budget"
                                type="number"
                                min="0"
                                max="9999999999.99"
                                step="0.01"
                                required
                                value={budget}
                                disabled={isLoading}
                                onChange={(event) => setBudget(event.target.value)}
                            />
                        </div>
                        <p className="input-help">
                            Activities and food only. You can change this anytime.
                        </p>
                        <button type="submit" disabled={isLoading}>
                            {isLoading ? "Planning your day…" : "Generate Itinerary"}{" "}
                            <span aria-hidden="true">↗</span>
                        </button>
                    </form>
                    <p className="fixture-note">
                        Synthetic demo · No bookings or live prices.
                        <br />
                        Transport, taxes, and tips aren’t included.
                    </p>
                </aside>

                <section
                    className="results"
                    aria-labelledby="results-title"
                    aria-busy={isLoading}
                >
                    <div className="results-heading">
                        <div>
                            <p className="eyebrow">A LITTLE STRUCTURE, A LOT TO DISCOVER</p>
                            <h2 id="results-title">Your day, at a glance</h2>
                        </div>
                        {itinerary && (
                            <span className="stop-count">
                                {itinerary.activities.length} stops
                            </span>
                        )}
                    </div>
                    <div aria-live="polite" aria-atomic="true">
                        {isLoading && (
                            <div className="empty-state">
                                <span className="compass spinning" aria-hidden="true">
                                    ✳
                                </span>
                                <h3>Finding your kind of Saturday</h3>
                                <p>Checking your budget and keeping your afternoon free.</p>
                            </div>
                        )}
                        {error && (
                            <div className="error-message" role="alert">
                                <h3>Let’s try that again</h3>
                                <p>{error}</p>
                            </div>
                        )}
                        {!isLoading && !error && !itinerary && (
                            <div className="empty-state">
                                <span className="compass" aria-hidden="true">
                                    ✳
                                </span>
                                <h3>Your next good day starts here.</h3>
                                <p>
                                    Set your budget and generate a plan.
                                    <br />
                                    We’ll fit the stops around your existing commitment.
                                </p>
                                <span className="small-note">
                                    Seven synthetic activities. One day to make your own.
                                </span>
                            </div>
                        )}
                        {itinerary && itinerary.activities.length === 0 && (
                            <div className="empty-state">
                                <span className="compass" aria-hidden="true">
                                    ◌
                                </span>
                                <h3>No activities fit this budget.</h3>
                                <p>
                                    Try increasing your budget and generate another itinerary.
                                </p>
                            </div>
                        )}
                    </div>

                    {itinerary && (
                        <>
                            <ol className="activity-list">
                                {/* Each response activity becomes one visible list item. IDs give React stable keys. */}
                                {itinerary.activities.map((activity, index) => (
                                    <li key={activity.id} className="activity-card">
                                        <span className="stop-number">
                                            {String(index + 1).padStart(2, "0")}
                                        </span>
                                        <div className="activity-details">
                                            <p className="activity-time">
                                                <time dateTime={activity.schedule.start}>
                                                    {formatTime(activity.schedule.start)}
                                                </time>{" "}
                                                –{" "}
                                                <time dateTime={activity.schedule.end}>
                                                    {formatTime(activity.schedule.end)}
                                                </time>
                                            </p>
                                            <h3>{activity.title}</h3>
                                            <p className="muted">
                                                {activity.categories.join(" · ")} ·{" "}
                                                {activity.duration_minutes} min
                                            </p>
                                        </div>
                                        <strong className="activity-cost">
                                            {formatMoney(activity.cost, activity.currency)}
                                        </strong>
                                    </li>
                                ))}
                            </ol>
                            <div className="total">
                                <div>
                                    <p>Estimated activity total</p>
                                    <span>
                                        Of{" "}
                                        {formatMoney(
                                            itinerary.profile.budget,
                                            itinerary.profile.currency,
                                        )}{" "}
                                        submitted budget
                                    </span>
                                </div>
                                <strong>
                                    {formatMoney(
                                        itinerary.total_cost,
                                        itinerary.profile.currency,
                                    )}
                                </strong>
                            </div>
                            <p className="result-note">
                                All times in New York (America/New_York). Synthetic estimates,
                                not reservations.
                            </p>
                        </>
                    )}
                </section>
            </div>
        </>
    );
}
