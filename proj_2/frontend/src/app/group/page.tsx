import { GroupBuilder } from "@/components/GroupBuilder";
import { PageShell } from "@/components/PageShell";

// Eat as a Group: several people's diets checked against every location.
// Backed by POST /filters/group.
export default function GroupPage() {
  return (
    <PageShell
      title="Eat as a Group"
      lede="Add everyone’s allergies and diets. PackPlate finds a location where each person has something to eat."
    >
      <GroupBuilder />
    </PageShell>
  );
}
