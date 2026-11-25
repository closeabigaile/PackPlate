import Link from "next/link";
import { Icon, type IconName } from "@/components/Icon";

const FEATURES: { icon: IconName; title: string; text: string }[] = [
  {
    icon: "clock",
    title: "See what’s open",
    text: "Hours for every dining location, with what’s open right now and when the rest open again.",
  },
  {
    icon: "utensils",
    title: "Eat for your diet",
    text: "Set allergies and preferences like vegetarian, halal or a protein goal, and see which items fit.",
  },
  {
    icon: "users",
    title: "Eat as a group",
    text: "Add everyone’s diets and find a location where each person has something to eat.",
  },
  {
    icon: "compare",
    title: "Compare meals",
    text: "Rank meals across campus by a goal like high protein or under 600 calories.",
  },
  {
    icon: "chat",
    title: "Chat with friends",
    text: "Make a room, invite friends who are open to chat, and plan where to meet.",
  },
  {
    icon: "bot",
    title: "Ask the assistant",
    text: "Plain-word questions about menus, hours and crowds, answered only from PackPlate’s data.",
  },
];

// Welcome page. "About PackPlate" in the header comes back here.
export default function WelcomePage() {
  return (
    <main className="page page-home">
      <section className="home-hero" aria-labelledby="welcome-title">
        <p className="eyebrow">About</p>
        <h1 id="welcome-title">
          Welcome to Pack<span>Plate</span>
        </h1>
        <p className="home-hero-lede">
          PackPlate helps NC State students decide where to eat on campus. It
          puts dining hours, menus and nutrition for every campus dining
          location in one place, and filters the menus for your allergies and
          diet.
        </p>
        <div className="button-row">
          <Link href="/home" className="btn btn-light">
            Get started <Icon name="arrow" size={18} />
          </Link>
        </div>
      </section>

      <section aria-labelledby="about-title" className="home-section">
        <h2 id="about-title" className="section-title">
          What you can do
        </h2>
        <div className="about-grid">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="about-card">
              <span className="about-icon" aria-hidden="true">
                <Icon name={feature.icon} size={22} />
              </span>
              <h3>{feature.title}</h3>
              <p>{feature.text}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
