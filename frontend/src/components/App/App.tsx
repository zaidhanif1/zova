import "./App.css";
import EventSearch from "../EventSearch/EventSearch";
import WeekendPlanner from "../WeekendPlanner/WeekendPlanner";

export default function App()
{
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

                <WeekendPlanner />
                <EventSearch />
            </main>
            <footer>
                Thoughtfully planned. Open to possibility.
                <span>ZOVA / WEEKEND PLANNER</span>
            </footer>
        </div>
    );
}
