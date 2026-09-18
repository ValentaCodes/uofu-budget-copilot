# UofU Budget Copilot (MVP Kernel)

This repo is the **MVP kernel** for an institutional budget copilot, starting with a single-department, narrow-category, human-in-the-loop flow.

It focuses on:

- A minimal **relational schema** (Postgres) for departments, grants, spend requests, and payments.
- A **request state machine** with safe transitions (DRAFT → SUBMITTED → APPROVED → PAID, etc.).
- **Fiscal and policy constraints** (caps, reserves, per-request limits, grant rules) enforced in code.
- **Concurrency and idempotency** around the `approve` operation.

Higher-level "agents" (Requester, Approver, Payment, Treasury, etc.) will be layered on top of this kernel later via APIs and an event bus.

## High-level idea

Think of this as:

- The **source of truth** for what budgets exist, what requests have been made, and which ones are approved or paid.
- A **workflow engine** that owns the lifecycle of each request.
- A **ledger boundary** where, later, real payment rails (ERP/AP, ACH, AP2/NET Dollar) will plug in.

For now, payments are recorded manually. The goal is to prove the core invariants: no double-spend, caps and reserves enforced, and a clear audit trail of state transitions.

## Data model

Defined in `sql/001_init.sql`. All money is stored as integer cents (`BIGINT`) to avoid floating-point rounding.

- `departments` — budget owners: `code`, `name`, `annual_cap_cents`, `reserve_requirement_cents`
- `grants` — optional funding sources: `code`, `name`
- `spend_requests` — one row per request to spend money: `id` (UUID), `department_id`, `grant_id`, `amount_cents`, `state`, `idempotency_key`, `version`
- `payments` — one row per executed payment (unique per request): `id` (UUID), `request_id`, `executed_at`, `amount_cents`

Request lifecycle is tracked by the `request_state` enum:

DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED → PAID; any active state can go to REJECTED or EXPIRED.

The `spend_requests` table carries two columns to make writes safe once the full state machine lands: `idempotency_key` (deduplicate external calls) and `version` (optimistic concurrency).

## Getting started

### 1. Install dependencies

You'll need Python 3.11+, Postgres running locally, and `psycopg2-binary` (pinned in `requirements.txt`).

    pip install -r requirements.txt

### 2. Create the database and load the schema

    createdb uofu_budget
    psql -d uofu_budget -f sql/001_init.sql

Note: the schema does not ship with seed data yet, so you'll need to insert at least one `departments` row (with an `annual_cap_cents` and `reserve_requirement_cents`) before creating requests.

### 3. Configure the connection

The service reads Postgres settings from environment variables (see `get_conn()` in `src/service.py`):

    export DB_NAME=uofu_budget
    export DB_USER=your_user
    export DB_PASSWORD=your_password
    export DB_HOST=localhost

### 4. Create a request

    from src.service import create_request

    request_id = create_request(
        department_id=1,
        requester_utaid="u0123456",
        category="equipment",
        amount_cents=45000,   # $450.00
        justification="New lab monitor",
    )
    print(request_id)

New requests are created directly in the `SUBMITTED` state (DRAFT is skipped for the MVP) with a 14-day expiration.

## Project structure

- `sql/001_init.sql` — schema: enum + departments, grants, spend_requests, payments
- `src/service.py` — service layer: connection, create_request, fiscal checks
- `requirements.txt`
- `README.md`

## Current status

Implemented in `src/service.py`:

- `RequestState` enum mirroring the DB `request_state` enum.
- `PolicyViolation` / `ConcurrencyError` exception types.
- `get_conn()` — opens a Postgres connection from env vars.
- `create_request(...)` — inserts a `SUBMITTED` request with a 14-day expiry.
- `_compute_fiscal_start(...)` — resolves the fiscal-year start (July 1).
- `_check_fiscal_constraints(...)` — enforces the department annual cap against already `APPROVED`/`PAID` spend in the current fiscal year.

## Roadmap

Not yet implemented, in rough priority order:

- **State transitions**: `approve`, `reject`, and `pay`, with state machine rules enforced.
- **Reserve enforcement**: check `reserve_requirement_cents` alongside the annual cap.
- **Concurrency safety**: row locking (`SELECT ... FOR UPDATE`) and use of the `version` column on approve.
- **Idempotency**: honor `idempotency_key` on externally triggered operations.
- **Grant rules** and per-request limits.
- **Seed data** for departments and grants.
- **Agent layer**: Requester / Approver / Payment / Treasury services over an API and event bus.
