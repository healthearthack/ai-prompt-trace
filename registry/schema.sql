-- Prompt Trace v4 portable identity database (PostgreSQL 16+)
-- One person account owns one permanent author ID across every device and workplace.

begin;
create extension if not exists pgcrypto;
create extension if not exists citext;
create schema if not exists prompt_trace;
set search_path = prompt_trace, public;

create type account_status as enum ('pending', 'active', 'locked', 'retired');
create type identity_status as enum ('reserved', 'active', 'retired');
create type device_status as enum ('pending', 'active', 'revoked', 'retired');
create type membership_role as enum ('member', 'manager', 'administrator', 'auditor');
create type membership_status as enum ('invited', 'active', 'suspended', 'ended');
create type workspace_kind as enum ('personal', 'organization');
create type portability_mode as enum ('full_content', 'signed_receipt', 'organization_only');

create table accounts (
  account_id uuid primary key default gen_random_uuid(),
  primary_email citext not null unique,
  username citext not null unique check (username::text ~ '^[a-z0-9][a-z0-9._-]{2,31}$'),
  display_name varchar(80) not null,
  password_hash text check (password_hash is null or password_hash like '$argon2id$%'),
  status account_status not null default 'pending',
  email_verified_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  last_login_at timestamptz
);

create table author_identities (
  author_id varchar(8) primary key check (author_id ~ '^[A-Z0-9]{1,8}$'),
  account_id uuid unique references accounts(account_id),
  public_display_name varchar(80) not null,
  status identity_status not null default 'reserved',
  claimed_order bigint generated always as identity unique,
  reserved_at timestamptz not null default now(),
  activated_at timestamptz,
  retired_at timestamptz,
  check ((status = 'reserved' and account_id is null)
      or (status = 'active' and account_id is not null and activated_at is not null and retired_at is null)
      or (status = 'retired' and retired_at is not null))
);

create table reserved_author_ids (
  author_id varchar(8) primary key check (author_id ~ '^[A-Z0-9]{1,8}$'),
  reservation_class varchar(40) not null,
  reason text not null,
  created_at timestamptz not null default now()
);

create table reserved_author_id_requests (
  request_id uuid primary key default gen_random_uuid(),
  author_id varchar(8) not null references reserved_author_ids(author_id),
  account_id uuid not null references accounts(account_id),
  purpose text not null,
  status text not null default 'pending' check (status in ('pending', 'approved', 'denied', 'revoked')),
  requested_at timestamptz not null default now(),
  decided_at timestamptz,
  decided_by uuid references accounts(account_id),
  unique(author_id, account_id)
);

create function enforce_reserved_author_id() returns trigger language plpgsql as $$
begin
  if new.status <> 'reserved' and exists (select 1 from reserved_author_ids r where r.author_id = new.author_id) then
    if new.account_id is null or not exists (
      select 1 from reserved_author_id_requests q
      where q.author_id = new.author_id and q.account_id = new.account_id and q.status = 'approved'
    ) then
      raise exception 'Author ID % is reserved and requires approved internal allocation', new.author_id;
    end if;
  end if;
  return new;
end $$;

create trigger enforce_reserved_author_id_before_write
before insert or update on author_identities
for each row execute function enforce_reserved_author_id();

create table passkey_credentials (
  passkey_id uuid primary key default gen_random_uuid(),
  account_id uuid not null references accounts(account_id),
  credential_id bytea not null unique,
  public_key bytea not null,
  sign_count bigint not null default 0 check (sign_count >= 0),
  device_label varchar(100),
  created_at timestamptz not null default now(),
  last_used_at timestamptz,
  revoked_at timestamptz
);

create table sessions (
  session_id uuid primary key default gen_random_uuid(),
  account_id uuid not null references accounts(account_id),
  token_hash bytea not null unique,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null,
  last_seen_at timestamptz not null default now(),
  revoked_at timestamptz,
  ip_prefix inet,
  user_agent_hash bytea,
  check (expires_at > created_at)
);

create table organizations (
  organization_id uuid primary key default gen_random_uuid(),
  legal_name varchar(160) not null,
  slug citext not null unique check (slug::text ~ '^[a-z0-9][a-z0-9-]{1,62}$'),
  created_at timestamptz not null default now()
);

