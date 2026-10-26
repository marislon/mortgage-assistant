CREATE TABLE payment_day_changes (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    loan_id bigint NOT NULL REFERENCES loans(id),
    old_day smallint NOT NULL CHECK (old_day BETWEEN 1 AND 28),
    new_day smallint NOT NULL CHECK (new_day BETWEEN 1 AND 28),
    changed_at timestamptz NOT NULL DEFAULT NOW(),
    CHECK (old_day <> new_day)
);