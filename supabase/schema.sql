-- Cuentas de la agenda: preferencias de cada persona y conciertos a los que va a ir.
-- Ejecutar una vez en Supabase: SQL Editor → New query → pegar → Run.

create table if not exists public.perfiles (
  user_id    uuid primary key references auth.users (id) on delete cascade,
  salas      text[] not null default '{}',   -- ids de venues.yaml
  generos    text[] not null default '{}',
  updated_at timestamptz not null default now()
);

create table if not exists public.voy (
  user_id      uuid not null references auth.users (id) on delete cascade,
  concierto_id text not null,
  fecha        date not null,                -- para listar solo los que aún no han pasado
  titulo       text not null,
  sala         text not null,
  created_at   timestamptz not null default now(),
  primary key (user_id, concierto_id)
);

-- Cada persona solo ve y cambia sus propias filas.
alter table public.perfiles enable row level security;
alter table public.voy enable row level security;

drop policy if exists "perfil propio" on public.perfiles;
create policy "perfil propio" on public.perfiles
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "voy propio" on public.voy;
create policy "voy propio" on public.voy
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
