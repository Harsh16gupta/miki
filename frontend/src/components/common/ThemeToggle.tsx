import { Moon, Sun } from "lucide-react";
import { cn } from "../../lib/cn";
import type { Theme } from "../../hooks/useTheme";

/** Mono LIGHT/DARK toggle for the Navbar utility cluster. */
export default function ThemeToggle({
  theme,
  onToggle,
}: {
  theme: Theme;
  onToggle: () => void;
}) {
  const light = theme === "light";
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={light}
      aria-label={light ? "Switch to dark mode" : "Switch to light mode"}
      title={light ? "Switch to dark mode" : "Switch to light mode"}
      className={cn(
        "flex items-center gap-1.5 rounded-none px-2 py-1 font-mono text-xs uppercase tracking-[0.14em] transition-colors duration-150 ease-out focus-ring",
        "text-[#8FA3A0] hover:text-[#83DDDA]",
      )}
    >
      {light ? <Moon size={13} /> : <Sun size={13} />}
      <span className="hidden sm:inline">{light ? "Dark" : "Light"}</span>
    </button>
  );
}
