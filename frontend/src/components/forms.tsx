"use client";

import { cn } from "@/lib/utils";

/** Shared form controls in the Airware style (native elements, so they work with autofill and screen readers). */

export function Field({ label, hint, error, htmlFor, children, className }: {
  label: string; hint?: React.ReactNode; error?: string; htmlFor?: string; children: React.ReactNode; className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <label htmlFor={htmlFor} className="text-sm font-medium">{label}</label>
      {children}
      {error ? <p className="text-[13px] text-destructive" role="alert">{error}</p> : hint ? <p className="text-[13px] text-faint">{hint}</p> : null}
    </div>
  );
}

export const inputClass =
  "h-10 w-full rounded-[7px] border border-border-strong bg-card px-3 text-sm outline-none transition-colors placeholder:text-faint focus-visible:border-brand focus-visible:ring-2 focus-visible:ring-brand/25 aria-invalid:border-destructive";

/** Row of mutually exclusive options (radio group styled as buttons). */
export function ChoiceGroup<T extends string>({ name, value, options, onChange, invalid, columns }: {
  name: string; value: T | undefined; options: { value: T; label: string; hint?: string }[];
  onChange: (v: T) => void; invalid?: boolean; columns?: number;
}) {
  return (
    <div role="radiogroup" aria-label={name} aria-invalid={invalid || undefined}
      className="grid gap-2" style={{ gridTemplateColumns: `repeat(${columns ?? options.length}, minmax(0, 1fr))` }}>
      {options.map((o) => {
        const on = value === o.value;
        return (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={on}
            onClick={() => onChange(o.value)}
            className={cn(
              "rounded-[7px] border px-3 py-2 text-left text-sm transition-colors",
              on ? "border-brand bg-brand-soft font-medium text-brand-ink shadow-[inset_0_0_0_1px_var(--brand)]" : "border-border-strong bg-card hover:bg-muted",
              invalid && !value && "border-destructive",
            )}
          >
            {o.label}
            {o.hint && <span className={cn("block text-xs", on ? "text-brand-ink/80" : "text-faint")}>{o.hint}</span>}
          </button>
        );
      })}
    </div>
  );
}

export function PrimaryButton({ className, ...props }: React.ComponentProps<"button">) {
  return (
    <button
      className={cn("inline-flex h-10 items-center justify-center gap-2 rounded-[7px] bg-brand px-5 text-sm font-medium text-on-brand transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60", className)}
      {...props}
    />
  );
}

export function SecondaryButton({ className, ...props }: React.ComponentProps<"button">) {
  return (
    <button
      className={cn("inline-flex h-10 items-center justify-center gap-2 rounded-[7px] border border-border-strong bg-card px-4 text-sm font-medium transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-60", className)}
      {...props}
    />
  );
}
