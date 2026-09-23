import { Fragment } from "react";
import { Link } from "react-router-dom";

export interface Crumb {
  label: string;
  to?: string;
}

/** Mono breadcrumb trail, e.g. HOME / INTERVIEW / SETUP. */
export default function Breadcrumb({ trail }: { trail: Crumb[] }) {
  return (
    <nav aria-label="Breadcrumb">
      <ol className="flex flex-wrap items-center gap-2 font-mono text-xs uppercase tracking-[0.18em] text-[#8FA3A0]">
        {trail.map((c, i) => (
          <Fragment key={c.label}>
            {i > 0 && (
              <span aria-hidden="true" className="text-[#8FA3A0]/60">
                /
              </span>
            )}
            <li>
              {c.to ? (
                <Link
                  to={c.to}
                  className="rounded-none transition-colors duration-150 ease-out hover:text-[#83DDDA] focus-ring"
                >
                  {c.label}
                </Link>
              ) : (
                <span aria-current="page" className="text-[#83DDDA]">
                  {c.label}
                </span>
              )}
            </li>
          </Fragment>
        ))}
      </ol>
    </nav>
  );
}
