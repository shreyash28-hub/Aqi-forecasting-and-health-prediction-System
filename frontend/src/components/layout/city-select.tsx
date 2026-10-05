"use client";

import { Check, ChevronDown, MapPin } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { CITIES } from "@/lib/content";

export function CitySelect({ city, onChange }: { city: string; onChange: (city: string) => void }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        aria-label="Select city"
        className="flex h-9 min-w-40 items-center justify-between gap-2 rounded-[7px] border border-border-strong bg-card px-3 text-sm font-medium hover:bg-muted"
      >
        <span className="flex items-center gap-2"><MapPin className="size-4 text-muted-foreground" aria-hidden />{city}</span>
        <ChevronDown className="size-4 text-muted-foreground" aria-hidden />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-44">
        {CITIES.map((c) => (
          <DropdownMenuItem key={c} onClick={() => onChange(c)} className="justify-between">
            {c}
            {c === city && <Check className="size-4 text-brand" aria-hidden />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
