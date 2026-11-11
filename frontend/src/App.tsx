import { useState } from "react";
import type { FormEvent } from "react";
import demoProfile from "../../src/zova/data/profile.json";
import demoActivities from "../../src/zova/data/activities.json";
import EventSearch from "./EventSearch";

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

export default function App()
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
        <div className="page">
            <header className="site-header">
                <a className="brand" href="/" aria-label="Zova home">
                    zova<span>✳</span>
                </a>
                <nav className="header-nav" aria-label="Main navigation">
                    <a href="#how-it-works">How it works</a>
                    <a href="#events">Find events</a>
                    <a className="nav-cta" href="#planner">Try the demo <span aria-hidden="true">↗</span></a>
                </nav>
            </header>

            <main>
                <section className="welcome" aria-labelledby="welcome-title">
                    <div className="welcome-copy">
                        <p className="eyebrow">A LITTLE CURIOSITY GOES A LONG WAY</p>
                        <h1 id="welcome-title">Your weekend.<br /><span>Your kind of wonderful.</span></h1>
                        <p className="welcome-description">
                            Less time piecing together a plan. More time finding your
                            favorite corner of a city. Meet Zova, a little help for
                            a day that feels like you.
                        </p>
                        <div className="welcome-actions">
                            <a className="primary-link" href="#planner">Try the planner <span aria-hidden="true">↗</span></a>
                            <a className="text-link" href="#how-it-works">Take a look around <span aria-hidden="true">↓</span></a>
                        </div>
                        <p className="welcome-note"><span aria-hidden="true">✳</span> Start with a fictional Saturday in New York.</p>
                    </div>
                    <div className="city-postcard">
                        <div className="postcard-top"><span>FIELD NOTES / 001</span><span>NEW YORK, NY</span></div>
                        <svg className="city-scene" viewBox="0 0 480 360" role="img" aria-labelledby="city-title">
                            <title id="city-title">An illustrated New York afternoon, with city buildings and a winding park path</title>
                            <circle cx="350" cy="83" r="47" fill="#e7b96c" />
                            <path d="M20 270V142h65v128M94 270V104h55v166M162 270V67h68v203M187 67V42h18v25M196 42V18M246 270V130h75v140M337 270V173h51v97M399 270V113h61v157" fill="#b7c1ac" stroke="#607966" strokeWidth="2" />
                            <path d="M31 160h42m-42 22h42m-42 22h42m31-80h34m-34 23h34m-34 23h34m33-79h46m-46 22h46m-46 22h46m-46 22h46m39-6h49m-49 24h49m-49 24h49m99-65h38m-38 24h38m-38 24h38" stroke="#f4eddb" strokeWidth="5" />
                            <path d="M0 258Q110 213 218 254T480 247V360H0Z" fill="#859b73" />
                            <path d="M0 310Q101 266 235 304T480 286V360H0Z" fill="#516f50" />
                            <path d="M221 254C148 280 362 297 275 360" fill="none" stroke="#e8d7b2" strokeWidth="36" />
                            <g fill="#345d46"><ellipse cx="60" cy="236" rx="33" ry="48" /><ellipse cx="405" cy="242" rx="37" ry="52" /></g>
                            <path d="M60 237v65m345-58v70" stroke="#d6c6a3" strokeWidth="4" />
                            <path d="M95 305h61m-55 0v18m49-18v18m-52-30h55v12H98Z" stroke="#e8d7b2" strokeWidth="4" fill="none" />
                        </svg>
                        <div className="postcard-caption"><span>A city full of possibilities.<br /><strong>A day with room for you.</strong></span><span className="postcard-star" aria-hidden="true">✳</span></div>
                        <span className="postcard-label">AN ILLUSTRATION, NOT A LIVE DESTINATION GUIDE</span>
                    </div>
                </section>

                <section className="how-it-works" id="how-it-works" aria-labelledby="how-title">
                    <div><p className="eyebrow">THOUGHTFUL BY DESIGN</p><h2 id="how-title">A little structure.<br />A lot to discover.</h2></div>
                    <ol className="steps">
                        <li><span>01 / YOUR INTERESTS</span><h3>Start with what you love.</h3><p>Our sample traveler loves architecture, thrift finds, and street food.</p></li>
                        <li><span>02 / YOUR BOUNDARIES</span><h3>Leave room for real life.</h3><p>Set an activity budget. The demo keeps a fixed 2–4 PM commitment free.</p></li>
                        <li><span>03 / YOUR DAY OUT</span><h3>Make a plan. Make it yours.</h3><p>See the selected stops and estimated costs. Change the budget and try again.</p></li>
                    </ol>
                </section>

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
                <EventSearch />
            </main>
            <footer>
                Thoughtfully planned. Open to possibility.
                <span>ZOVA / WEEKEND PLANNER</span>
            </footer>
        </div>
    );
}
