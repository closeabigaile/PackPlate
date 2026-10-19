import Link from "next/link";
import { AuthForm } from "@/components/AuthForm";
import { PageShell } from "@/components/PageShell";

export default function SignupPage() {
  return (
    <PageShell title="Sign up" showFreshness={false}>
      <AuthForm mode="signup" />
      <p className="auth-switch">
        Already have an account? <Link href="/login">Log in</Link>
      </p>
    </PageShell>
  );
}
