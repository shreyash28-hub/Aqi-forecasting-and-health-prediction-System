"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Check, Loader2 } from "lucide-react";
import type { Session } from "@supabase/supabase-js";
import { ChoiceGroup, Field, PrimaryButton, SecondaryButton, inputClass } from "@/components/forms";
import { Panel } from "@/components/common";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/common";
import { useAsync } from "@/hooks/use-async";
import { meApi, type Profile, type SavedProfile } from "@/lib/api";
import { CITIES } from "@/lib/content";
import { cn } from "@/lib/utils";

type Draft = Partial<Omit<SavedProfile, "age" | "outdoor_hours" | "bmi" | "exercise_hours">> & {
  age?: string; outdoor_hours?: string; bmi?: string; exercise_hours?: string;
};

const CONDITIONS: { value: Profile["condition"]; label: string }[] = [
  { value: "No Condition", label: "None" }, { value: "Asthma", label: "Asthma" }, { value: "COPD", label: "COPD" },
  { value: "HeartDisease", label: "Heart disease" }, { value: "Diabetes", label: "Diabetes" }, { value: "Hypertension", label: "High blood pressure" },
];
const OCCUPATIONS: { value: Profile["occupation"]; label: string }[] = [
  { value: "Student", label: "Student" }, { value: "Indoor Worker", label: "Indoor work" }, { value: "Outdoor Worker", label: "Outdoor work" },
  { value: "Homemaker", label: "Homemaker" }, { value: "Retired", label: "Retired" },
];
const AREAS: { value: Profile["area_type"]; label: string; hint: string }[] = [
  { value: "Residential", label: "Residential", hint: "Mostly homes" }, { value: "Commercial", label: "Commercial", hint: "Shops, offices, traffic" },
  { value: "Industrial", label: "Industrial", hint: "Factories nearby" },
];
const MASKS: { value: Profile["mask_usage"]; label: string }[] = [
  { value: "No", label: "Rarely or never" }, { value: "Sometimes", label: "Sometimes" }, { value: "Yes", label: "Usually" },
];
const YES_NO = [{ value: "yes", label: "Yes" }, { value: "no", label: "No" }] as const;
const FAMILY = [{ value: "yes", label: "Yes" }, { value: "no", label: "No" }, { value: "unknown", label: "Not sure" }] as const;

// Ranges accepted by the API, and the narrower ranges the model was trained on.
const LIMITS = {
  age: { min: 1, max: 110, train: [1, 95] }, outdoor_hours: { min: 0, max: 24, train: [0.5, 10] },
  bmi: { min: 10, max: 70, train: [14, 45] }, exercise_hours: { min: 0, max: 40, train: [0, 14] },
} as const;

const STEPS = ["About you", "Daily exposure", "Health details"];

function toDraft(p: SavedProfile | null): Draft {
  if (!p) return {};
  const s = (v?: number | null) => (v == null ? "" : String(v));
  return { ...p, age: s(p.age), outdoor_hours: s(p.outdoor_hours), bmi: s(p.bmi), exercise_hours: s(p.exercise_hours) };
}

function numError(key: keyof typeof LIMITS, raw: string | undefined, required: boolean): string | undefined {
  if (!raw?.trim()) return required ? "Required." : undefined;
  const v = Number(raw);
  const { min, max } = LIMITS[key];
  if (!Number.isFinite(v)) return "Enter a number.";
  if (v < min || v > max) return `Enter a value between ${min} and ${max}.`;
  return undefined;
}

function rangeNote(key: keyof typeof LIMITS, raw: string | undefined): string | undefined {
  const v = Number(raw);
  const [lo, hi] = LIMITS[key].train;
  return raw?.trim() && Number.isFinite(v) && (v < lo || v > hi) ? `Outside the range the model learned from (${lo}–${hi}); the estimate will be less reliable.` : undefined;
}

export function ProfileWizard({ session }: { session: Session }) {
  const existing = useAsync((signal) => meApi(session.access_token).profile(signal), [session.user.id]);
  if (existing.error) return <ErrorState message={existing.error.message} onRetry={existing.retry} />;
  if (existing.loading && !existing.data) return <Skeleton className="h-[460px]" />;
  return <WizardForm session={session} initial={existing.data ?? null} />;
}

