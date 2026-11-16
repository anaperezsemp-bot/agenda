// Página principal: listado por días con filtros guardados en la URL.

(() => {
  const { hoyISO, sumarDias, nombreDia, diaSemanaCorto, precioTexto, esc, cargar } = Agenda;
  const $ = (id) => document.getElementById(id);
  const LOTE = 60; // filas que se pintan de cada vez al hacer scroll
  const DIAS_TIRA = 14;

  let datos = null;
  let mio = null; // { salas, generos, voy:Set } cuando hay sesión
  let filtrados = [];
  let pintados = 0;
  let observador = null;

  // ---- Estado en la URL --------------------------------------------------
  function leerFiltros() {
    const p = new URLSearchParams(location.search);
    const lista = (k) => (p.get(k) ? p.get(k).split(",") : []);
    return {
      dia: p.get("dia") || "",
      desde: p.get("desde") || "",
      hasta: p.get("hasta") || "",
      pmax: p.get("pmax") ?? "",
      sinagotados: p.get("sinagotados") === "1",
      mios: p.get("mios") === "1",
      barrio: lista("barrio"),
      sala: lista("sala"),
      gen: lista("gen"),
    };
  }
  function guardarFiltros(f) {
    const p = new URLSearchParams();
    for (const [k, v] of Object.entries(f)) {
      if (Array.isArray(v) ? v.length : v) p.set(k, Array.isArray(v) ? v.join(",") : v === true ? "1" : v);
    }
    const qs = p.toString();
    history.replaceState(null, "", qs ? "?" + qs : location.pathname);
  }

  // ---- Filtrado -----------------------------------------------------------
  function aplicar(f) {
    const hoy = hoyISO();
    const pmax = f.pmax === "" ? null : Number(f.pmax);
    return datos.conciertos.filter((c) => {
      if (c.f < hoy) return false;
      if (f.dia) {
        if (c.f !== f.dia) return false;
      } else {
        if (f.desde && c.f < f.desde) return false;
        if (f.hasta && c.f > f.hasta) return false;
      }
      if (pmax !== null && (c.p === undefined || c.p > pmax)) return false;
      if (f.sinagotados && c.a) return false;
      if (f.mios && mio && !(mio.salas.includes(c.s) || (c.gen || []).some((g) => mio.generos.includes(g)))) return false;
      if (f.sala.length && !f.sala.includes(c.s)) return false;
      if (f.barrio.length && !f.barrio.includes(datos.salas[c.s]?.b)) return false;
      if (f.gen.length && !(c.gen || []).some((g) => f.gen.includes(g))) return false;
      return true;
    });
  }

  // ---- Pintado ------------------------------------------------------------
  function fila(c) {
    const sala = datos.salas[c.s]?.n || c.s;
    const meta = [];
    if (c.h) meta.push(`<span class="hora">${esc(c.h)}</span>`);
    if (mio?.voy.has(c.id)) meta.push(`<span class="tag-voy">Vas</span>`);
    if (c.a) meta.push(`<span class="tag-agotado">Agotado</span>`);
    else if (c.p !== undefined) meta.push(`<span class="precio">${esc(precioTexto(c.p))}</span>`);
    const boton = c.au
      ? `<button class="escuchar" type="button" data-audio="${esc(c.au)}" aria-label="Escuchar a ${esc(c.g)}" aria-pressed="false"></button>`
      : "";
    return `<li class="item"><a class="row${c.a ? " agotado" : ""}${c.au ? " con-audio" : ""}" href="detalle.html?id=${encodeURIComponent(c.id)}">
      <div class="info"><div class="grupo">${esc(c.g)}</div><div class="sala">${esc(sala)}</div></div>
      <div class="meta">${meta.join(" ")}</div></a>${boton}</li>`;
  }

  // ---- Escuchar sin salir del listado ---------------------------------------
  // Un único reproductor para toda la página: pulsar otro grupo para el anterior.
  const reproductor = new Audio();
  let botonActivo = null;
  function marcar(boton, sonando) {
    if (!boton) return;
    boton.setAttribute("aria-pressed", String(sonando));
    boton.classList.toggle("sonando", sonando);
  }
  function alternarAudio(boton) {
    if (boton === botonActivo && !reproductor.paused) {
      reproductor.pause();
      return;
    }
    marcar(botonActivo, false);
    botonActivo = boton;
    if (reproductor.src !== boton.dataset.audio) reproductor.src = boton.dataset.audio;
    reproductor.play().then(() => marcar(boton, true), () => marcar(boton, false));
  }
  reproductor.addEventListener("pause", () => marcar(botonActivo, false));
  reproductor.addEventListener("ended", () => marcar(botonActivo, false));

  function pintarLote() {
    const lista = $("lista");
    const fin = Math.min(pintados + LOTE, filtrados.length);
    let html = "";
    let ultimoDia = pintados > 0 ? filtrados[pintados - 1].f : null;
    let abierto = false;
    for (let i = pintados; i < fin; i++) {
      const c = filtrados[i];
      if (c.f !== ultimoDia) {
        if (abierto) html += "</ul></section>";
        html += `<section class="dia"><h2>${esc(nombreDia(c.f))}</h2><ul>`;
        abierto = true;
        ultimoDia = c.f;
      } else if (!abierto) {
        // continúa el día del lote anterior: se añade a su última lista
        const ul = lista.querySelector("section.dia:last-of-type ul");
        ul.insertAdjacentHTML("beforeend", fila(c));
        continue;
      }
      html += fila(c);
    }
    if (abierto) html += "</ul></section>";
    lista.querySelector(".centinela")?.remove();
    lista.insertAdjacentHTML("beforeend", html);
    pintados = fin;
    if (pintados < filtrados.length) {
      lista.insertAdjacentHTML("beforeend", '<div class="centinela" aria-hidden="true"></div>');
      observador.observe(lista.querySelector(".centinela"));
    }
  }

  function pintar() {
    const f = leerFiltros();
    filtrados = aplicar(f);
    pintados = 0;
    const lista = $("lista");
    lista.innerHTML = filtrados.length
      ? ""
      : `<p class="vacio">No hay conciertos con estos filtros.</p>`;
    if (filtrados.length) pintarLote();
    pintarDias(f);
    pintarChips(f);
  }

  function pintarDias(f) {
    const hoy = hoyISO();
    let html = `<button class="day" type="button" data-dia="" aria-pressed="${!f.dia}"><small>ver</small><b>Todos</b></button>`;
    for (let i = 0; i < DIAS_TIRA; i++) {
      const d = sumarDias(hoy, i);
      const etiqueta = i === 0 ? "hoy" : diaSemanaCorto(d);
      html += `<button class="day" type="button" data-dia="${d}" aria-pressed="${f.dia === d}">
        <small>${etiqueta}</small><b>${Number(d.slice(8))}</b></button>`;
    }
    $("dias").innerHTML = html;
  }

  function pintarChips(f) {
    const chips = [];
    const nombreSala = (id) => datos.salas[id]?.n || id;
    if (!f.dia && (f.desde || f.hasta)) chips.push(["fecha", `${f.desde || "…"} – ${f.hasta || "…"}`]);
    if (f.pmax !== "") chips.push(["pmax", f.pmax === "0" ? "Gratis" : `Hasta ${f.pmax} €`]);
    if (f.sinagotados) chips.push(["sinagotados", "Sin agotados"]);
    if (f.mios) chips.push(["mios", "Mis favoritos"]);
    f.barrio.forEach((b) => chips.push([`barrio:${b}`, b]));
    f.sala.forEach((s) => chips.push([`sala:${s}`, nombreSala(s)]));
    f.gen.forEach((g) => chips.push([`gen:${g}`, g]));
    $("chips").innerHTML = chips
      .map(([k, t]) => `<button class="chip" type="button" data-quitar="${esc(k)}">${esc(t)} ✕</button>`)
      .join("");
    const n = chips.length;
    $("n-filtros").hidden = !n;
    $("n-filtros").textContent = n;
    ajustarCabecera();
  }

  function ajustarCabecera() {
    document.documentElement.style.setProperty("--top-h", $("top").offsetHeight + "px");
  }

  // ---- Hoja de filtros ----------------------------------------------------
  function opciones(contenedor, nombre, valores, marcados) {
    $(contenedor).innerHTML = valores
      .map(([v, t]) => `<label><input type="checkbox" name="${nombre}" value="${esc(v)}"${marcados.includes(v) ? " checked" : ""}> ${esc(t)}</label>`)
      .join("");
  }

  function abrirFiltros() {
    const f = leerFiltros();
    const form = $("form-filtros");
    form.desde.value = f.desde;
    form.hasta.value = f.hasta;
    form.pmax.value = f.pmax;
    form.sinagotados.checked = f.sinagotados;
    form.mios.checked = f.mios;
    $("fs-mios").hidden = !mio;
    const conConciertos = new Set(datos.conciertos.map((c) => c.s));
    const salas = Object.entries(datos.salas)
      .filter(([id]) => conConciertos.has(id))
      .map(([id, s]) => [id, s.n])
      .sort((a, b) => a[1].localeCompare(b[1], "es"));
    const barrios = [...new Set(salas.map(([id]) => datos.salas[id].b).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b, "es"))
      .map((b) => [b, b]);
    const generos = [...new Set(datos.conciertos.flatMap((c) => c.gen || []))]
      .sort((a, b) => a.localeCompare(b, "es"))
      .map((g) => [g, g]);
    opciones("op-barrio", "barrio", barrios, f.barrio);
    opciones("op-sala", "sala", salas, f.sala);
    opciones("op-gen", "gen", generos, f.gen);
    $("op-gen").closest("fieldset").hidden = !generos.length;
    $("filtros").showModal();
  }

  function leerFormulario() {
    const form = $("form-filtros");
    const marcados = (n) => [...form.querySelectorAll(`input[name="${n}"]:checked`)].map((i) => i.value);
    const desde = form.desde.value;
    const hasta = form.hasta.value;
    return {
      dia: desde || hasta ? "" : leerFiltros().dia,
      desde,
      hasta,
      pmax: form.pmax.value,
      sinagotados: form.sinagotados.checked,
      mios: form.mios.checked,
      barrio: marcados("barrio"),
      sala: marcados("sala"),
      gen: marcados("gen"),
    };
  }

  // ---- Eventos ------------------------------------------------------------
  function enlazar() {
    $("abrir-filtros").addEventListener("click", abrirFiltros);
    $("filtros").addEventListener("close", () => {
      if ($("filtros").returnValue === "aplicar") {
        guardarFiltros(leerFormulario());
        pintar();
        scrollTo({ top: 0 });
      }
    });
    $("limpiar").addEventListener("click", () => {
      $("filtros").close("cerrar");
      guardarFiltros({});
      pintar();
    });
    $("dias").addEventListener("click", (e) => {
      const b = e.target.closest("[data-dia]");
      if (!b) return;
      const f = leerFiltros();
      f.dia = b.dataset.dia;
      if (f.dia) f.desde = f.hasta = "";
      guardarFiltros(f);
      pintar();
      scrollTo({ top: 0 });
    });
    $("chips").addEventListener("click", (e) => {
      const b = e.target.closest("[data-quitar]");
      if (!b) return;
      const f = leerFiltros();
      const [k, v] = b.dataset.quitar.split(/:(.*)/s);
      if (k === "fecha") f.desde = f.hasta = "";
      else if (k === "pmax") f.pmax = "";
      else if (k === "sinagotados") f.sinagotados = false;
      else if (k === "mios") f.mios = false;
      else f[k] = f[k].filter((x) => x !== v);
      guardarFiltros(f);
      pintar();
    });
    $("lista").addEventListener("click", (e) => {
      const b = e.target.closest(".escuchar");
      if (b) alternarAudio(b);
    });
    observador = new IntersectionObserver((entradas) => {
      if (entradas.some((e) => e.isIntersecting)) pintarLote();
    }, { rootMargin: "600px" });
    addEventListener("resize", ajustarCabecera);
  }

  async function iniciar() {
    enlazar();
    try {
      datos = await cargar("data/agenda.json");
    } catch (e) {
      $("lista").innerHTML = `<p class="estado">No se ha podido cargar la agenda.</p>`;
      return;
    }
    const cuando = new Date(datos.generado);
    $("pie").textContent = `Actualizado el ${cuando.toLocaleString("es-ES", { dateStyle: "medium", timeStyle: "short" })}. Datos de las webs de cada sala.`;
    pintar();
    cargarMio();
  }

  // Con sesión iniciada: favoritos para el filtro "Mis favoritos" y la marca "Vas".
  // Se carga después de pintar para que la agenda no espere a la cuenta.
  async function cargarMio() {
    if (typeof Cuenta === "undefined" || !Cuenta.activa) return;
    $("mi-cuenta").hidden = false;
    try {
      if (!(await Cuenta.usuario())) return;
      const [perfil, voy] = await Promise.all([Cuenta.perfil(), Cuenta.voyLista()]);
      mio = { salas: perfil.salas, generos: perfil.generos, voy: new Set(voy.map((v) => v.concierto_id)) };
      pintar();
    } catch (e) {
      console.warn("No se pudo cargar la cuenta", e);
    }
  }

  iniciar();
})();
