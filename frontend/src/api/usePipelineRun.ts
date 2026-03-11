import { useEffect, useRef, useState } from "react";
import type { PipelineStateSummary } from "./client";
import { getRun } from "./client";

const POLL_INTERVAL_MS = 1500;
const MAX_POLL_MS = 10 * 60 * 1000; // 10 min

export interface UsePipelineRunResult {
  data: PipelineStateSummary | null;
  error: string | null;
  isLoading: boolean;
  isPolling: boolean;
}

/**
 * Fetches run state once; if run is still active, polls until complete or max time.
 */
export function usePipelineRun(runId: string | null): UsePipelineRunResult {
  const [data, setData] = useState<PipelineStateSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(!!runId);
  const [isPolling, setIsPolling] = useState(false);
  const startedAt = useRef<number | null>(null);
  const intervalId = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!runId) {
      setData(null);
      setError(null);
      setIsLoading(false);
      setIsPolling(false);
      if (intervalId.current) {
        clearInterval(intervalId.current);
        intervalId.current = null;
      }
      startedAt.current = null;
      return;
    }

    let cancelled = false;
    startedAt.current = startedAt.current ?? Date.now();

    async function fetchOnce() {
      try {
        const summary = await getRun(runId!);
        if (cancelled) return;
        setData(summary);
        setError(null);
        if (summary.is_running && !summary.has_error) {
          setIsPolling(true);
          if (!intervalId.current) {
            intervalId.current = setInterval(fetchOnce, POLL_INTERVAL_MS);
          }
        } else {
          setIsPolling(false);
          if (intervalId.current) {
            clearInterval(intervalId.current);
            intervalId.current = null;
          }
        }
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : String(e));
        setIsPolling(false);
        if (intervalId.current) {
          clearInterval(intervalId.current);
          intervalId.current = null;
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    setIsLoading(true);
    fetchOnce();

    const timeoutId = setTimeout(() => {
      if (intervalId.current) {
        clearInterval(intervalId.current);
        intervalId.current = null;
      }
      setIsPolling(false);
    }, MAX_POLL_MS);

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
      if (intervalId.current) {
        clearInterval(intervalId.current);
        intervalId.current = null;
      }
    };
  }, [runId]);

  return { data, error, isLoading, isPolling };
}
