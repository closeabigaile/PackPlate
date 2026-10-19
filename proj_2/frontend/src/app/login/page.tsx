import Link from "next/link";
import { AuthForm } from "@/components/AuthForm";
import { PageShell } from "@/components/PageShell";

export default function LoginPage() {
  return (
    <PageShell title="Log in" showFreshness={false}>
      <AuthForm mode="login" />
      <p className="auth-switch">
        New to PackPlate? <Link href="/signup">Sign up</Link>
      </p>
    </PageShell>
  );
}
