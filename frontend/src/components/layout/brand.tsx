import Link from "next/link";
import { Wind } from "lucide-react";
import { cn } from "@/lib/utils";

export function Brand({ className, href = "/" }: { className?: string; href?: string }) {
  return (
    <Link href={href} className={cn("flex items-center gap-2.5 text-[17px] font-semibold tracking-tight", className)}>
      <span className="grid size-6 place-items-center rounded-[6px] bg-brand text-on-brand">
        <Wind className="size-4" strokeWidth={2.2} aria-hidden />
      </span>
      Airware
    </Link>
  );
}
