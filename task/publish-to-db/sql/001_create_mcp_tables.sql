-- Apply once to the destination DB; the publishing Task only inserts results.
CREATE TABLE public.mcp_components (
    id uuid PRIMARY KEY,
    name text NOT NULL,
    git_url text NOT NULL,
    CONSTRAINT mcp_components_identity_key UNIQUE (name, git_url)
);

CREATE TABLE public.mcp_evaluations (
    id uuid PRIMARY KEY,
    component_id uuid NOT NULL REFERENCES public.mcp_components(id),
    run_id text NOT NULL UNIQUE,
    commit_sha text NOT NULL,
    status text NOT NULL,
    stored_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.mcp_phase_results (
    id uuid PRIMARY KEY,
    evaluation_id uuid NOT NULL REFERENCES public.mcp_evaluations(id) ON DELETE CASCADE,
    phase text NOT NULL CHECK (phase IN ('static-eval', 'conformance-eval', 'behavioral-eval')),
    passed boolean NOT NULL,
    summary_json jsonb NOT NULL,
    CONSTRAINT mcp_phase_per_run_key UNIQUE (evaluation_id, phase)
);

CREATE TABLE public.mcp_check_results (
    id uuid PRIMARY KEY,
    phase_result_id uuid NOT NULL REFERENCES public.mcp_phase_results(id) ON DELETE CASCADE,
    check_id text NOT NULL,
    status text NOT NULL CHECK (status IN ('pass', 'fail', 'not_evaluated')),
    passed boolean,
    score double precision CHECK (score BETWEEN 0 AND 1),
    source text,
    message text NOT NULL DEFAULT '',
    findings_count integer CHECK (findings_count >= 0),
    CONSTRAINT mcp_check_per_phase_key UNIQUE (phase_result_id, check_id),
    CONSTRAINT mcp_check_status_passed_ck CHECK (
        (status = 'pass' AND passed IS TRUE)
        OR (status = 'fail' AND passed IS FALSE)
        OR (status = 'not_evaluated' AND passed IS NULL AND score IS NULL)
    )
);
