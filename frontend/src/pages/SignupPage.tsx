import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../components/auth/AuthLayout";
import { Button, Input } from "../components/common/Primitives";
import { useAuth } from "../app/useAuth";
import { passwordStrength, strengthBarColors } from "../lib/passwordStrength";

function isEmail(v: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim());
}

/** T36a/T37/T38: registration with strength meter + terms checkbox. */
export default function SignupPage() {
  const { register, status } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [terms, setTerms] = useState(false);
  const [errors, setErrors] = useState<{
    name?: string;
    email?: string;
    password?: string;
    terms?: string;
  }>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const strength = passwordStrength(password);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const next: typeof errors = {};
    if (!name.trim()) next.name = "Enter your name.";
    if (!isEmail(email)) next.email = "Enter a valid email address.";
    if (password.length < 8) next.password = "At least 8 characters.";
    if (!terms) next.terms = "Please accept the Terms and Privacy Policy.";
    setErrors(next);
    if (Object.keys(next).length > 0) return;
    setBusy(true);
    setServerError(null);
    try {
      await register(name.trim(), email.trim(), password);
      navigate("/setup", { replace: true });
    } catch (err) {
      setServerError(err instanceof Error ? err.message : "Sign-up failed.");
    } finally {
      setBusy(false);
    }
  };

  if (status === "authed") {
    return (
      <AuthLayout title="Already signed in" subtitle="You're good to go.">
        <Button variant="primary" onClick={() => navigate("/setup", { replace: true })}>
          Go to Setup
        </Button>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Track interview history across visits. Guest mode still works without an account."
    >
      <form onSubmit={(e) => void submit(e)} noValidate className="space-y-4">
        <Input
          id="signup-name"
          label="Full name"
          type="text"
          autoComplete="name"
          autoFocus
          placeholder="Ada Lovelace"
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={errors.name}
        />
        <Input
          id="signup-email"
          label="Email"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={errors.email}
        />
        <div>
          <Input
            id="signup-password"
            label="Password"
            type={showPw ? "text" : "password"}
            autoComplete="new-password"
            placeholder="At least 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password}
            hint="Use length, numbers, and symbols for a stronger password."
          />
          {password.length > 0 && (
            <div className="mt-2 flex items-center gap-2" aria-live="polite">
              <div className="flex flex-1 gap-1">
                {[0, 1, 2, 3].map((i) => (
                  <span
                    key={i}
                    className={
                      "h-1.5 flex-1 rounded-full " +
                      (i < strength.score
                        ? strengthBarColors[strength.score]
                        : "bg-white/10")
                    }
                  />
                ))}
              </div>
              <span className="text-xs text-zinc-400">{strength.label}</span>
            </div>
          )}
          <button
            type="button"
            onClick={() => setShowPw((s) => !s)}
            aria-pressed={showPw}
            className="mt-1.5 rounded text-xs text-neutral-400 transition-colors hover:text-white focus-ring"
          >
            {showPw ? "Hide password" : "Show password"}
          </button>
        </div>
        <div>
          <label className="flex cursor-pointer items-start gap-2.5 rounded-lg p-1 focus-within:outline focus-within:outline-2 focus-within:outline-white/60">
            <input
              type="checkbox"
              checked={terms}
              onChange={(e) => setTerms(e.target.checked)}
              className="mt-0.5 h-4 w-4 shrink-0 cursor-pointer accent-white"
            />
            <span className="text-sm leading-relaxed text-neutral-300">
              I agree to the Terms of Service and Privacy Policy. My uploads
              stay in this backend.
            </span>
          </label>
          {errors.terms && (
            <p role="alert" className="mt-1.5 text-xs text-red-400">
              {errors.terms}
            </p>
          )}
        </div>
        {serverError && (
          <p role="alert" className="rounded-lg border border-red-500/30 bg-red-500/[0.08] px-3 py-2 text-sm text-red-400">
            {serverError}
          </p>
        )}
        <Button
          variant="primary"
          type="submit"
          disabled={busy}
          className="w-full justify-center"
        >
          {busy ? "Creating account…" : "Create Account"}
        </Button>
      </form>
      <p className="mt-4 text-center text-sm text-zinc-500">
        Have an account?{" "}
        <Link to="/login" className="text-cyan-300 hover:text-white focus-ring">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
