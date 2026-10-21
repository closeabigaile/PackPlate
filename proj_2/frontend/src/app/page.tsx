import Link from "next/link";

// Welcome page. "About" in the header comes back here.
export default function WelcomePage() {
  return (
    <main className="page">
      <section className="hero" aria-labelledby="welcome-title">
        <h1 id="welcome-title">
          Welcome to Pack<span>Plate</span>
        </h1>
        <p>
          PackPlate helps NC State students decide where to eat on campus. It
          puts dining hours, menus and nutrition for every campus dining
          location in one place, and filters the menus for your allergies and
          diet.
        </p>
        <div className="button-row">
          <Link href="/home" className="btn">
            Get started
          </Link>
        </div>
      </section>

      <div className="page-body">
        <section aria-labelledby="about-title">
          <h2 id="about-title" className="section-title">
            What you can do
          </h2>
          <div className="about-grid">
            <div className="about-card">
              <h3>See what’s open</h3>
              <p>
                Hours for every dining location, with what’s open right now and
                when the rest open again.
              </p>
            </div>
            <div className="about-card">
              <h3>Eat for your diet</h3>
              <p>
                Set allergies and preferences like vegetarian, halal or a
                protein goal, and see which items fit.
              </p>
            </div>
            <div className="about-card">
              <h3>Eat as a group</h3>
              <p>
                Add everyone’s diets and find a location where each person has
                something to eat.
              </p>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
