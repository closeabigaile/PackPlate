import { FeatureCard } from "@/components/FeatureCard";
import { PageShell } from "@/components/PageShell";

// Home: the five features from the wireframe.
export default function HomePage() {
  return (
    <PageShell
      title="Where do you want to start?"
      lede="Everything about eating on campus, in one place."
      showFreshness={false}
    >
      <ul className="cards">
        <li>
          <FeatureCard
            href="/group"
            title="Eat as a Group"
            action="Find a Match"
            accent="var(--teal)"
            art="👥"
          />
        </li>
        <li>
          <FeatureCard
            href="/locations"
            title="What’s Open Now"
            action="See Locations"
            accent="var(--green)"
            art="🕒"
          />
        </li>
        <li>
          <FeatureCard
            href="/menus"
            title="Menus + Nutrition"
            action="View Menus"
            accent="var(--purple)"
            art="🥗"
          />
        </li>
        <li>
          <FeatureCard
            href="/profile"
            title="My Dietary Profile"
            action="Set My Diet"
            accent="var(--amber)"
            art="👤"
          />
        </li>
        <li>
          <FeatureCard
            href="/busy"
            title="How Busy Is It?"
            action="Report Crowds"
            accent="#2b2b30"
            art="📊"
          />
        </li>
      </ul>
    </PageShell>
  );
}
