# UofU Budget Copilot (MVP Kernel)

This repo is the **MVP kernel** for an institutional budget copilot, starting with a
single-department, narrow-category, human-in-the-loop flow.

It focuses on:

- A minimal **relational schema** (Postgres) for departments, grants, spend requests, and payments.
- A **request state machine** with safe transitions (DRAFT → SUBMITTED → APPROVED → PAID, etc.).
- **Fiscal and policy constraints** (caps, reserves, per-request limits, grant rules) encoded in code.
- **Concurrency and idempotency** around the `approve` operation.

Higher-level “agents” (Requester, Approver, Payment, Treasury, etc.) will be layered on
top of this kernel later via APIs and an event bus.

## High-level idea

Think of this as:

- The **source of truth** for: what budgets exist, what requests have been made,
  and which ones are approved or paid.
- A **workflow engine** that owns the lifecycle of each request.
- A **ledger boundary** where, later, real payment rails (ERP/AP, ACH, AP2/NET Dollar)
  will plug in.

For now, payments are recorded manually; the goal is to prove the core invariants:
no double-spend, caps and reserves enforced, and a clear audit trail of state transitions.

## Getting started

### 1. Install dependencies

You’ll need:

- Python 3.11+
- Postgres running locally
- `psycopg2-binary`

Install Python deps:

```bash
pip install -r requirements.txt
