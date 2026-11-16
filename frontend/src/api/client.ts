/**
 * Typed fetch wrapper for the Sprintline API.
 *
 * The browser talks to relative `/api/...` paths only: the Vite dev server
 * proxies them to the FastAPI backend, so there is one origin in development
 * and no CORS friction. The session token is kept in localStorage so a hard
 * reload of any gated route stays authenticated.
 */

const TOKEN_KEY = 'sprintline.token';
export const UNAUTHORIZED_EVENT = 'sprintline:unauthorized';

export interface ApiErrorPayload {
  error?: { code?: string; message?: string; fields?: Record<string, string> };
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fields: Record<string, string>;

  constructor(status: number, code: string, message: string, fields: Record<string, string> = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

export function getToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) {
      window.localStorage.setItem(TOKEN_KEY, token);
    } else {
      window.localStorage.removeItem(TOKEN_KEY);
    }
  } catch {
    /* storage can be unavailable in private modes — the in-memory session still works */
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
  auth?: boolean;
  suppressAuthEvent?: boolean;
}

const STATUS_MESSAGES: Record<number, string> = {
  400: 'That request could not be processed.',
  401: 'Your session expired. Please sign in again.',
  403: 'You do not have access to that.',
  404: 'Not found.',
  422: 'Please check the highlighted fields.',
  429: 'Too many attempts. Please wait a moment.',
  500: 'Something went wrong on our side.',
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }
  const token = getToken();
  if (token && options.auth !== false) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(path, {
      method: options.method ?? 'GET',
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  } catch {
    throw new ApiError(
      0,
      'network_error',
      'Cannot reach the Sprintline API. Is the backend running on port 8000?',
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    const body = payload as ApiErrorPayload | null;
    const status = response.status;
    if (status === 401 && options.auth !== false && !options.suppressAuthEvent) {
      setToken(null);
      window.dispatchEvent(new CustomEvent(UNAUTHORIZED_EVENT));
    }
    throw new ApiError(
      status,
      body?.error?.code ?? 'error',
      body?.error?.message ?? STATUS_MESSAGES[status] ?? 'Request failed.',
      body?.error?.fields ?? {},
    );
  }

  return payload as T;
}

export const api = {
  get: <T>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'POST', body }),
  patch: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'PATCH', body }),
  del: <T>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'DELETE' }),
};
