import { AccountPanel } from "@/components/AccountPanel";
import { PageShell } from "@/components/PageShell";

export default function AccountPage() {
  return (
    <PageShell title="My account" icon="user" showFreshness={false}>
      <AccountPanel />
    </PageShell>
  );
}
