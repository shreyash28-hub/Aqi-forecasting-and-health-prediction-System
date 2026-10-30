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

/** "Today" / "Tomorrow" for those dates (in the viewer's time zone), otherwise "Thu 2 Jul". */
export const relDay = (iso: string) => {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const days = Math.round((parse(iso).getTime() - today.getTime()) / 86_400_000);
  return days === 0 ? "Today" : days === 1 ? "Tomorrow" : fmtDay(iso);
};
