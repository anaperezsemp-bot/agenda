// Utilidades compartidas por la agenda y el detalle.

const Agenda = (() => {
  const fmtDia = new Intl.DateTimeFormat("es-ES", { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" });
  const fmtSemana = new Intl.DateTimeFormat("es-ES", { weekday: "short", timeZone: "UTC" });

  // Fechas como "AAAA-MM-DD" en hora de Madrid, para que "hoy" no dependa del huso del móvil.
  function hoyISO() {
    return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Madrid" }).format(new Date());
  }
  function sumarDias(iso, n) {
    const d = new Date(iso + "T00:00:00Z");
    d.setUTCDate(d.getUTCDate() + n);
    return d.toISOString().slice(0, 10);
  }
  function nombreDia(iso) {
    const hoy = hoyISO();
    const largo = fmtDia.format(new Date(iso + "T00:00:00Z"));
    if (iso === hoy) return "Hoy · " + largo;
    if (iso === sumarDias(hoy, 1)) return "Mañana · " + largo;
    return largo;
  }
  function diaSemanaCorto(iso) {
    return fmtSemana.format(new Date(iso + "T00:00:00Z")).replace(".", "");
  }
  function precioTexto(p) {
    if (p === undefined || p === null) return "";
    if (p === 0) return "Gratis";
    return (Number.isInteger(p) ? p : p.toFixed(2).replace(".", ",")) + " €";
  }
  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  }
  async function cargar(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error(r.status + " " + url);
    return r.json();
  }

  return { hoyISO, sumarDias, nombreDia, diaSemanaCorto, precioTexto, esc, cargar };
})();
