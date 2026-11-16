-- Conciertos favoritos de cada persona (el corazón del detalle).
-- Ejecutar una vez en Supabase: SQL Editor → New query → pegar → Run.
-- Solo crea cosas nuevas: no borra ni cambia nada de lo que ya hay.

create table if not exists public.favoritos (
  user_id      uuid not null references auth.users (id) on delete cascade,
  concierto_id text not null,
  fecha        date not null,
  titulo       text not null,
  sala         text not null,
  created_at   timestamptz not null default now(),
  primary key (user_id, concierto_id)
);

alter table public.favoritos enable row level security;

create policy "favorito propio" on public.favoritos
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