create table organization_memberships (
  membership_id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(organization_id),
  account_id uuid not null references accounts(account_id),
  employee_reference_ciphertext bytea,
  role membership_role not null default 'member',
  status membership_status not null default 'invited',
  joined_at timestamptz,
  ended_at timestamptz,
  unique (organization_id, account_id),
  check (ended_at is null or status = 'ended')
);

create table devices (
  device_id uuid primary key default gen_random_uuid(),
  account_id uuid not null references accounts(account_id),
  device_name varchar(100) not null,
  platform varchar(40) not null,
  public_key text not null unique,
  public_key_fingerprint varchar(64) not null unique,
  status device_status not null default 'pending',
  enrolled_at timestamptz not null default now(),
  credential_expires_at timestamptz not null,
  last_seen_at timestamptz,
  revoked_at timestamptz,
  check (credential_expires_at = enrolled_at + interval '100 years')
);

create table workspaces (
  workspace_id uuid primary key default gen_random_uuid(),
  kind workspace_kind not null,
  owner_account_id uuid references accounts(account_id),
  organization_id uuid references organizations(organization_id),
  name varchar(100) not null,
  portability portability_mode not null default 'signed_receipt',
  retain_raw_content boolean not null default false,
  retention_days integer check (retention_days is null or retention_days between 1 and 36500),
  created_at timestamptz not null default now(),
  check ((kind = 'personal' and owner_account_id is not null and organization_id is null)
      or (kind = 'organization' and owner_account_id is null and organization_id is not null)),
  check (not retain_raw_content or portability = 'full_content')
);

create table consent_grants (
  consent_id uuid primary key default gen_random_uuid(),
  account_id uuid not null references accounts(account_id),
  device_id uuid not null references devices(device_id),
  workspace_id uuid not null references workspaces(workspace_id),
  notice_version varchar(40) not null,
  capture_scope jsonb not null check (jsonb_typeof(capture_scope) = 'object'),
  granted_at timestamptz not null default now(),
  revoked_at timestamptz
);
create unique index one_active_consent_per_device_workspace
  on consent_grants(device_id, workspace_id) where revoked_at is null;

create table ledger_records (
  record_id uuid primary key,
  account_id uuid not null references accounts(account_id),
  author_id varchar(8) not null references author_identities(author_id),
  device_id uuid not null references devices(device_id),
  workspace_id uuid not null references workspaces(workspace_id),
  organization_id uuid references organizations(organization_id),
  occurred_at timestamptz not null,
  received_at timestamptz not null default now(),
  source varchar(120) not null,
  entry_title varchar(180),
  entry_hash char(64) not null check (entry_hash ~ '^[0-9a-f]{64}$'),
  previous_hash char(64) check (previous_hash is null or previous_hash ~ '^[0-9a-f]{64}$'),
  code_signature_id varchar(80) not null,
  signature text not null,
  verified_at timestamptz,
  redaction_applied boolean not null default false,
  redaction_count integer not null default 0 check (redaction_count >= 0),
  metadata jsonb not null default '{}' check (jsonb_typeof(metadata) = 'object' and pg_column_size(metadata) <= 16384),
  entry_text_ciphertext bytea,
  encryption_key_reference text,
  check ((entry_text_ciphertext is null and encryption_key_reference is null)
      or (entry_text_ciphertext is not null and encryption_key_reference is not null))
);

create index ledger_account_timeline on ledger_records(account_id, occurred_at desc);
create index ledger_workspace_timeline on ledger_records(workspace_id, occurred_at desc);
create index ledger_organization_timeline on ledger_records(organization_id, occurred_at desc) where organization_id is not null;
create index ledger_metadata_search on ledger_records using gin(metadata);

create view account_continuity with (security_invoker = true) as
select
  l.account_id, l.record_id, l.author_id, l.occurred_at, l.source,
  w.kind as workspace_kind, w.name as workspace_name, w.portability,
  o.legal_name as organization_name,
  case when w.portability = 'organization_only' then null else l.entry_title end as portable_title,
  l.entry_hash, l.code_signature_id, l.signature, l.verified_at,
  case when w.portability = 'full_content' then l.entry_text_ciphertext else null end as portable_content_ciphertext
