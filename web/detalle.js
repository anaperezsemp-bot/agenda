// Ficha de un concierto: lee data/events/<id>.json.

(() => {
  const { nombreDia, precioTexto, esc, cargar } = Agenda;
  const raiz = document.getElementById("detalle");

  // Volver conserva los filtros si venimos de la agenda.
  if (document.referrer && new URL(document.referrer).pathname.replace(/index\.html$/, "") === location.pathname.replace(/detalle\.html$/, "")) {
    document.getElementById("volver").addEventListener("click", (e) => {
      e.preventDefault();
      history.back();
    });
  }

  function precio(c) {
    if (c.precio_min === null || c.precio_min === undefined) return "";
    if (c.precio_max && c.precio_max !== c.precio_min) return `${precioTexto(c.precio_min)} – ${precioTexto(c.precio_max)}`;
    return precioTexto(c.precio_min);
  }

  function ics(c, sala) {
    const fecha = c.fecha.replaceAll("-", "");
    const inicio = c.hora ? `DTSTART;TZID=Europe/Madrid:${fecha}T${c.hora.replace(":", "")}00` : `DTSTART;VALUE=DATE:${fecha}`;
    const texto = [
      "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Agenda//ES", "BEGIN:VEVENT",
      `UID:${c.id}@agenda`, inicio, `SUMMARY:${c.titulo} en ${sala}`, `URL:${c.url || ""}`,
      "END:VEVENT", "END:VCALENDAR",
    ].join("\r\n");
    return "data:text/calendar;charset=utf-8," + encodeURIComponent(texto);
  }

  async function iniciar() {
    const id = new URLSearchParams(location.search).get("id");
    let c, agenda;
    try {
      [c, agenda] = await Promise.all([
        cargar(`data/events/${encodeURIComponent(id)}.json`),
        cargar("data/agenda.json"),
      ]);
    } catch (e) {
      raiz.querySelector(".estado").textContent = "Este concierto ya no está en la agenda.";
      return;
    }
    const sala = agenda.salas[c.sala] || { n: c.sala };
    document.title = `${c.titulo} · ${sala.n}`;
    const q = encodeURIComponent(c.titulo);
    const filas = [
      ["Fecha", nombreDia(c.fecha)],
      ["Hora", c.hora || "Por confirmar"],
      ["Precio", precio(c) || "Ver en la web"],
      ["Sala", `${esc(sala.n)}${sala.b ? " · " + esc(sala.b) : ""}`],
      ["Género", (c.generos || []).join(", ")],
    ].filter(([, v]) => v);

    raiz.querySelector(".estado").remove();
    raiz.insertAdjacentHTML("beforeend", `
      ${c.imagen ? `<img class="cartel" src="${esc(c.imagen)}" alt="Cartel de ${esc(c.titulo)}">` : ""}
      <article class="ficha">
        <h1>${esc(c.titulo)}</h1>
        ${c.agotado ? `<p><span class="tag-agotado">Entradas agotadas</span></p>` : ""}
        <dl class="datos">${filas.map(([k, v]) => `<dt>${k}</dt><dd>${k === "Sala" ? v : esc(v)}</dd>`).join("")}</dl>
        ${c.descripcion ? `<p class="descripcion">${esc(c.descripcion)}</p>` : ""}
        <div class="enlaces">
          <a class="btn" href="https://www.youtube.com/results?search_query=${q}" target="_blank" rel="noopener">Ver en YouTube</a>
          <a class="btn" href="https://open.spotify.com/search/${q}" target="_blank" rel="noopener">Escuchar en Spotify</a>
          <a class="btn" href="https://bandcamp.com/search?q=${q}" target="_blank" rel="noopener">Bandcamp</a>
          <a class="btn" href="${ics(c, sala.n)}" download="${esc(c.id)}.ics">Añadir al calendario</a>
          ${c.url ? `<a class="btn" href="${esc(c.url)}" target="_blank" rel="noopener">Web de la sala</a>` : ""}
        </div>
      </article>
      <div class="comprar">${
        c.agotado
          ? `<span>Agotado</span>`
          : c.url_entradas
            ? `<a href="${esc(c.url_entradas)}" target="_blank" rel="noopener">Comprar entradas</a>`
            : `<span>Venta en taquilla</span>`
      }</div>`);
  }

  iniciar();
})();