function WizardForm({ session, initial }: { session: Session; initial: SavedProfile | null }) {
  const router = useRouter();
  const [draft, setDraft] = useState<Draft>(() => toDraft(initial));
  const [step, setStep] = useState(0);
  const [tried, setTried] = useState<Record<number, boolean>>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string>();
  const set = <K extends keyof Draft>(k: K, v: Draft[K]) => setDraft((d) => ({ ...d, [k]: v }));

  const errors: Record<number, Partial<Record<keyof Draft, string>>> = {
    0: {
      age: numError("age", draft.age, true),
      gender: draft.gender ? undefined : "Choose one.",
      condition: draft.condition ? undefined : "Choose one.",
      smoker: draft.smoker == null ? "Choose one." : undefined,
    },
    1: {
      city: draft.city ? undefined : "Choose your city.",
      occupation: draft.occupation ? undefined : "Choose one.",
      area_type: draft.area_type ? undefined : "Choose one.",
      outdoor_hours: numError("outdoor_hours", draft.outdoor_hours, true),
      mask_usage: draft.mask_usage ? undefined : "Choose one.",
    },
    2: {
      bmi: numError("bmi", draft.bmi, false),
      exercise_hours: numError("exercise_hours", draft.exercise_hours, false),
    },
  };
  const stepValid = (s: number) => Object.values(errors[s]).every((e) => !e);
  const show = (k: keyof Draft) => (tried[step] ? errors[step][k] : undefined);

  function next() {
    setTried((t) => ({ ...t, [step]: true }));
    if (stepValid(step)) setStep((s) => s + 1);
  }

  async function save() {
    setTried((t) => ({ ...t, 2: true }));
    if (![0, 1, 2].every(stepValid)) return;
    const num = (v?: string) => (v?.trim() ? Number(v) : null);
    const body: SavedProfile = {
      age: Number(draft.age), gender: draft.gender!, condition: draft.condition!, smoker: draft.smoker!,
      occupation: draft.occupation!, area_type: draft.area_type!, mask_usage: draft.mask_usage!,
      outdoor_hours: Number(draft.outdoor_hours), bmi: num(draft.bmi), exercise_hours: num(draft.exercise_hours),
      family_history: draft.family_history ?? null, city: draft.city ?? null,
    };
    setSaving(true);
    setSaveError(undefined);
    try {
      await meApi(session.access_token).saveProfile(body);
      router.push("/risk");
    } catch (e) {
      setSaveError((e as Error).message);
      setSaving(false);
    }
  }

  return (
    <Panel className="p-0 lg:p-0">
      {/* progress */}
      <ol className="flex border-b" aria-label="Profile steps">
        {STEPS.map((label, i) => {
          const done = i < step, current = i === step;
          return (
            <li key={label} className={cn("flex flex-1 items-center gap-3 border-b-2 px-6 py-4", current ? "border-brand" : "border-transparent")}
              aria-current={current ? "step" : undefined}>
              <span className={cn("grid size-7 shrink-0 place-items-center rounded-full text-[13px] font-semibold",
                done ? "bg-brand text-on-brand" : current ? "bg-brand-soft text-brand-ink" : "bg-muted text-faint")}>
                {done ? <Check className="size-4" aria-hidden /> : i + 1}
              </span>
              <span className={cn("text-sm font-medium", !current && !done && "text-muted-foreground")}>{label}</span>
            </li>
          );
        })}
      </ol>

      <div className="p-6 lg:p-8">
        {step === 0 && (
          <div className="grid gap-6">
            <div className="grid gap-6 md:grid-cols-[200px_minmax(0,1fr)]">
              <Field label="Age" htmlFor="age" error={show("age")} hint={rangeNote("age", draft.age) ?? "In years."}>
                <input id="age" inputMode="numeric" type="number" min={1} max={110} value={draft.age ?? ""} onChange={(e) => set("age", e.target.value)}
                  aria-invalid={!!show("age")} className={inputClass} />
              </Field>
              <Field label="Gender" error={show("gender")}>
                <ChoiceGroup name="Gender" value={draft.gender} onChange={(v) => set("gender", v)} invalid={!!show("gender")}
                  options={[{ value: "F", label: "Female" }, { value: "M", label: "Male" }]} />
              </Field>
            </div>
            <Field label="Long-term health condition" error={show("condition")} hint="Choose the one that affects you most.">
              <ChoiceGroup name="Health condition" value={draft.condition} onChange={(v) => set("condition", v)} options={CONDITIONS} columns={3} invalid={!!show("condition")} />
            </Field>
            <div className="grid gap-6 md:grid-cols-2">
              <Field label="Do you smoke?" error={show("smoker")}>
                <ChoiceGroup name="Smoker" value={draft.smoker == null ? undefined : draft.smoker ? "yes" : "no"}
                  onChange={(v) => set("smoker", v === "yes")} options={[...YES_NO]} invalid={!!show("smoker")} />
              </Field>
              <Field label="Family history of lung disease" hint="Optional.">
                <ChoiceGroup name="Family history" value={draft.family_history == null ? (draft.family_history === null ? "unknown" : undefined) : draft.family_history ? "yes" : "no"}
                  onChange={(v) => set("family_history", v === "unknown" ? null : v === "yes")} options={[...FAMILY]} />
              </Field>
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="grid gap-6">
            <Field label="Your city" error={show("city")} hint="Used by default for your risk estimates.">
              <ChoiceGroup name="City" value={draft.city ?? undefined} onChange={(v) => set("city", v)} columns={6} invalid={!!show("city")}
                options={CITIES.map((c) => ({ value: c, label: c }))} />
            </Field>
            <Field label="What do you do most days?" error={show("occupation")}>
              <ChoiceGroup name="Occupation" value={draft.occupation} onChange={(v) => set("occupation", v)} options={OCCUPATIONS} columns={5} invalid={!!show("occupation")} />
            </Field>
            <Field label="Where do you live?" error={show("area_type")}>
              <ChoiceGroup name="Area type" value={draft.area_type} onChange={(v) => set("area_type", v)} options={AREAS} invalid={!!show("area_type")} />
            </Field>
            <div className="grid gap-6 md:grid-cols-[240px_minmax(0,1fr)]">
              <Field label="Hours outdoors per day" htmlFor="outdoor" error={show("outdoor_hours")} hint={rangeNote("outdoor_hours", draft.outdoor_hours) ?? "Including travel."}>
                <input id="outdoor" type="number" inputMode="decimal" step={0.5} min={0} max={24} value={draft.outdoor_hours ?? ""}
                  onChange={(e) => set("outdoor_hours", e.target.value)} aria-invalid={!!show("outdoor_hours")} className={inputClass} />
              </Field>
              <Field label="Do you wear a mask outdoors?" error={show("mask_usage")}>
                <ChoiceGroup name="Mask use" value={draft.mask_usage} onChange={(v) => set("mask_usage", v)} options={MASKS} invalid={!!show("mask_usage")} />
              </Field>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="grid gap-6">
            <p className="text-sm text-muted-foreground">These are optional. Adding them makes your estimate more personal; if you skip them, typical values are used.</p>
            <div className="grid gap-6 md:grid-cols-2">
              <Field label="BMI (body mass index)" htmlFor="bmi" error={show("bmi")} hint={rangeNote("bmi", draft.bmi) ?? "Weight (kg) ÷ height (m)². Typical adult range 18.5–25."}>
                <input id="bmi" type="number" inputMode="decimal" step={0.1} value={draft.bmi ?? ""} onChange={(e) => set("bmi", e.target.value)}
                  aria-invalid={!!show("bmi")} className={inputClass} />
              </Field>
              <Field label="Exercise hours per week" htmlFor="exercise" error={show("exercise_hours")} hint={rangeNote("exercise_hours", draft.exercise_hours)}>
                <input id="exercise" type="number" inputMode="decimal" step={0.5} value={draft.exercise_hours ?? ""} onChange={(e) => set("exercise_hours", e.target.value)}
                  aria-invalid={!!show("exercise_hours")} className={inputClass} />
              </Field>
            </div>
            <Review draft={draft} />
          </div>
        )}

        {saveError && <p className="mt-6 rounded-[7px] bg-destructive/10 px-3 py-2 text-[13px] text-destructive" role="alert">Couldn&apos;t save your profile: {saveError}</p>}

        <div className="mt-8 flex items-center gap-3 border-t pt-6">
          {step > 0 && <SecondaryButton type="button" onClick={() => setStep((s) => s - 1)}>Back</SecondaryButton>}
          <span className="text-[13px] text-faint">Step {step + 1} of {STEPS.length}</span>
          <div className="ml-auto">
            {step < STEPS.length - 1
              ? <PrimaryButton type="button" onClick={next}>Continue</PrimaryButton>
              : <PrimaryButton type="button" onClick={save} disabled={saving}>{saving && <Loader2 className="size-4 animate-spin" aria-hidden />}Save profile</PrimaryButton>}
          </div>
        </div>
      </div>
    </Panel>
  );
}

