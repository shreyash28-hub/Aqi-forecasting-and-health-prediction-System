"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brand } from "./brand";
import { ThemeToggle } from "./theme-toggle";
import { CitySelect } from "./city-select";
import { UserMenu } from "./user-menu";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Overview" },
  { href: "/forecast", label: "Forecast" },
  { href: "/risk", label: "My risk" },
  { href: "/history", label: "History" },
  { href: "/models", label: "Models" },
];

/** Header for the product pages: nav, city selector, theme toggle, sign in. */
export function AppHeader({ city, onCityChange }: { city?: string; onCityChange?: (c: string) => void }) {
  const path = usePathname();
  return (
    <header className="sticky top-0 z-30 border-b bg-card">
      <div className="shell flex h-[58px] items-center gap-9">
        <Brand href="/" />
        <nav aria-label="Main" className="flex h-full gap-1">
          {NAV.map((n) => {
            const active = path === n.href || path.startsWith(`${n.href}/`);
            return (
              <Link
                key={n.href}
                href={n.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center border-b-2 px-3 text-sm font-medium transition-colors",
                  active ? "border-brand text-foreground" : "border-transparent text-muted-foreground hover:text-foreground",
                )}
              >
                {n.label}
              </Link>
            );
          })}
        </nav>
        <div className="ml-auto flex items-center gap-2.5">
          {city && onCityChange && <CitySelect city={city} onChange={onCityChange} />}
          <ThemeToggle />
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
