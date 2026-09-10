import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="flex flex-col items-center justify-between gap-2 border-t border-white/[0.08] pb-4 pt-4 text-[11px] text-zinc-500 sm:flex-row">
      <p>
        Miki · open-source evidence-grounded interview trainer · your uploads
        stay in this backend
      </p>
      <div className="flex items-center gap-3">
        <span title="Composer shortcuts">Enter to send · Shift+Enter for newline</span>
        <a
          href="https://github.com"
          target="_blank"
          rel="noreferrer"
          className="rounded transition-colors hover:text-zinc-300 focus-ring"
        >
          GitHub
        </a>
        <Link
          to="/setup"
          className="rounded transition-colors hover:text-zinc-300 focus-ring"
        >
          Privacy: local-only
        </Link>
      </div>
    </footer>
  );
}
