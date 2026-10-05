import Link from "next/link";
import { Brand } from "./brand";
import { DISCLAIMER } from "@/lib/content";

/** Full footer for the landing page. */
export function SiteFooter() {
  const cols = [
    { title: "Product", links: [["/dashboard", "Dashboard"], ["/risk", "My risk"], ["/history", "History"], ["/models", "Models"]] },
    { title: "Learn", links: [["/#how", "How it works"], ["/#data", "Data and methodology"], ["/#faq", "FAQ"]] },
    { title: "Account", links: [["/sign-in", "Sign in"], ["/sign-in?mode=sign-up", "Create account"]] },
  ];
  return (
    <footer className="border-t py-12">
      <div className="shell">
        <div className="grid grid-cols-[2fr_1fr_1fr_1fr] gap-10">
          <div>
            <Brand />
            <p className="mt-3 max-w-sm text-sm text-muted-foreground">Air-quality forecasts and personal health-risk estimates for Indian cities.</p>
          </div>
          {cols.map((c) => (
            <div key={c.title}>
              <h4 className="mb-3 text-[13px] font-semibold">{c.title}</h4>
              {c.links.map(([href, label]) => (
                <Link key={href} href={href} className="block py-1 text-sm text-muted-foreground hover:text-foreground">{label}</Link>
              ))}
            </div>
          ))}
        </div>
        <div className="mt-10 flex justify-between gap-6 border-t pt-5 text-[13px] text-faint">
          <span>© 2026 Airware</span>
          <span>{DISCLAIMER}</span>
        </div>
      </div>
    </footer>
  );
}

/** Slim footer for product pages. */
export function AppFooter() {
  return (
    <footer className="shell flex justify-between gap-5 py-8 text-[12.5px] text-faint">
      <span>Airware · Forecasts from CPCB monitoring data</span>
      <span>{DISCLAIMER}</span>
    </footer>
  );
}
