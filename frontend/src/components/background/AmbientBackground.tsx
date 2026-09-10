/** Neutral obsidian canvas. No decorative orbs or gradients (DESIGN.md §6.4). */
export default function AmbientBackground() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 bg-[#09090b]"
    />
  );
}
