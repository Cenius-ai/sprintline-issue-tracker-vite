# Using Sprintline

Sign in at `/login` with `cenius@cenius.ai` / `cenius` (the credential is printed on the card, and
there is a **Use demo credentials** button that fills it in and signs you in). Everything below
happens in one shared workspace — there are no private projects.

## The workspace overview (`/`)

The landing screen after sign-in. Four tiles count open, in-progress, done and total estimated
points; two bar lists break the same 24 issues down by priority and by assignee (open work only);
the active sprint card shows its goal, how many of its issues are done and which day of the sprint
you are on; the right-hand card lists the eight most recent events across the workspace, each
linking to the issue it happened on. At the bottom, "Assigned to you" lists your own open issues.

## Finding issues (`/issues`)

The list is sorted newest-first and shows key, title, status pill, priority, assignee, label chips
and sprint. Six filters sit above it:

- **Search** — matches title, description and issue key (`SPL-12`). Debounced by 300ms and stored in
  the URL, so a filtered view is shareable.
- **Status / Priority / Assignee / Label / Project** — combinable; *Anyone* and *Unassigned* are
  distinct options on the assignee filter.

Every active filter is echoed under the bar, and **Clear filters** resets all of them. If a filter
combination matches nothing you get "No issues match these filters" with the same reset action; if
the workspace itself is empty you are invited to create the first issue.

## Creating and editing issues

**New issue** (on `/issues`, the overview, or from an empty board column) opens a form with:

- a required title (an inline error and focus move if you submit it blank);
- a free-text description;
- project, sprint (filtered to the project), status, priority, assignee and point estimate — all
  native selects and a number input, so they are keyboard- and screen-reader-friendly;
- labels as checkboxes.

Saving creates the issue, generates its project key (`SPL-18`), clears the filters so the new issue
is visible at the top of the list, and records a `created` event. On the issue detail page **Edit**
opens the same form pre-filled; the title, priority, status and assignee can also be changed inline
from the Fields card — each change saves immediately and appends an activity event.

**Delete** is behind a confirmation dialog that tells you how many comments and activity rows go
with it.

## Working an issue (`/issues/:id`)

- Left column: title, key, status pill, priority, assignee, description, and the Fields card with
  inline editors and metadata (labels, sprint, estimate, created by, completed at).
- Right column: two tabs.
  - **Comments** — oldest first, with author and relative time, plus a composer. The button stays
    disabled until you type something and shows "Posting…" while the request is in flight. New
    comments appear immediately without a page reload.
  - **Activity** — newest first, one line per change ("Diego Marín changed status from In progress
    to Done", "Maya Okafor commented", "reassigned from Priya Raman to Maya Okafor").

A bad id renders a "not found" panel with a link back to the list rather than an error page.

## The sprint board (`/board`)

Pick a sprint from the selector (the active sprint is preselected). The burndown card draws the
sprint's ideal burn as a dashed line and the actual remaining points as a solid line — the actual
line is computed from the persisted completion timestamps of the sprint's issues, so completing an
issue moves it. Below it, five columns (Backlog, Todo, In progress, In review, Done) hold the cards.

To move a card, use its **Move to …** select. The new status is written with
`PATCH /api/issues/{id}` and the board refetches, so the card is still in its new column after a
reload. Empty columns explain themselves and offer **Add issue**, which opens the create form with
that column's status (and the sprint) pre-filled.

## The roadmap (`/roadmap`)

Each project is a row with four lanes:

| Lane      | Contents                                                        |
| --------- | --------------------------------------------------------------- |
| **Now**   | Open issues in the project's active sprint                      |
| **Next**  | Open issues in a planned sprint                                 |
| **Later** | Open issues with no sprint, or left over from a completed sprint|
| **Done**  | Completed issues                                                |

Every lane carries a count badge and its cards (key, title, assignee, priority). Use the **Project**
select to focus a single row. A lane with no work shows what to do about it rather than blank space.

## Keyboard and command palette

- `⌘K` / `Ctrl-K` opens the command palette: type to fuzzy-search pages and issues (by key or
  title), `↑`/`↓` to move, `Enter` to open, `Esc` to close.
- Every control is reachable with Tab, focus is always visible, and the card status control is a
  native select — the board is fully usable without a mouse or a drag gesture.
- **Sign out** in the header clears the stored token and returns to the login screen.

## Session behaviour

The JWT lives in `localStorage`, so reloading any page keeps you signed in; the app restores the
session through `GET /api/auth/me` before rendering a gated route. If a request ever comes back 401
the token is discarded and you land on the login screen with an "your session expired" notice, and
the page you were on is remembered so you return to it after signing in.
