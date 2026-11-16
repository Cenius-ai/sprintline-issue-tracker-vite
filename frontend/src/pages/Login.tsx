import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { ApiError } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { useDocumentTitle } from '../hooks/useApi';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function Login() {
  useDocumentTitle('Sign in');
  const { login, status, sessionExpired } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  const requested = (location.state as { from?: string } | null)?.from;
  const redirectTo = requested && requested !== '/login' ? requested : '/';

  useEffect(() => {
    if (status === 'authenticated') {
      navigate(redirectTo, { replace: true });
    }
  }, [status, redirectTo, navigate]);

  async function signIn(nextEmail: string, nextPassword: string) {
    setBusy(true);
    setFormError(null);
    try {
      await login(nextEmail, nextPassword);
      navigate(redirectTo, { replace: true });
    } catch (error) {
      setFormError(
        error instanceof ApiError ? error.message : 'Could not sign in. Please try again.',
      );
    } finally {
      setBusy(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const errors: { email?: string; password?: string } = {};
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      errors.email = 'Enter your email address.';
    } else if (!EMAIL_PATTERN.test(trimmedEmail)) {
      errors.email = 'That does not look like an email address.';
    }
    if (!password) {
      errors.password = 'Enter your password.';
    }
    setFieldErrors(errors);
    if (errors.email) {
      emailRef.current?.focus();
      return;
    }
    if (errors.password) {
      passwordRef.current?.focus();
      return;
    }
    void signIn(trimmedEmail, password);
  }

  function useDemoAccount() {
    setEmail('cenius@cenius.ai');
    setPassword('cenius');
    setFieldErrors({});
    void signIn('cenius@cenius.ai', 'cenius');
  }

  return (
    <div className="login">
      <div className="login__card">
        <span className="login__brand">
          <span className="brand__glyph" aria-hidden="true">
            ◆
          </span>
          Sprintline
        </span>

        <div>
          <h1 className="login__title">Sign in to Sprintline</h1>
          <p className="login__sub">
            Issues, sprint board, burndown and roadmap for the whole team.
          </p>
        </div>

        {sessionExpired ? (
          <div className="banner banner--info" role="status">
            Your session expired. Sign in again to pick up where you left off.
          </div>
        ) : null}

        {formError ? (
          <div className="banner banner--error" role="alert">
            {formError}
          </div>
        ) : null}

        <form className="stack" onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label className="field__label" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              name="email"
              ref={emailRef}
              className="input"
              type="email"
              inputMode="email"
              autoComplete="username"
              autoCapitalize="none"
              spellCheck={false}
              value={email}
              aria-invalid={Boolean(fieldErrors.email)}
              aria-describedby={fieldErrors.email ? 'email-error' : undefined}
              onChange={(event) => setEmail(event.target.value)}
            />
            {fieldErrors.email ? (
              <span className="field__error" id="email-error" role="alert">
                {fieldErrors.email}
              </span>
            ) : null}
          </div>

          <div className="field">
            <label className="field__label" htmlFor="password">
              Password
            </label>
            <div className="password-wrap">
              <input
                id="password"
                name="password"
                ref={passwordRef}
                className="input"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                aria-invalid={Boolean(fieldErrors.password)}
                aria-describedby={fieldErrors.password ? 'password-error' : undefined}
                onChange={(event) => setPassword(event.target.value)}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword((current) => !current)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                aria-pressed={showPassword}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
            {fieldErrors.password ? (
              <span className="field__error" id="password-error" role="alert">
                {fieldErrors.password}
              </span>
            ) : null}
          </div>

          <button type="submit" className="btn btn--primary btn--block" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div className="demo">
          <span className="muted">Demo: cenius@cenius.ai / cenius</span>
          <div className="demo__creds">
            <span>
              Email <code>cenius@cenius.ai</code>
            </span>
            <span>
              Password <code>cenius</code>
            </span>
          </div>
          <button type="button" className="btn btn--ghost btn--sm" onClick={useDemoAccount} disabled={busy}>
            Use demo credentials
          </button>
        </div>
      </div>
    </div>
  );
}
