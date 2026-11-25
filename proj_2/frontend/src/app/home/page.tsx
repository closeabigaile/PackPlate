import Link from "next/link";
import { FeatureCard } from "@/components/FeatureCard";
import { Icon } from "@/components/Icon";
import { OpenNowStrip } from "@/components/OpenNowStrip";

// Home: a hero with the two most common starting points, then every feature,
// grouped by what you're trying to do.
export default function HomePage() {
  return (
    <main className="page page-home">
      <section className="home-hero" aria-labelledby="home-title">
        <p className="eyebrow">NC State dining, in one place</p>
        <h1 id="home-title">Where are you eating today?</h1>
        <p className="home-hero-lede">
          Hours, menus and nutrition for every campus dining location, checked
          against your diet, or everyone’s.
        </p>
        <div className="button-row">
          <Link href="/locations" className="btn btn-light">
            <Icon name="clock" size={18} /> See what’s open
          </Link>
          <Link href="/assistant" className="btn btn-ghost-light">
            <Icon name="bot" size={18} /> Ask the assistant
          </Link>
        </div>
        <OpenNowStrip />
      </section>

      <section aria-labelledby="find-title" className="home-section">
        <h2 id="find-title" className="section-title">
          Find something to eat
        </h2>
        <ul className="cards">
          <li>
            <FeatureCard
              href="/locations"
              title="What’s open now"
              description="Every location’s hours, and when the closed ones open again."
              icon="clock"
              accent="var(--green)"
            />
          </li>
          <li>
            <FeatureCard
              href="/menus"
              title="Menus and nutrition"
              description="Today’s menus with allergens, diets and nutrition facts."
              icon="utensils"
              accent="var(--purple)"
            />
          </li>
          <li>
            <FeatureCard
              href="/compare"
              title="Compare meals"
              description="Find high-protein or low-calorie meals across campus."
              icon="compare"
              accent="var(--teal)"
              tag="New"
            />
          </li>
          <li>
            <FeatureCard
              href="/busy"
              title="How busy is it?"
              description="Live crowd reports from students, plus a forecast."
              icon="activity"
              accent="var(--amber)"
            />
          </li>
        </ul>
      </section>

      <section aria-labelledby="together-title" className="home-section">
        <h2 id="together-title" className="section-title">
          Plan with friends
        </h2>
        <ul className="cards">
          <li>
            <FeatureCard
              href="/group"
              title="Eat as a group"
              description="Add everyone’s diets and find a place where all of you can eat."
              icon="users"
              accent="var(--teal)"
            />
          </li>
          <li>
            <FeatureCard
              href="/chat"
              title="Group chat"
              description="Make a room, invite friends and pick where to meet."
              icon="chat"
              accent="var(--red)"
              tag="New"
            />
          </li>
          <li>
            <FeatureCard
              href="/assistant"
              title="Dining assistant"
              description="Ask in plain words: what’s for dinner, what fits my diet."
              icon="bot"
              accent="var(--purple)"
              tag="New"
            />
          </li>
          <li>
            <FeatureCard
              href="/profile"
              title="My diet"
              description="Save your allergies and preferences once, use them everywhere."
              icon="user"
              accent="var(--green)"
            />
          </li>
        </ul>
      </section>
    </main>
  );
}
