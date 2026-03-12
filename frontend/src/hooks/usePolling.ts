import { useEffect, useRef, useCallback } from 'react';

interface UsePollingOptions {
  /** Callback to execute on each interval */
  callback: () => void | Promise<void>;
  /** Polling interval in milliseconds (default: 5000) */
  interval?: number;
  /** Whether polling is currently enabled (default: true) */
  enabled?: boolean;
}

/**
 * Generic polling hook that repeatedly calls a callback at a given interval.
 *
 * The callback is stable-referenced so changes to it don't reset the timer.
 * Polling starts immediately on mount (or when enabled becomes true) and
 * pauses when enabled is false.
 */
export function usePolling({
  callback,
  interval = 5000,
  enabled = true,
}: UsePollingOptions): void {
  const savedCallback = useRef(callback);

  // Update the stored callback reference whenever it changes.
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  const tick = useCallback(async () => {
    try {
      await savedCallback.current();
    } catch {
      // Swallow errors — callers should handle their own errors inside callback.
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;

    // Invoke immediately, then start interval.
    tick();

    const id = setInterval(tick, interval);
    return () => clearInterval(id);
  }, [enabled, interval, tick]);
}

export default usePolling;
