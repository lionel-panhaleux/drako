create extension if not exists unaccent;
create extension if not exists pgcrypto;

create or replace function utcnow() returns timestamp as $$
  begin
    return (now() at time zone 'UTC')::timestamp;
  end;
  $$ language plpgsql;

begin;

/* DESIGN NOTES
Nota bene: all timestamp are UTC and all dates are local,
because PostgreSQL does not handle DST precisely (from PSQL 9.6 documentation):
"The default time zone is specified as a constant numeric offset from UTC.
It is therefore impossible to adapt to daylight-saving time
when doing date/time arithmetic across DST boundaries."
*/

------------------------------------ TYPES ------------------------------------
create type price as (
  base_amount integer,
  taxes integer[]
  );

create type invoice_reference as (
  prefix text,
  number bigint
  );

create type payment_type as enum(
  'normal',
  'cancelled',
  'duplicate',
  'chargeback'
  );

------------------------------------ TABLES ------------------------------------
create table firm (
  uid uuid primary key default gen_random_uuid(),
  label text,
  timezone text,  -- IANA time zone
  invoice_format jsonb not null default '{}'::jsonb,
  images text[] default '{}'::text[]
  );

-- config contains taxes and items pricing
create table config (
  uid uuid primary key default gen_random_uuid(),
  firm uuid not null references firm,
  effective_date timestamp not null default utcnow(),
  content jsonb not null default '{}'::jsonb
  );

create table customer_account (
  uid uuid primary key default gen_random_uuid(),
  firm uuid not null references firm,
  reference jsonb not null unique default '{}'::jsonb,
  name text not null default '',
  address text not null default '',
  contact jsonb not null unique default '{}'::jsonb
  );

create table document (
  uid uuid primary key default gen_random_uuid(),
  external_reference text,
  backend text not null default '',
  path jsonb not null default '{}'::jsonb
  );

create table payment_mode (
  uid uuid primary key default gen_random_uuid(),
  customer uuid not null references customer_account,
  authorized bool not null default false,
  backend text not null default '',
  document uuid references document,
  reference jsonb not null unique default '{}'::jsonb
  );

create table pricing (
  uid uuid primary key default gen_random_uuid(),
  customer uuid not null references customer_account,
  config uuid not null references config,
  item text not null,  -- reference of item in config
  details jsonb not null unique default '{}'::jsonb,  -- details for invoicing
  quantity integer not null,
  amount price,
  range tsrange not null
  );

create table invoice (
  reference invoice_reference primary key,
  customer uuid not null references customer_account,
  amount price,
  content jsonb not null default '{}'::jsonb,
  document uuid references document,
  creation_date timestamp not null default utcnow(),
  due_date timestamp not null default utcnow()
  );

create table assignment (
  uid uuid primary key default gen_random_uuid(),
  pricing uuid not null references pricing,
  invoice invoice_reference not null references invoice
  );

create table journal (
  assignment uuid not null references assignment,
  date date not null,
  amount price
  );

create table account(
  id uuid primary key default gen_random_uuid(),
  reference jsonb not null unique default '{}'::jsonb
  );

create table cashflow (
  uid uuid primary key default gen_random_uuid(),
  payment_mode uuid not null references payment_mode,
  account uuid not null references account,
  date date,
  type payment_type not null default 'normal',
  amount integer,
  document uuid references document,
  proof jsonb not null default '{}'::jsonb,
  parent uuid references cashflow
  );

create table payment (
  target_invoice invoice_reference references invoice,
  source_invoice invoice_reference references invoice,
  cashflow uuid references cashflow,
  amount integer  -- signed from target POV
  );

create table compensation(
  cashflow uuid references cashflow,
  amount integer,
  backend text not null default '',
  document uuid references document,
  proof jsonb not null default '{}'::jsonb
  );

------------------------------- DENORMALIZATION -------------------------------
create table daily_sales (
  date date,
  amount price
  );

create table daily_payments (
  date date,
  amount price
  );

commit;
