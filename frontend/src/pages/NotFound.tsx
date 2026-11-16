import { Link } from 'react-router-dom';

import { useDocumentTitle } from '../hooks/useApi';

export function NotFound() {
  useDocumentTitle('Not found');
  return (
    <main className="page stack">
      <div className="card">
        <div className="empty">
          <p className="empty__title">That page does not exist</p>
          <p className="empty__text">
            The link may be out of date. Jump back into the workspace from one of these.
          </p>
          <div className="cluster">
            <Link className="btn btn--primary" to="/">
              Overview
            </Link>
            <Link className="btn btn--ghost" to="/issues">
              Issues
            </Link>
            <Link className="btn btn--ghost" to="/board">
              Board
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
