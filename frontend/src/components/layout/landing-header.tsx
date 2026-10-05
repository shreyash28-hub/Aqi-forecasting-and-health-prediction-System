import Link from "next/link";
import { Brand } from "./brand";
import { ThemeToggle } from "./theme-toggle";

const LINKS = [
  { href: "#how", label: "How it works" },
  { href: "#features", label: "Features" },
  { href: "#models", label: "Models" },
  { href: "#data", label: "Data" },
  { href: "#faq", label: "FAQ" },
];

export function LandingHeader() {
  return (
    <header className="sticky top-0 z-30 border-b bg-background/90 backdrop-blur">
      <div className="shell flex h-[62px] items-center gap-9">
        <Brand />
        <nav aria-label="Sections" className="flex gap-6">
          {LINKS.map((l) => (
            <a key={l.href} href={l.href} className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
              {l.label}
            </a>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2.5">
          <ThemeToggle />
          <Link href="/sign-in" className="flex h-9 items-center rounded-[7px] border border-border-strong bg-card px-4 text-sm font-medium hover:bg-muted">
            Sign in
          </Link>
          <Link href="/dashboard" className="flex h-9 items-center rounded-[7px] bg-brand px-4 text-sm font-medium text-on-brand hover:brightness-110">
            Open dashboard
          </Link>
        </div>
      </div>
    </header>
  );
}
