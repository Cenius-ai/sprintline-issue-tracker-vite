import { useCallback, useEffect, useRef, useState } from 'react';

import { api, ApiError } from '../api/client';

export interface AsyncResult<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
  reload: () => void;
}

/**
 * Minimal data-fetch hook: one request per path, keeps the previous payload
 * while refetching (no skeleton flash), and exposes `reload` for retries and
 * post-mutation refreshes.
 */
export function useApi<T>(path: string | null): AsyncResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(Boolean(path));
  const [error, setError] = useState<ApiError | null>(null);
  const [version, setVersion] = useState(0);
  const requestId = useRef(0);

  useEffect(() => {
    if (!path) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }
    const id = requestId.current + 1;
    requestId.current = id;
    setLoading(true);
    setError(null);
    api
      .get<T>(path)
      .then((result) => {
        if (requestId.current !== id) return;
        setData(result);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (requestId.current !== id) return;
        setError(err instanceof ApiError ? err : new ApiError(0, 'error', 'Unexpected error.'));
        setLoading(false);
      });
  }, [path, version]);

  const reload = useCallback(() => setVersion((current) => current + 1), []);

  return { data, loading, error, reload };
}

export function useDocumentTitle(title: string): void {
  useEffect(() => {
    document.title = `${title} · Sprintline`;
  }, [title]);
}
