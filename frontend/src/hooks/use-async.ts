"use client";

import { useCallback, useEffect, useEffectEvent, useState } from "react";

export interface AsyncState<T> {
  data: T | undefined;
  error: Error | undefined;
  loading: boolean;
  retry: () => void;
}

/**
 * Runs `fn` whenever `deps` change (deps must be serialisable, e.g. a city name),
 * cancelling the previous request. Keeps the last data while a new request loads,
 * so views don't flash empty. State only changes when a request settles.
 */
export function useAsync<T>(fn: (signal: AbortSignal) => Promise<T>, deps: unknown[]): AsyncState<T> {
  const [attempt, setAttempt] = useState(0);
  const key = JSON.stringify([...deps, attempt]);
  const [result, setResult] = useState<{ key: string; data?: T; error?: Error }>({ key: "" });
  const run = useEffectEvent(fn);

  useEffect(() => {
    const ctrl = new AbortController();
    run(ctrl.signal)
      .then((data) => { if (!ctrl.signal.aborted) setResult({ key, data }); })
      .catch((error: Error) => {
        if (!ctrl.signal.aborted && error.name !== "AbortError") setResult((prev) => ({ key, data: prev.data, error }));
      });
    return () => ctrl.abort();
  }, [key]);

  const retry = useCallback(() => setAttempt((a) => a + 1), []);
  return {
    data: result.data,
    error: result.key === key ? result.error : undefined,
    loading: result.key !== key,
    retry,
  };
}
