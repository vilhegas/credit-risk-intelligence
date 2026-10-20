const navigation = [
  { href: "#projeto", label: "O projeto" },
  { href: "#abordagem", label: "Abordagem" },
  { href: "#transparencia", label: "Transparência" },
];

export function SiteHeader() {
  return (
    <header className="border-b border-line bg-white">
      <div className="mx-auto flex max-w-7xl flex-col gap-5 px-6 py-5 sm:px-10 md:flex-row md:items-center md:justify-between lg:px-14">
        <a href="#projeto" className="flex w-fit items-center gap-3" aria-label="Credit Risk Intelligence, início">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-navy text-white" aria-hidden="true">
            <svg width="23" height="23" viewBox="0 0 24 24" fill="none">
              <path d="M5 17V11M12 17V5M19 17V8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              <path d="M4 21H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </span>
          <span className="text-sm font-bold tracking-tight text-navy sm:text-base">
            Credit Risk <span className="font-normal text-muted">Intelligence</span>
          </span>
        </a>
        <nav aria-label="Navegação principal">
          <ul className="flex flex-wrap gap-x-6 gap-y-3 text-sm font-medium text-muted">
            {navigation.map((item) => (
              <li key={item.href}>
                <a className="transition-colors hover:text-navy" href={item.href}>
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  );
}
