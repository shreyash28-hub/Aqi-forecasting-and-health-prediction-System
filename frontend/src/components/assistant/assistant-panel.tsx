"use client";

import { Fragment, useEffect, useRef, useState } from "react";
import { Loader2, Send, TriangleAlert } from "lucide-react";
import { Panel, PanelTitle } from "@/components/common";
import { ApiError, meApi, type AssistantTurn } from "@/lib/api";
import { cn } from "@/lib/utils";

const SUGGESTIONS = [
  "Is it safe for me to go for a walk tomorrow?",
  "Which day this week has the cleanest air?",
  "Should I wear a mask today?",
  "What should I keep in mind with my condition?",
];
const HISTORY_TURNS = 10;

interface Turn extends AssistantTurn {
  emergency?: boolean;
}

/** Chat with the air-quality assistant (Claude, grounded in the site's forecast and the user's
 *  saved profile). The conversation lives in this component only; the server stores nothing. */
export function AssistantPanel({ token, city }: { token: string; city: string }) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [remaining, setRemaining] = useState<number>();
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [turns, busy]);

  async function send(text: string) {
    const message = text.trim();
    if (!message || busy) return;
    const history = turns.slice(-HISTORY_TURNS).map(({ role, content }) => ({ role, content }));
    setTurns((t) => [...t, { role: "user", content: message }]);
    setDraft("");
    setBusy(true);
    setError(undefined);
    try {
      const res = await meApi(token).ask({ message, history, city });
      setTurns((t) => [...t, { role: "assistant", content: res.reply, emergency: res.emergency }]);
      setRemaining(res.remaining_today);
    } catch (e) {
      setTurns((t) => t.slice(0, -1));   // let the user resend the same question
      setDraft(message);
      setError(e instanceof ApiError && e.status === 429 ? e.message : `The assistant couldn't answer: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Panel delay={0.1} className="col-span-12 mt-4 flex flex-col">
      <PanelTitle sub="answers from your forecast and saved profile"
        action={remaining !== undefined && <span className="text-xs text-faint">{remaining} questions left today</span>}>
        Ask about your air
      </PanelTitle>

      <div className="mt-4 max-h-[460px] min-h-[120px] space-y-4 overflow-y-auto pr-1" aria-live="polite">
        {turns.length === 0 && (
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => send(s)} disabled={busy}
                className="rounded-[7px] border border-border-strong bg-card px-3 py-1.5 text-left text-[13px] text-muted-foreground hover:border-brand hover:text-foreground">
                {s}
              </button>
            ))}
          </div>
        )}
        {turns.map((t, i) => t.role === "user" ? (
          <p key={i} className="ml-auto w-fit max-w-[80%] rounded-[10px] bg-muted px-3.5 py-2 text-sm">{t.content}</p>
        ) : (
          <div key={i} className={cn("max-w-[88%] text-sm leading-relaxed",
            t.emergency && "rounded-[10px] border border-destructive/40 bg-destructive/5 px-3.5 py-2.5")}>
            {t.emergency && <p className="mb-1.5 flex items-center gap-1.5 font-semibold text-destructive"><TriangleAlert className="size-4" aria-hidden />Get help now</p>}
            <RichText text={t.content} />
          </div>
        ))}
        {busy && <p className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="size-4 animate-spin" aria-hidden />Checking the forecast…</p>}
        <div ref={endRef} />
      </div>

      {error && <p className="mt-3 rounded-[7px] bg-destructive/10 px-3 py-2 text-[13px] text-destructive" role="alert">{error}</p>}

      <form className="mt-4 flex items-end gap-2" onSubmit={(e) => { e.preventDefault(); send(draft); }}>
        <label htmlFor="assistant-input" className="sr-only">Your question</label>
        <textarea id="assistant-input" value={draft} onChange={(e) => setDraft(e.target.value)} rows={1} maxLength={1000}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(draft); } }}
          placeholder="Ask about the air, your risk or precautions (English or Hindi)"
          className="min-h-9 flex-1 resize-none rounded-[7px] border border-border-strong bg-card px-3 py-2 text-sm outline-none focus:border-brand" />
        <button type="submit" disabled={busy || !draft.trim()} aria-label="Send"
          className="flex size-9 shrink-0 items-center justify-center rounded-[7px] bg-brand text-white disabled:opacity-40">
          <Send className="size-4" aria-hidden />
        </button>
      </form>
      <p className="mt-2.5 text-xs text-faint">
        General guidance for decision support, not medical advice. In an emergency call 112 (or 108 for an ambulance).
        Your question and the profile details needed to answer it are sent to our AI provider (Anthropic) to write the reply; Airware doesn&apos;t store the conversation.
      </p>
    </Panel>
  );
}

const LIST_ITEM = /^\s*([-*]|\d+\.)\s+/;

/** Paragraphs, "- " or "1." lists and **bold**: the formatting the assistant uses. */
function RichText({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/);
  return (
    <div className="space-y-2">
      {blocks.map((block, i) => {
        const lines = block.split("\n").filter((l) => l.trim());
        const lead = lines.length && !LIST_ITEM.test(lines[0]) ? lines[0] : null;   // "Tips:" before a list
        const items = lead ? lines.slice(1) : lines;
        if (items.length && items.every((l) => LIST_ITEM.test(l))) {
          return (
            <Fragment key={i}>
              {lead && <p><Inline text={lead} /></p>}
              <ul className="list-disc space-y-1 pl-5">
                {items.map((l, j) => <li key={j}><Inline text={l.replace(LIST_ITEM, "")} /></li>)}
              </ul>
            </Fragment>
          );
        }
        return <p key={i}>{lines.map((l, j) => <Fragment key={j}>{j > 0 && <br />}<Inline text={l} /></Fragment>)}</p>;
      })}
    </div>
  );
}

function Inline({ text }: { text: string }) {
  return <>{text.split(/(\*\*[^*]+\*\*)/).map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong> : part)}</>;
}
