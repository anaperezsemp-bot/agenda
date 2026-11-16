// Ficha de un concierto: lee data/events/<id>.json.

(() => {
  const { nombreDia, precioTexto, esc, cargar } = Agenda;
  const raiz = document.getElementById("detalle");
  const ICONO_FAV = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20.5s-7.5-4.6-9.3-9.2C1.4 7.9 3.6 4.5 7 4.5c2 0 3.5 1.1 5 3 1.5-1.9 3-3 5-3 3.4 0 5.6 3.4 4.3 6.8-1.8 4.6-9.3 9.2-9.3 9.2z"/></svg>`;
  const ICONO_ENTRADA = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 7.5A1.5 1.5 0 0 1 4.5 6h15A1.5 1.5 0 0 1 21 7.5V10a2 2 0 0 0 0 4v2.5a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 16.5V14a2 2 0 0 0 0-4z"/><path d="M15 6v12" stroke-dasharray="2 2"/></svg>`;

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
        <div class="titular">
          <h1>${esc(c.titulo)}</h1>
          <div class="marcas" id="marcas" hidden>
            <button class="icono" id="fav" type="button" aria-pressed="false" aria-label="Favorito" title="Favorito">${ICONO_FAV}</button>
            <button class="icono" id="voy" type="button" aria-pressed="false" aria-label="Tengo entrada" title="Tengo entrada">${ICONO_ENTRADA}</button>
          </div>
        </div>
        ${c.agotado ? `<p><span class="tag-agotado">Entradas agotadas</span></p>` : ""}
        <dl class="datos">${filas.map(([k, v]) => `<dt>${k}</dt><dd>${k === "Sala" ? v : esc(v)}</dd>`).join("")}</dl>
        ${c.audio ? `<div class="audio-detalle"><audio controls preload="none" src="${esc(c.audio)}"></audio>
          <p>Muestra de «${esc(c.cancion || "")}» · ${c.enlace_audio ? `<a href="${esc(c.enlace_audio)}" target="_blank" rel="noopener">Apple Music</a>` : "Apple Music"}</p></div>` : ""}
        ${c.descripcion ? `<p class="descripcion">${esc(c.descripcion)}</p>` : ""}
        <div class="enlaces">
          <button class="btn" id="copiar" type="button">Copiar enlace</button>
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
    prepararCopiar();
    prepararMarcas(c);
  }

  // Copiar la dirección del concierto para compartirla.
  function prepararCopiar() {
    const boton = document.getElementById("copiar");
    boton.addEventListener("click", async () => {
      const url = location.href;
      try {
        await navigator.clipboard.writeText(url);
      } catch {
        // Navegadores sin portapapeles: copia con un campo de texto temporal.
        const campo = Object.assign(document.createElement("textarea"), { value: url });
        document.body.append(campo);
        campo.select();
        document.execCommand("copy");
        campo.remove();
      }
      boton.textContent = "✓ Enlace copiado";
      setTimeout(() => (boton.textContent = "Copiar enlace"), 2500);
    });
  }

  // Favorito y "Tengo entrada": solo se ven con la sesión iniciada.
  async function prepararMarcas(c) {
    if (!Cuenta.activa) return;
    const usuario = await Cuenta.usuario().catch(() => null);
    if (!usuario) return;
    const [voy, fav] = await Promise.all([
      Cuenta.voyLista().catch(() => []),
      Cuenta.favLista().catch(() => null), // null: la tabla de favoritos aún no existe
    ]);
    const tiene = (l) => l.some((v) => v.concierto_id === c.id);
    enlazarMarca(document.getElementById("voy"), tiene(voy), (si) => Cuenta.marcarVoy(c, si));
    const botonFav = document.getElementById("fav");
    if (fav) enlazarMarca(botonFav, tiene(fav), (si) => Cuenta.marcarFav(c, si));
    else botonFav.remove();
    document.getElementById("marcas").hidden = false;
  }

  function enlazarMarca(boton, inicial, guardar) {
    let si = inicial;
    boton.setAttribute("aria-pressed", String(si));
    boton.addEventListener("click", async () => {
      boton.disabled = true;
      try {
        await guardar(!si);
        si = !si;
        boton.setAttribute("aria-pressed", String(si));
      } catch (e) {
        console.warn("No se pudo guardar", e);
      } finally {
        boton.disabled = false;
      }
    });
  }

  iniciar();
})();
