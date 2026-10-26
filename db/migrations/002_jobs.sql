CREATE TABLE jobs (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    loan_id bigint NOT NULL REFERENCES loans(id),
    idempotency_key text NOT NULL UNIQUE,
    job_type text NOT NULL,
    status text NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    payload jsonb NOT NULL,
    result jsonb,
    error_message text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    started_at timestamptz
);
