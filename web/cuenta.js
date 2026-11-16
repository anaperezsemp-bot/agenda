// Cuentas de usuario con Supabase: sesión, preferencias, "tengo entrada" y favoritos.
// Si config.js no tiene datos, Cuenta.activa es false y la web funciona sin cuentas.

const Cuenta = (() => {
  const cfg = window.AGENDA_CONFIG || {};
  const activa = Boolean(cfg.supabaseUrl && cfg.supabaseKey);
  const LIB = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.110.0/dist/umd/supabase.min.js";
  let cliente = null;
  let cargando = null;

  function cargarLibreria() {
    if (window.supabase) return Promise.resolve();
    return new Promise((ok, mal) => {
      const s = document.createElement("script");
      s.src = LIB;
      s.onload = ok;
      s.onerror = () => mal(new Error("No se pudo cargar Supabase"));
      document.head.appendChild(s);
    });
  }

  async function sb() {
    if (!activa) return null;
    if (cliente) return cliente;
    cargando = cargando || cargarLibreria().then(() => {
      cliente = window.supabase.createClient(cfg.supabaseUrl, cfg.supabaseKey);
      return cliente;
    });
    return cargando;
  }

  async function usuario() {
    const c = await sb();
    if (!c) return null;
    const { data } = await c.auth.getSession();
    return data.session?.user || null;
  }

  async function entrar(email) {
    const c = await sb();
    const destino = new URL("cuenta.html", location.href).href;
    const { error } = await c.auth.signInWithOtp({ email, options: { emailRedirectTo: destino } });
    if (error) throw error;
  }

  async function salir() {
    const c = await sb();
    await c.auth.signOut();
  }

  async function perfil() {
    const c = await sb();
    const u = await usuario();
    if (!u) return null;
    const { data, error } = await c.from("perfiles").select("salas, generos").eq("user_id", u.id).maybeSingle();
    if (error) throw error;
    return data || { salas: [], generos: [] };
  }

  async function guardarPerfil({ salas, generos }) {
    const c = await sb();
    const u = await usuario();
    const { error } = await c.from("perfiles").upsert({
      user_id: u.id, salas, generos, updated_at: new Date().toISOString(),
    });
    if (error) throw error;
  }

  // Listas de conciertos de cada persona: "voy" (tengo entrada) y "favoritos".
  async function lista(tabla) {
    const c = await sb();
    const u = await usuario();
    if (!u) return [];
    const { data, error } = await c.from(tabla).select("concierto_id, fecha, titulo, sala")
      .eq("user_id", u.id).gte("fecha", Agenda.hoyISO()).order("fecha");
    if (error) throw error;
    return data;
  }

  async function marcar(tabla, concierto, si) {
    const c = await sb();
    const u = await usuario();
    const { error } = si
      ? await c.from(tabla).upsert({
          user_id: u.id, concierto_id: concierto.id, fecha: concierto.fecha,
          titulo: concierto.titulo, sala: concierto.sala,
        })
      : await c.from(tabla).delete().eq("user_id", u.id).eq("concierto_id", concierto.id);
    if (error) throw error;
  }

  return {
    activa, usuario, entrar, salir, perfil, guardarPerfil,
    voyLista: () => lista("voy"),
    favLista: () => lista("favoritos"),
    marcarVoy: (c, si) => marcar("voy", c, si),
    marcarFav: (c, si) => marcar("favoritos", c, si),
  };
})();
