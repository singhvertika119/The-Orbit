-- ============================================================
-- EXTENSIONS
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- for text search


-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT UNIQUE NOT NULL,
    name            TEXT,
    upi_id          TEXT,
    gst_number      TEXT,
    bank_details    TEXT,
    onboarded       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: users can only read/write their own row
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS users_self ON public.users;
CREATE POLICY users_self ON public.users
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());


-- ============================================================
-- CLIENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.clients (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    email           TEXT,
    phone           TEXT,
    platform        TEXT, -- 'upwork' | 'direct' | 'fiverr' | 'toptal' | 'referral' | 'other'
    company         TEXT,
    notes           TEXT,
    total_billed    DECIMAL(12,2) DEFAULT 0,
    total_paid      DECIMAL(12,2) DEFAULT 0,
    status          TEXT DEFAULT 'active', -- 'active' | 'inactive'
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.clients ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS clients_owner ON public.clients;
CREATE POLICY clients_owner ON public.clients
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_clients_user_id ON public.clients(user_id);


-- ============================================================
-- PROJECTS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.projects (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    client_id       UUID REFERENCES public.clients(id) ON DELETE SET NULL,
    title           TEXT NOT NULL,
    status          TEXT DEFAULT 'scoping',
    -- status: 'scoping' | 'active' | 'complete' | 'cancelled'
    
    deadline        DATE,
    value_inr       DECIMAL(12,2),
    
    -- Brief data
    brief_text      TEXT,           -- raw client brief
    brief_parsed    JSONB,          -- output from brief-parser agent
    
    -- Scope data
    scope           JSONB,          -- output from scope-advisor agent
    
    -- Proposal data
    proposal_text   TEXT,           -- output from proposal-drafter agent
    proposal_subject TEXT,
    proposal_sent_at TIMESTAMPTZ,
    proposal_status TEXT DEFAULT 'draft',
    -- proposal_status: 'draft' | 'sent' | 'accepted' | 'rejected'
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS projects_owner ON public.projects;
CREATE POLICY projects_owner ON public.projects
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_client_id ON public.projects(client_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON public.projects(status);


-- ============================================================
-- MILESTONES
-- ============================================================
CREATE TABLE IF NOT EXISTS public.milestones (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    title           TEXT NOT NULL,
    description     TEXT,
    due_date        DATE,
    status          TEXT DEFAULT 'pending',
    -- status: 'pending' | 'complete'
    
    -- Invoice linkage
    invoice_id      UUID,           -- set when invoice is generated
    invoice_triggered BOOLEAN DEFAULT FALSE,
    completed_at    TIMESTAMPTZ,
    
    sort_order      INTEGER DEFAULT 0,
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.milestones ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS milestones_owner ON public.milestones;
CREATE POLICY milestones_owner ON public.milestones
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_milestones_project_id ON public.milestones(project_id);
CREATE INDEX IF NOT EXISTS idx_milestones_user_id ON public.milestones(user_id);
CREATE INDEX IF NOT EXISTS idx_milestones_status ON public.milestones(status);
CREATE INDEX IF NOT EXISTS idx_milestones_due_date ON public.milestones(due_date);


-- ============================================================
-- INVOICES
-- ============================================================
CREATE TABLE IF NOT EXISTS public.invoices (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    project_id      UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    milestone_id    UUID REFERENCES public.milestones(id) ON DELETE SET NULL,
    client_id       UUID REFERENCES public.clients(id) ON DELETE SET NULL,
    
    -- Invoice identity
    invoice_number  TEXT NOT NULL UNIQUE,
    
    -- Amounts
    amount_inr      DECIMAL(12,2) NOT NULL,
    gst_rate        DECIMAL(5,2) DEFAULT 18.00,
    gst_inr         DECIMAL(12,2),
    total_inr       DECIMAL(12,2),
    
    -- Content
    invoice_text    TEXT,           -- formatted invoice from agent
    milestone_title TEXT,           -- snapshot of milestone name
    project_title   TEXT,           -- snapshot of project name
    client_name     TEXT,           -- snapshot of client name
    client_email    TEXT,
    
    -- Dates
    issued_date     DATE DEFAULT CURRENT_DATE,
    due_date        DATE,           -- issued_date + payment_terms_days
    paid_at         TIMESTAMPTZ,
    
    -- Status
    payment_status  TEXT DEFAULT 'draft',
    -- status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled'
    
    -- Follow-up drafts (stored as array of drafts)
    followup_drafts JSONB DEFAULT '[]',
    
    -- PDF
    pdf_url         TEXT,           -- Supabase Storage URL
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.invoices ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS invoices_owner ON public.invoices;
CREATE POLICY invoices_owner ON public.invoices
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_invoices_user_id ON public.invoices(user_id);
CREATE INDEX IF NOT EXISTS idx_invoices_project_id ON public.invoices(project_id);
CREATE INDEX IF NOT EXISTS idx_invoices_payment_status ON public.invoices(payment_status);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON public.invoices(due_date);


-- ============================================================
-- DIGEST CACHE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.digest_cache (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    generated_at    TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id) -- only one cached digest per user (upsert pattern)
);

ALTER TABLE public.digest_cache ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS digest_owner ON public.digest_cache;
CREATE POLICY digest_owner ON public.digest_cache
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());


-- ============================================================
-- ERROR LOGS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.error_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES public.users(id) ON DELETE SET NULL,
    agent_name      TEXT,
    endpoint        TEXT,
    error_message   TEXT,
    input_snapshot  TEXT,           -- first 500 chars of input
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- No RLS for error logs - system writes only
CREATE INDEX IF NOT EXISTS idx_error_logs_created_at ON public.error_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_error_logs_agent_name ON public.error_logs(agent_name);


-- ============================================================
-- INVOICE NUMBER SEQUENCE
-- ============================================================
CREATE SEQUENCE IF NOT EXISTS public.invoice_sequence START 1;

-- Function to generate invoice number
CREATE OR REPLACE FUNCTION public.generate_invoice_number(user_short_id TEXT)
RETURNS TEXT AS $$
DECLARE
    year_part TEXT;
    seq_num TEXT;
BEGIN
    year_part := EXTRACT(YEAR FROM NOW())::TEXT;
    seq_num := LPAD(nextval('public.invoice_sequence')::TEXT, 3, '0');
    RETURN 'GIG-' || year_part || '-' || UPPER(user_short_id) || '-' || seq_num;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- TRIGGERS
-- ============================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE OR REPLACE TRIGGER clients_updated_at
    BEFORE UPDATE ON public.clients
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE OR REPLACE TRIGGER projects_updated_at
    BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE OR REPLACE TRIGGER milestones_updated_at
    BEFORE UPDATE ON public.milestones
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE OR REPLACE TRIGGER invoices_updated_at
    BEFORE UPDATE ON public.invoices
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


-- Auto-update client totals when invoice status changes
CREATE OR REPLACE FUNCTION public.sync_client_totals()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.clients SET
        total_billed = (
            SELECT COALESCE(SUM(total_inr), 0)
            FROM public.invoices
            WHERE client_id = NEW.client_id
            AND payment_status != 'cancelled'
        ),
        total_paid = (
            SELECT COALESCE(SUM(total_inr), 0)
            FROM public.invoices
            WHERE client_id = NEW.client_id
            AND payment_status = 'paid'
        )
    WHERE id = NEW.client_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER invoices_sync_client_totals
    AFTER INSERT OR UPDATE OF payment_status ON public.invoices
    FOR EACH ROW EXECUTE FUNCTION public.sync_client_totals();


-- ============================================================
-- VIEWS
-- ============================================================

-- Today's dashboard view
CREATE OR REPLACE VIEW public.today_dashboard AS
SELECT
    u.id AS user_id,
    -- Overdue milestones
    (SELECT COUNT(*) FROM public.milestones m
     JOIN public.projects p ON m.project_id = p.id
     WHERE p.user_id = u.id
     AND m.status = 'pending'
     AND m.due_date < CURRENT_DATE) AS overdue_milestones,
    
    -- Due today
    (SELECT COUNT(*) FROM public.milestones m
     JOIN public.projects p ON m.project_id = p.id
     WHERE p.user_id = u.id
     AND m.status = 'pending'
     AND m.due_date = CURRENT_DATE) AS due_today,
    
    -- Overdue invoice amount
    (SELECT COALESCE(SUM(total_inr), 0) FROM public.invoices
     WHERE user_id = u.id
     AND payment_status IN ('sent', 'overdue')
     AND due_date < CURRENT_DATE) AS overdue_amount,
    
    -- Active projects
    (SELECT COUNT(*) FROM public.projects
     WHERE user_id = u.id
     AND status = 'active') AS active_projects

FROM public.users u;


-- Invoice summary view
CREATE OR REPLACE VIEW public.invoice_summary AS
SELECT
    user_id,
    SUM(total_inr) FILTER (WHERE payment_status != 'cancelled') AS total_billed,
    SUM(total_inr) FILTER (WHERE payment_status = 'paid') AS total_paid,
    SUM(total_inr) FILTER (WHERE payment_status IN ('sent', 'overdue') AND due_date < CURRENT_DATE) AS total_overdue
FROM public.invoices
GROUP BY user_id;


-- ============================================================
-- AUTH USER REGISTRATION SYNC TRIGGER (OPTION A)
-- ============================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, created_at, updated_at)
  VALUES (
    NEW.id,
    NEW.email,
    NOW(),
    NOW()
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
