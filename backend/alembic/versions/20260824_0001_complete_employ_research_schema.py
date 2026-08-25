"""Create the complete Employ Research schema.

Revision ID: 20260824_0001
Revises: None
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260824_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        r"""
        create schema if not exists app_private;

        create or replace function app_private.set_updated_at()
        returns trigger language plpgsql set search_path = '' as $$
        begin
          new.updated_at = now();
          return new;
        end;
        $$;

        create table if not exists public.users (
          id uuid primary key,
          email varchar(320) not null,
          password_hash varchar(255) not null,
          is_active boolean not null default true,
          created_at timestamptz not null default now()
        );
        alter table public.users add column if not exists updated_at timestamptz not null default now();
        alter table public.users alter column id set default gen_random_uuid();
        alter table public.users alter column is_active set default true;
        alter table public.users alter column created_at set default now();
        create unique index if not exists uq_users_email_lower on public.users (lower(email));

        create table public.candidate_profiles (
          id uuid primary key default gen_random_uuid(),
          user_id uuid not null unique references public.users(id) on delete cascade,
          professional_summary text,
          total_experience_months integer check (total_experience_months is null or total_experience_months >= 0),
          experiences jsonb not null default '[]'::jsonb check (jsonb_typeof(experiences) = 'array'),
          skills jsonb not null default '[]'::jsonb check (jsonb_typeof(skills) = 'array'),
          languages jsonb not null default '[]'::jsonb check (jsonb_typeof(languages) = 'array'),
          certifications jsonb not null default '[]'::jsonb check (jsonb_typeof(certifications) = 'array'),
          education jsonb not null default '[]'::jsonb check (jsonb_typeof(education) = 'array'),
          source_text text,
          extraction_status varchar(24) not null default 'pending' check (extraction_status in ('pending','processing','completed','failed','manual')),
          created_at timestamptz not null default now(),
          updated_at timestamptz not null default now()
        );

        create table public.resumes (
          id uuid primary key default gen_random_uuid(),
          user_id uuid not null references public.users(id) on delete cascade,
          label varchar(100) not null,
          original_filename varchar(255) not null,
          storage_path text not null,
          mime_type varchar(100) not null,
          size_bytes bigint not null check (size_bytes > 0),
          file_sha256 char(64) not null,
          extracted_text text,
          parsing_status varchar(24) not null default 'pending' check (parsing_status in ('pending','processing','completed','failed')),
          is_default boolean not null default false,
          created_at timestamptz not null default now(),
          updated_at timestamptz not null default now(),
          unique (user_id, label),
          unique (user_id, file_sha256)
        );
        create unique index uq_resumes_one_default_per_user on public.resumes(user_id) where is_default;

        create table public.search_profiles (
          id uuid primary key default gen_random_uuid(),
          user_id uuid not null references public.users(id) on delete cascade,
          name varchar(120) not null,
          country_code char(2) not null,
          regions jsonb not null default '[]'::jsonb check (jsonb_typeof(regions) = 'array'),
          cities jsonb not null default '[]'::jsonb check (jsonb_typeof(cities) = 'array'),
          job_titles jsonb not null default '[]'::jsonb check (jsonb_typeof(job_titles) = 'array'),
          areas jsonb not null default '[]'::jsonb check (jsonb_typeof(areas) = 'array'),
          objective text,
          flexibility_level varchar(16) not null default 'medium' check (flexibility_level in ('low','medium','high')),
          search_languages jsonb not null default '["en"]'::jsonb check (jsonb_typeof(search_languages) = 'array'),
          immigration_objective boolean not null default false,
          immigration_preferences jsonb not null default '{}'::jsonb check (jsonb_typeof(immigration_preferences) = 'object'),
          is_active boolean not null default true,
          created_at timestamptz not null default now(),
          updated_at timestamptz not null default now(),
          unique (user_id, name)
        );

        create table public.search_keywords (
          id uuid primary key default gen_random_uuid(),
          search_profile_id uuid not null references public.search_profiles(id) on delete cascade,
          term text not null,
          normalized_term text not null,
          language_code varchar(10) not null,
          keyword_type varchar(24) not null check (keyword_type in ('original','translation','synonym','expanded_title','negative')),
          source_term text,
          generation_source varchar(24) not null default 'deterministic' check (generation_source in ('manual','deterministic','ai')),
          is_active boolean not null default true,
          created_at timestamptz not null default now(),
          unique (search_profile_id, normalized_term, language_code, keyword_type)
        );

        create table public.job_sources (
          id uuid primary key default gen_random_uuid(),
          code varchar(50) not null unique,
          name varchar(100) not null,
          connector_type varchar(24) not null check (connector_type in ('greenhouse','lever','ashby','job_bank','quebec_emploi','custom_scraper')),
          base_url text,
          is_enabled boolean not null default true,
          configuration jsonb not null default '{}'::jsonb check (jsonb_typeof(configuration) = 'object'),
          created_at timestamptz not null default now(),
          updated_at timestamptz not null default now()
        );

        create table public.companies (
          id uuid primary key default gen_random_uuid(),
          normalized_name varchar(255) not null,
          display_name varchar(255) not null,
          sector varchar(150),
          description text,
          website_url text,
          careers_url text,
          address_line text,
          city varchar(150),
          region varchar(150),
          country_code char(2),
          postal_code varchar(30),
          enrichment_source varchar(100),
          enrichment_data jsonb not null default '{}'::jsonb check (jsonb_typeof(enrichment_data) = 'object'),
          enriched_at timestamptz,
          created_at timestamptz not null default now(),
          updated_at timestamptz not null default now()
        );
        create unique index uq_companies_normalized_country on public.companies(normalized_name, coalesce(country_code, ''));

        create table public.jobs (
          id uuid primary key default gen_random_uuid(),
          company_id uuid references public.companies(id) on delete set null,
          fingerprint char(64) not null unique,
          title varchar(255) not null,
          normalized_title varchar(255) not null,
          description text,
          employment_type varchar(40),
          workplace_type varchar(24) check (workplace_type is null or workplace_type in ('onsite','hybrid','remote','unknown')),
          city varchar(150),
          region varchar(150),
          country_code char(2),
          postal_code varchar(30),
          salary_min numeric(14,2),
          salary_max numeric(14,2),
          salary_currency char(3),
          salary_period varchar(16) check (salary_period is null or salary_period in ('hour','day','week','month','year')),
          language_requirements jsonb not null default '[]'::jsonb check (jsonb_typeof(language_requirements) = 'array'),
          immigration_data jsonb not null default '{}'::jsonb check (jsonb_typeof(immigration_data) = 'object'),
          published_at timestamptz,
          expires_at timestamptz,
          first_seen_at timestamptz not null default now(),
          last_seen_at timestamptz not null default now(),
          is_active boolean not null default true,
          created_at timestamptz not null default now(),
          updated_at timestamptz not null default now(),
          check (salary_min is null or salary_max is null or salary_min <= salary_max)
        );

        create table public.job_source_links (
          id uuid primary key default gen_random_uuid(),
          job_id uuid not null references public.jobs(id) on delete cascade,
          job_source_id uuid not null references public.job_sources(id) on delete cascade,
          external_job_id text,
          source_url text not null,
          raw_payload jsonb,
          source_published_at timestamptz,
          first_seen_at timestamptz not null default now(),
          last_seen_at timestamptz not null default now(),
          is_available boolean not null default true,
          unique (job_source_id, source_url)
        );

        create table public.company_contacts (
          id uuid primary key default gen_random_uuid(),
          company_id uuid not null references public.companies(id) on delete cascade,
          email varchar(320) not null,
          normalized_email varchar(320) not null,
          contact_type varchar(24) not null check (contact_type in ('careers','hr','rh','talent','contact','personal')),
          person_name varchar(200),
          job_title varchar(200),
          source_url text,
          confidence numeric(5,4) check (confidence is null or confidence between 0 and 1),
          is_personal boolean not null default false,
          approval_status varchar(24) not null default 'requires_review' check (approval_status in ('approved','requires_review','rejected')),
          approved_at timestamptz,
          approved_by_user_id uuid references public.users(id) on delete set null,
          created_at timestamptz not null default now(),
          updated_at timestamptz not null default now(),
          unique (company_id, normalized_email),
          check (approval_status <> 'approved' or approved_at is not null),
          check (not is_personal or contact_type = 'personal')
        );

        create table public.job_scores (
          id uuid primary key default gen_random_uuid(),
          user_id uuid not null references public.users(id) on delete cascade,
          job_id uuid not null references public.jobs(id) on delete cascade,
          search_profile_id uuid not null references public.search_profiles(id) on delete cascade,
          deterministic_score numeric(5,2) not null check (deterministic_score between 0 and 100),
          ai_score numeric(5,2) check (ai_score is null or ai_score between 0 and 100),
          objective_score numeric(5,2) check (objective_score is null or objective_score between 0 and 100),
          immigration_score numeric(5,2) check (immigration_score is null or immigration_score between 0 and 100),
          final_score numeric(5,2) not null check (final_score between 0 and 100),
          score_breakdown jsonb not null default '{}'::jsonb check (jsonb_typeof(score_breakdown) = 'object'),
          scoring_version varchar(50) not null,
          scored_at timestamptz not null default now(),
          unique (user_id, job_id, search_profile_id)
        );

        create table public.email_templates (
          id uuid primary key default gen_random_uuid(),
          user_id uuid not null references public.users(id) on delete cascade,
          name varchar(120) not null,
          subject_template text not null,
          body_template text not null,
          variables jsonb not null default '[]'::jsonb check (jsonb_typeof(variables) = 'array'),
          language_code varchar(10) not null default 'en',
          is_default boolean not null default false,
          created_at timestamptz not null default now(),
          updated_at timestamptz not null default now(),
          unique (user_id, name)
        );
        create unique index uq_email_templates_default_language on public.email_templates(user_id, language_code) where is_default;

        create table public.email_drafts (
          id uuid primary key default gen_random_uuid(),
          user_id uuid not null references public.users(id) on delete cascade,
          job_id uuid not null references public.jobs(id) on delete cascade,
          company_contact_id uuid references public.company_contacts(id) on delete set null,
          email_template_id uuid references public.email_templates(id) on delete set null,
          resume_id uuid references public.resumes(id) on delete set null,
          recipient_email varchar(320) not null,
          subject text not null,
          body text not null,
          generation_method varchar(24) not null default 'template' check (generation_method in ('manual','template','ai')),
          validation_status varchar(24) not null default 'pending' check (validation_status in ('pending','approved','requires_review','rejected')),
          validation_notes text,
          approved_at timestamptz,
          created_at timestamptz not null default now(),
          updated_at timestamptz not null default now()
        );

        create table public.email_queue (
          id uuid primary key default gen_random_uuid(),
          user_id uuid not null references public.users(id) on delete cascade,
          email_draft_id uuid not null unique references public.email_drafts(id) on delete cascade,
          status varchar(24) not null default 'pending' check (status in ('pending','scheduled','processing','sent','failed','cancelled')),
          scheduled_for timestamptz,
          priority smallint not null default 100 check (priority between 0 and 1000),
          attempts smallint not null default 0 check (attempts >= 0),
          max_attempts smallint not null default 3 check (max_attempts between 1 and 10),
          locked_at timestamptz,
          locked_by varchar(120),
          last_error text,
          created_at timestamptz not null default now(),
          updated_at timestamptz not null default now(),
          check (attempts <= max_attempts)
        );

        create table public.email_sends (
          id uuid primary key default gen_random_uuid(),
          user_id uuid not null references public.users(id) on delete cascade,
          email_draft_id uuid not null references public.email_drafts(id) on delete restrict,
          email_queue_id uuid references public.email_queue(id) on delete set null,
          provider varchar(24) not null default 'gmail' check (provider in ('gmail')),
          provider_message_id text,
          provider_thread_id text,
          recipient_email varchar(320) not null,
          subject text not null,
          status varchar(24) not null check (status in ('sent','failed','bounced','delivered','replied')),
          error_code varchar(100),
          error_message text,
          sent_at timestamptz,
          created_at timestamptz not null default now(),
          unique (provider, provider_message_id)
        );

        create table public.applications (
          id uuid primary key default gen_random_uuid(),
          user_id uuid not null references public.users(id) on delete cascade,
          job_id uuid not null references public.jobs(id) on delete cascade,
          resume_id uuid references public.resumes(id) on delete set null,
          email_draft_id uuid references public.email_drafts(id) on delete set null,
          latest_email_send_id uuid references public.email_sends(id) on delete set null,
          status varchar(32) not null default 'draft' check (status in ('draft','queued','sent','response_received','interview','rejected','withdrawn','hired')),
          applied_at timestamptz,
          last_event_at timestamptz,
          notes text,
          created_at timestamptz not null default now(),
          updated_at timestamptz not null default now(),
          unique (user_id, job_id)
        );

        create table public.application_events (
          id uuid primary key default gen_random_uuid(),
          application_id uuid not null references public.applications(id) on delete cascade,
          event_type varchar(32) not null check (event_type in ('created','queued','sent','response_received','interview','rejected','withdrawn','hired','note')),
          event_at timestamptz not null default now(),
          details jsonb not null default '{}'::jsonb check (jsonb_typeof(details) = 'object'),
          source varchar(24) not null default 'system' check (source in ('system','user','gmail','automation')),
          created_at timestamptz not null default now()
        );

        create table public.user_settings (
          user_id uuid primary key references public.users(id) on delete cascade,
          daily_email_target smallint not null default 3 check (daily_email_target in (3,5,10,15,20) and daily_email_target <= 20),
          sending_window_start time not null default '09:00',
          sending_window_end time not null default '17:00',
          timezone varchar(64) not null default 'America/Sao_Paulo',
          ai_provider varchar(50),
          validation_mode varchar(24) not null default 'manual' check (validation_mode in ('manual','semi_automatic','automatic')),
          ai_api_key_encrypted text,
          google_access_token_encrypted text,
          google_refresh_token_encrypted text,
          google_token_expires_at timestamptz,
          created_at timestamptz not null default now(),
          updated_at timestamptz not null default now(),
          check (sending_window_start <> sending_window_end)
        );
        comment on column public.user_settings.ai_api_key_encrypted is 'Application-encrypted value only; plaintext is forbidden.';
        comment on column public.user_settings.google_access_token_encrypted is 'Application-encrypted OAuth access token only; plaintext is forbidden.';
        comment on column public.user_settings.google_refresh_token_encrypted is 'Application-encrypted OAuth refresh token only; plaintext is forbidden.';

        create table public.daily_usage (
          id uuid primary key default gen_random_uuid(),
          user_id uuid not null references public.users(id) on delete cascade,
          usage_date date not null,
          emails_queued integer not null default 0 check (emails_queued >= 0),
          emails_sent integer not null default 0 check (emails_sent >= 0),
          deterministic_analyses integer not null default 0 check (deterministic_analyses >= 0),
          ai_analyses integer not null default 0 check (ai_analyses >= 0),
          failed_sends integer not null default 0 check (failed_sends >= 0),
          created_at timestamptz not null default now(),
          updated_at timestamptz not null default now(),
          unique (user_id, usage_date)
        );

        create table public.automation_runs (
          id uuid primary key default gen_random_uuid(),
          user_id uuid references public.users(id) on delete cascade,
          run_type varchar(32) not null check (run_type in ('daily_search','scraping','scoring','email_generation','email_sending','contact_enrichment')),
          status varchar(24) not null default 'pending' check (status in ('pending','running','completed','partial','failed','cancelled')),
          scheduled_for timestamptz,
          started_at timestamptz,
          finished_at timestamptz,
          items_processed integer not null default 0 check (items_processed >= 0),
          items_succeeded integer not null default 0 check (items_succeeded >= 0),
          items_failed integer not null default 0 check (items_failed >= 0),
          parameters jsonb not null default '{}'::jsonb check (jsonb_typeof(parameters) = 'object'),
          summary jsonb not null default '{}'::jsonb check (jsonb_typeof(summary) = 'object'),
          error_message text,
          created_at timestamptz not null default now(),
          check (finished_at is null or started_at is null or finished_at >= started_at)
        );

        create table public.scraping_logs (
          id uuid primary key default gen_random_uuid(),
          automation_run_id uuid references public.automation_runs(id) on delete cascade,
          job_source_id uuid references public.job_sources(id) on delete set null,
          level varchar(16) not null default 'info' check (level in ('debug','info','warning','error')),
          event_type varchar(50) not null,
          url text,
          http_status integer check (http_status is null or http_status between 100 and 599),
          message text not null,
          details jsonb not null default '{}'::jsonb check (jsonb_typeof(details) = 'object'),
          occurred_at timestamptz not null default now()
        );

        create index ix_candidate_profiles_user on public.candidate_profiles(user_id);
        create index ix_resumes_user on public.resumes(user_id);
        create index ix_search_profiles_user_active on public.search_profiles(user_id, is_active);
        create index ix_search_keywords_profile_active on public.search_keywords(search_profile_id, is_active);
        create index ix_jobs_company on public.jobs(company_id);
        create index ix_jobs_location_active on public.jobs(country_code, region, city) where is_active;
        create index ix_jobs_last_seen_active on public.jobs(last_seen_at desc) where is_active;
        create index ix_job_source_links_job on public.job_source_links(job_id);
        create index ix_job_source_links_source_external on public.job_source_links(job_source_id, external_job_id) where external_job_id is not null;
        create index ix_company_contacts_review on public.company_contacts(company_id, approval_status) where approval_status = 'requires_review';
        create index ix_job_scores_job on public.job_scores(job_id);
        create index ix_job_scores_user_final on public.job_scores(user_id, final_score desc);
        create index ix_email_drafts_user_status on public.email_drafts(user_id, validation_status);
        create index ix_email_queue_ready on public.email_queue(scheduled_for, priority, created_at) where status in ('pending','scheduled');
        create index ix_email_sends_user_sent on public.email_sends(user_id, sent_at desc);
        create index ix_applications_user_status on public.applications(user_id, status);
        create index ix_application_events_application_time on public.application_events(application_id, event_at desc);
        create index ix_daily_usage_date on public.daily_usage(usage_date);
        create index ix_automation_runs_user_status on public.automation_runs(user_id, status, scheduled_for);
        create index ix_scraping_logs_run_time on public.scraping_logs(automation_run_id, occurred_at);
        create index ix_scraping_logs_errors on public.scraping_logs(occurred_at desc) where level = 'error';

        create trigger trg_users_updated_at before update on public.users for each row execute function app_private.set_updated_at();
        create trigger trg_candidate_profiles_updated_at before update on public.candidate_profiles for each row execute function app_private.set_updated_at();
        create trigger trg_resumes_updated_at before update on public.resumes for each row execute function app_private.set_updated_at();
        create trigger trg_search_profiles_updated_at before update on public.search_profiles for each row execute function app_private.set_updated_at();
        create trigger trg_job_sources_updated_at before update on public.job_sources for each row execute function app_private.set_updated_at();
        create trigger trg_companies_updated_at before update on public.companies for each row execute function app_private.set_updated_at();
        create trigger trg_jobs_updated_at before update on public.jobs for each row execute function app_private.set_updated_at();
        create trigger trg_company_contacts_updated_at before update on public.company_contacts for each row execute function app_private.set_updated_at();
        create trigger trg_email_templates_updated_at before update on public.email_templates for each row execute function app_private.set_updated_at();
        create trigger trg_email_drafts_updated_at before update on public.email_drafts for each row execute function app_private.set_updated_at();
        create trigger trg_email_queue_updated_at before update on public.email_queue for each row execute function app_private.set_updated_at();
        create trigger trg_applications_updated_at before update on public.applications for each row execute function app_private.set_updated_at();
        create trigger trg_user_settings_updated_at before update on public.user_settings for each row execute function app_private.set_updated_at();
        create trigger trg_daily_usage_updated_at before update on public.daily_usage for each row execute function app_private.set_updated_at();

        insert into public.job_sources(code, name, connector_type, base_url) values
          ('greenhouse','Greenhouse','greenhouse','https://www.greenhouse.com'),
          ('lever','Lever','lever','https://www.lever.co'),
          ('ashby','Ashby','ashby','https://www.ashbyhq.com'),
          ('job_bank','Job Bank Canada','job_bank','https://www.jobbank.gc.ca'),
          ('quebec_emploi','Québec Emploi','quebec_emploi','https://www.quebec.ca/emploi'),
          ('custom_scraper','Scraping próprio','custom_scraper',null)
        on conflict (code) do nothing;

        alter table public.users enable row level security;
        alter table public.candidate_profiles enable row level security;
        alter table public.resumes enable row level security;
        alter table public.search_profiles enable row level security;
        alter table public.search_keywords enable row level security;
        alter table public.job_sources enable row level security;
        alter table public.companies enable row level security;
        alter table public.jobs enable row level security;
        alter table public.job_source_links enable row level security;
        alter table public.company_contacts enable row level security;
        alter table public.job_scores enable row level security;
        alter table public.email_templates enable row level security;
        alter table public.email_drafts enable row level security;
        alter table public.email_queue enable row level security;
        alter table public.email_sends enable row level security;
        alter table public.applications enable row level security;
        alter table public.application_events enable row level security;
        alter table public.user_settings enable row level security;
        alter table public.daily_usage enable row level security;
        alter table public.automation_runs enable row level security;
        alter table public.scraping_logs enable row level security;

        do $$
        begin
          if exists (select 1 from pg_roles where rolname = 'anon') then
            revoke all on all tables in schema public from anon;
          end if;
          if exists (select 1 from pg_roles where rolname = 'authenticated') then
            revoke all on all tables in schema public from authenticated;
          end if;
        end $$;
        """
    )


def downgrade() -> None:
    op.execute(
        r"""
        drop table if exists public.scraping_logs cascade;
        drop table if exists public.automation_runs cascade;
        drop table if exists public.daily_usage cascade;
        drop table if exists public.user_settings cascade;
        drop table if exists public.application_events cascade;
        drop table if exists public.applications cascade;
        drop table if exists public.email_sends cascade;
        drop table if exists public.email_queue cascade;
        drop table if exists public.email_drafts cascade;
        drop table if exists public.email_templates cascade;
        drop table if exists public.job_scores cascade;
        drop table if exists public.company_contacts cascade;
        drop table if exists public.job_source_links cascade;
        drop table if exists public.jobs cascade;
        drop table if exists public.companies cascade;
        drop table if exists public.job_sources cascade;
        drop table if exists public.search_keywords cascade;
        drop table if exists public.search_profiles cascade;
        drop table if exists public.resumes cascade;
        drop table if exists public.candidate_profiles cascade;
        drop trigger if exists trg_users_updated_at on public.users;
        alter table public.users drop column if exists updated_at;
        drop function if exists app_private.set_updated_at();
        drop schema if exists app_private;
        """
    )