function Review({ draft }: { draft: Draft }) {
  const label = <T extends string>(list: readonly { value: T; label: string }[], v?: T | null) => list.find((o) => o.value === v)?.label ?? "–";
  const rows: [string, string][] = [
    ["Age", draft.age || "–"], ["Gender", draft.gender === "F" ? "Female" : draft.gender === "M" ? "Male" : "–"],
    ["Condition", label(CONDITIONS, draft.condition)], ["Smoker", draft.smoker == null ? "–" : draft.smoker ? "Yes" : "No"],
    ["City", draft.city || "–"], ["Daily activity", label(OCCUPATIONS, draft.occupation)], ["Area", label(AREAS, draft.area_type)],
    ["Outdoors", draft.outdoor_hours ? `${draft.outdoor_hours} h/day` : "–"], ["Mask", label(MASKS, draft.mask_usage)],
    ["Family history", draft.family_history == null ? "Not given" : draft.family_history ? "Yes" : "No"],
  ];
  return (
    <div className="rounded-[10px] bg-muted p-5">
      <h3 className="text-sm font-semibold">Review</h3>
      <dl className="mt-3 grid grid-cols-2 gap-x-8 gap-y-2 text-sm md:grid-cols-5">
        {rows.map(([k, v]) => (
          <div key={k}><dt className="text-[12.5px] text-faint">{k}</dt><dd className="font-medium">{v}</dd></div>
        ))}
      </dl>
    </div>
  );
}
