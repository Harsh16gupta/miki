import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import AuthLayout from "../components/auth/AuthLayout";
import { Button, Input } from "../components/common/Primitives";
import { useAuth } from "../app/useAuth";

function isEmail(v: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim());
}

/** T33: email + password form with inline validation (no OAuth, no recovery). */
export default function LoginPage() {
  const { login, status } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/setup";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const next: typeof errors = {};
    if (!isEmail(email)) next.email = "Enter a valid email address.";
    if (!password) next.password = "Enter your password.";
    setErrors(next);
    if (Object.keys(next).length > 0) return;
    setBusy(true);
    setServerError(null);
    try {
      await login(email.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      setServerError(err instanceof Error ? err.message : "Sign-in failed.");
    } finally {
      setBusy(false);
    }
  };

  if (status === "authed") {
    return (
      <AuthLayout title="Already signed in" subtitle="You're good to go.">
        <Button variant="primary" onClick={() => navigate(from, { replace: true })}>
          Continue →
        </Button>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to track sessions across visits. Guest mode still works without an account."
    >
      <form onSubmit={(e) => void submit(e)} noValidate className="space-y-4">
        <Input
          id="login-email"
          label="Email"
          type="email"
          autoComplete="email"
          autoFocus
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={errors.email}
        />
        <div>
          <Input
            id="login-password"
            label="Password"
            type={showPw ? "text" : "password"}
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password}
          />
          <button
            type="button"
            onClick={() => setShowPw((s) => !s)}
            aria-pressed={showPw}
            className="mt-1.5 rounded-none font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0] transition-colors duration-150 ease-out hover:text-[#83DDDA] focus-ring"
          >
            {showPw ? "Hide password" : "Show password"}
          </button>
        </div>
        {serverError && (
          <p role="alert" className="rounded-none border border-red-500/30 bg-red-500/[0.08] px-3 py-2 font-mono text-xs text-[#f87171]">
            {serverError}
          </p>
        )}
        <Button
          variant="primary"
          type="submit"
          disabled={busy}
          className="w-full justify-center py-3"
        >
          {busy ? "Signing in…" : "Sign in →"}
        </Button>
      </form>
      <p className="mt-4 text-center font-serif text-[15px] text-[#8FA3A0]">
        No account?{" "}
        <Link to="/signup" className="rounded-none font-mono text-xs uppercase tracking-[0.14em] text-[#3AA99E] transition-colors duration-150 ease-out hover:text-[#83DDDA] focus-ring">
          Create one →
        </Link>
      </p>
    </AuthLayout>
  );
}
