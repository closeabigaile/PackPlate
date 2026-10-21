import { PageShell } from "@/components/PageShell";
import { ProfileEditor } from "@/components/ProfileEditor";

// My Dietary Profile: allergies and dietary preferences.
export default function ProfilePage() {
  return (
    <PageShell
      title="My Dietary Profile"
      lede="Add your allergies and dietary preferences, and PackPlate will mark which menu items fit."
      showFreshness={false}
    >
      <ProfileEditor />
    </PageShell>
  );
}
