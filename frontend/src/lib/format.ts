const parse = (iso: string) => new Date(`${iso.slice(0, 10)}T00:00:00`);

/** "Thu 2 Jul" */
export const fmtDay = (iso: string) =>
  parse(iso).toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" });

/** "Thu" */
export const fmtWeekday = (iso: string) => parse(iso).toLocaleDateString("en-GB", { weekday: "short" });

/** "2 Jul" */
export const fmtDayMonth = (iso: string) => parse(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" });

/** "1 Jul 2020" */
export const fmtDate = (iso: string) =>
  parse(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });

export const round = (v: number | null | undefined) => (v == null ? "–" : Math.round(v).toString());
