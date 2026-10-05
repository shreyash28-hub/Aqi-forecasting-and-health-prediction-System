"use client";

import { motion } from "motion/react";
import { Info, RotateCw, TriangleAlert } from "lucide-react";
import { aqiCategory, chipStyle, scalePosition, AQI_CATEGORIES } from "@/lib/aqi";
import { cn } from "@/lib/utils";

/** Bordered surface used for every dashboard block. */
export function Panel({ className, children, delay = 0, ...rest }: React.ComponentProps<"section"> & { delay?: number }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: "easeOut", delay }}
      className={cn("rounded-[10px] border bg-card p-5 lg:p-[22px]", className)}
      {...(rest as object)}
    >
      {children}
    </motion.section>
  );
}

export function PanelTitle({ children, sub, action }: { children: React.ReactNode; sub?: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2">
      <h2 className="text-sm font-semibold">{children}</h2>
      {sub && <span className="text-sm text-faint">{sub}</span>}
      {action && <div className="ml-auto">{action}</div>}
    </div>
  );
}

/** Fades content up when it scrolls into view (landing page). */
export function Reveal({ children, className, delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.55, ease: "easeOut", delay }}
    >
      {children}
    </motion.div>
  );
}

export function CategoryChip({ aqi, className }: { aqi: number; className?: string }) {
  const cat = aqiCategory(aqi);
  return (
    <span className={cn("inline-flex h-6 items-center rounded-[6px] px-2 text-[12.5px] font-medium", className)} style={chipStyle(cat.color)}>
      {cat.name}
    </span>
  );
}

export function ColorChip({ color, children, className }: { color: string; children: React.ReactNode; className?: string }) {
  return (
    <span className={cn("inline-flex h-6 items-center rounded-[6px] px-2 text-[12.5px] font-medium", className)} style={chipStyle(color)}>
      {children}
    </span>
  );
}

/** CPCB scale of six equal-width bands with a marker placed inside its band. */
export function AqiScale({ aqi }: { aqi: number }) {
  return (
    <div className="mt-5">
      <div className="relative">
        <div className="flex h-2 overflow-hidden rounded-full">
          {AQI_CATEGORIES.map((c) => <i key={c.key} className="flex-1" style={{ background: c.color }} />)}
        </div>
        <div
          className="absolute -top-[5px] h-[18px] w-[3px] rounded-full bg-foreground ring-2 ring-card"
          style={{ left: `calc(${scalePosition(aqi) * 100}% - 1.5px)` }}
          aria-hidden
        />
      </div>
      <div className="num mt-1.5 flex justify-between text-[11.5px] text-faint">
        {[0, 50, 100, 200, 300, 400, 500].map((v) => <span key={v}>{v}</span>)}
      </div>
    </div>
  );
}

export function Disclaimer({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <p className={cn("flex gap-2 text-[12.5px] leading-snug text-faint", className)}>
      <Info className="mt-px size-4 shrink-0" aria-hidden />
      {children}
    </p>
  );
}

export function ErrorState({ message, onRetry, className }: { message?: string; onRetry?: () => void; className?: string }) {
  return (
    <div className={cn("flex flex-col items-start gap-3 rounded-[10px] border border-dashed p-5 text-sm", className)} role="alert">
      <span className="flex items-center gap-2 font-medium"><TriangleAlert className="size-4 text-aqi-poor" aria-hidden />Couldn&apos;t load this data</span>
      <span className="text-muted-foreground">{message ?? "The forecast service didn't respond."} Make sure the API is running, then try again.</span>
      {onRetry && (
        <button onClick={onRetry} className="flex h-8 items-center gap-1.5 rounded-[7px] border border-border-strong px-3 font-medium hover:bg-muted">
          <RotateCw className="size-3.5" aria-hidden />Retry
        </button>
      )}
    </div>
  );
}
