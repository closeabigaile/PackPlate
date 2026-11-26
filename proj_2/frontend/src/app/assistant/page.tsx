import { PageShell } from "@/components/PageShell";
import { AssistantPanel } from "./AssistantPanel";

// This is the /assistant page. AssistantPanel checks who's signed in and shows their chat.
export default function AssistantPage() {
  return (
    <PageShell
      title="Dining assistant"
      icon="bot"
      lede="Ask about menus, hours, and how busy a dining hall is. Answers use your saved diet."
      showFreshness={false}
    >
      <AssistantPanel />
    </PageShell>
  );
}
