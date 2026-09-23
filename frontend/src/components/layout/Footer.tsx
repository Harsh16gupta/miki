export default function Footer() {
  return (
    <footer className="border-t border-white/[0.08] py-4">
      <div className="flex items-center gap-4 font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0]">
        <span aria-hidden="true" className="h-px w-8 bg-white/[0.14]" />
        <p className="shrink-0">Turn conversations into confidence</p>
        <span aria-hidden="true" className="h-px flex-1 bg-white/[0.14]" />
        <p className="shrink-0">Built for engineers</p>
      </div>
    </footer>
  );
}
