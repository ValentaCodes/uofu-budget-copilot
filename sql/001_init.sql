
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,          -- e.g., 'CS'
    name TEXT NOT NULL,
    annual_cap_cents BIGINT NOT NULL,   -- department cap (fiscal year)
    reserve_requirement_cents BIGINT NOT NULL
);

CREATE TABLE grants (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,          -- e.g., 'NSF-1234'
    name TEXT NOT NULL
);

-- Enum for tracking the state of each spend request
CREATE TYPE request_state AS ENUM (
    'DRAFT',
    'SUBMITTED',
    'UNDER_REVIEW',
    'APPROVED',
    'REJECTED',
    'PAID',
    'EXPIRED'
);

-- Core request entity, every time someone asks to spend money, a new row is created here. The state column tracks the lifecycle of the request.
CREATE TABLE spend_requests (
    id UUID PRIMARY KEY,
    department_id INT NOT NULL REFERENCES departments(id),
    grant_id INT REFERENCES grants(id),
    requester_utaid TEXT NOT NULL,
    category TEXT NOT NULL,
    amount_cents BIGINT NOT NULL,
    justification TEXT,
    state request_state NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    desired_date DATE,
    expires_at TIMESTAMPTZ,
    idempotency_key TEXT UNIQUE,             -- for external calls
    version INT NOT NULL DEFAULT 0           -- optimistic concurrency
);

-- Payments table, one row per executed payment. Each payment is linked to a spend request.
CREATE TABLE payments (
    id UUID PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES spend_requests(id),
    executed_at TIMESTAMPTZ NOT NULL,
    amount_cents BIGINT NOT NULL,
    UNIQUE (request_id)
);


-- Add seed data for departments and grants?