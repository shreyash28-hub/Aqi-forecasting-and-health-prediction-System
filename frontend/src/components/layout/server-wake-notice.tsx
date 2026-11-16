"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { onApiSlow } from "@/lib/api";

/**
 * Shown while an API request is unusually slow. The API's free hosting plan sleeps after
 * 15 idle minutes and needs up to a minute to start, so a first visit can otherwise look broken.
 */
export function ServerWakeNotice() {
  const [slow, setSlow] = useState(false);
  useEffect(() => onApiSlow(setSlow), []);
  if (!slow) return null;
  return (
    <div role="status" aria-live="polite"
      className="fixed inset-x-4 bottom-4 z-50 mx-auto flex max-w-[560px] items-start gap-3 rounded-[10px] border bg-card px-4 py-3 text-sm shadow-lg">
      <Loader2 className="mt-0.5 size-4 shrink-0 animate-spin text-primary" aria-hidden />
      <span>
        <span className="font-medium">Starting the forecast service…</span>{" "}
        <span className="text-muted-foreground">It sleeps when nobody has used it for a while and can take up to a minute to start. The page will fill in by itself.</span>
      </span>
    </div>
  );
}