from ledger_records l
join workspaces w on w.workspace_id = l.workspace_id
left join organizations o on o.organization_id = l.organization_id;

create table cyber_cv_profiles (
  account_id uuid primary key references accounts(account_id),
  public_slug citext unique check (public_slug is null or public_slug::text ~ '^[a-z0-9][a-z0-9-]{2,62}$'),
  headline varchar(160),
  summary text,
  visibility text not null default 'private' check (visibility in ('private', 'unlisted', 'public')),
  updated_at timestamptz not null default now()
);

create table cyber_cv_entries (
  account_id uuid not null references accounts(account_id),
  record_id uuid not null references ledger_records(record_id),
  included boolean not null default false,
  sort_order integer,
  annotation text,
  excluded_at timestamptz,
  updated_at timestamptz not null default now(),
  primary key (account_id, record_id),
  check ((included and excluded_at is null) or not included)
);

create view cyber_cv_render with (security_invoker = true) as
select c.*, p.public_slug, p.headline, p.summary, p.visibility,
       e.sort_order, e.annotation
from account_continuity c
join cyber_cv_entries e on e.account_id = c.account_id and e.record_id = c.record_id
join cyber_cv_profiles p on p.account_id = c.account_id
where e.included = true and e.excluded_at is null;

create table security_events (
  security_event_id bigint generated always as identity primary key,
  account_id uuid references accounts(account_id),
  device_id uuid references devices(device_id),
  event_type varchar(80) not null,
  outcome varchar(20) not null check (outcome in ('success', 'failure', 'blocked')),
  occurred_at timestamptz not null default now(),
  metadata jsonb not null default '{}' check (jsonb_typeof(metadata) = 'object' and pg_column_size(metadata) <= 8192)
);

-- The application sets app.account_id after validating a session or passkey.
create function current_account_id() returns uuid language sql stable as $$
  select nullif(current_setting('app.account_id', true), '')::uuid
$$;

alter table accounts enable row level security;
alter table accounts force row level security;
create policy account_self on accounts using (account_id = current_account_id());

alter table author_identities enable row level security;
alter table author_identities force row level security;
create policy identity_owner on author_identities for select using (account_id = current_account_id());

alter table reserved_author_id_requests enable row level security;
alter table reserved_author_id_requests force row level security;
create policy reserved_request_owner on reserved_author_id_requests for select using (account_id = current_account_id());

alter table passkey_credentials enable row level security;
alter table passkey_credentials force row level security;
create policy passkey_owner on passkey_credentials for select using (account_id = current_account_id());

alter table sessions enable row level security;
alter table sessions force row level security;
create policy session_owner on sessions for select using (account_id = current_account_id());

alter table organization_memberships enable row level security;
alter table organization_memberships force row level security;
create policy membership_owner on organization_memberships for select using (account_id = current_account_id());

alter table devices enable row level security;
alter table devices force row level security;
create policy device_owner on devices using (account_id = current_account_id());

alter table workspaces enable row level security;
alter table workspaces force row level security;
create policy workspace_owner_or_member on workspaces for select using (
  owner_account_id = current_account_id()
  or exists (
    select 1 from organization_memberships m
    where m.organization_id = workspaces.organization_id
      and m.account_id = current_account_id()
      and m.status = 'active'
  )
);

alter table consent_grants enable row level security;
alter table consent_grants force row level security;
create policy consent_owner on consent_grants using (account_id = current_account_id());

alter table ledger_records enable row level security;
alter table ledger_records force row level security;
create policy ledger_owner on ledger_records for select using (account_id = current_account_id());

alter table cyber_cv_profiles enable row level security;
alter table cyber_cv_profiles force row level security;
create policy cyber_cv_profile_owner on cyber_cv_profiles using (account_id = current_account_id());

alter table cyber_cv_entries enable row level security;
alter table cyber_cv_entries force row level security;
create policy cyber_cv_entry_owner on cyber_cv_entries using (account_id = current_account_id());

alter table security_events enable row level security;
alter table security_events force row level security;
create policy security_event_owner on security_events for select using (account_id = current_account_id());

commit;
