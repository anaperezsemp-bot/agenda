// Página "Mi cuenta": entrar con un enlace al correo, elegir favoritos y ver tus conciertos.

(() => {
  const { esc, nombreDia, cargar } = Agenda;
  const raiz = document.getElementById("contenido");

  function pintarEntrada(aviso = "") {
    raiz.innerHTML = `
      <h1>Mi cuenta</h1>
      <p>Guarda tus salas y géneros favoritos, tus conciertos favoritos y los que ya tienen entrada.</p>
      <form id="entrar" class="form-cuenta">
        <label>Tu correo<input type="email" name="email" required autocomplete="email" placeholder="nombre@correo.com"></label>
        <button class="btn btn-primary" type="submit">Enviarme un enlace para entrar</button>
      </form>
      ${aviso ? `<p class="aviso">${aviso}</p>` : ""}
      <p class="nota">No hace falta contraseña: te llega un enlace al correo y al pulsarlo entras.</p>`;
    document.getElementById("entrar").addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = e.target.email.value.trim();
      const boton = e.target.querySelector("button");
      boton.disabled = true;
      try {
        await Cuenta.entrar(email);
        pintarEntrada(`Te hemos enviado un enlace a <b>${esc(email)}</b>. Ábrelo en este mismo navegador.`);
      } catch (err) {
        boton.disabled = false;
        pintarEntrada(`No se ha podido enviar el enlace: ${esc(err.message)}`);
      }
    });
  }

  function opciones(nombre, valores, marcados) {
    return valores.map(([v, t]) =>
      `<label><input type="checkbox" name="${nombre}" value="${esc(v)}"${marcados.includes(v) ? " checked" : ""}> ${esc(t)}</label>`
    ).join("");
  }

  async function pintarCuenta(usuario) {
    const [agenda, perfil, voy, fav] = await Promise.all([
      cargar("data/agenda.json"), Cuenta.perfil(), Cuenta.voyLista(), Cuenta.favLista().catch(() => []),
    ]);
    const salas = Object.entries(agenda.salas)
      .map(([id, s]) => [id, s.n])
      .sort((a, b) => a[1].localeCompare(b[1], "es"));
    const generos = [...new Set(agenda.conciertos.flatMap((c) => c.gen || []).concat(perfil.generos))]
      .sort((a, b) => a.localeCompare(b, "es"))
      .map((g) => [g, g]);
    const nombreSala = (id) => agenda.salas[id]?.n || id;
    const listaConciertos = (l, vacio) => l.length
      ? `<ul class="voy-lista">${l.map((v) => `
          <li><a class="row" href="detalle.html?id=${encodeURIComponent(v.concierto_id)}">
            <div class="info"><div class="grupo">${esc(v.titulo)}</div><div class="sala">${esc(nombreSala(v.sala))}</div></div>
            <div class="meta"><span class="hora">${esc(nombreDia(v.fecha))}</span></div></a></li>`).join("")}</ul>`
      : `<p class="nota">${vacio}</p>`;

    raiz.innerHTML = `
      <h1>Mi cuenta</h1>
      <p class="nota">Has entrado como ${esc(usuario.email)}.</p>

      <section class="bloque">
        <h2>Tengo entrada</h2>
        ${listaConciertos(voy, "Todavía no has marcado ninguno. Hazlo con el icono de entrada en el detalle de cada concierto.")}
      </section>

      <section class="bloque">
        <h2>Favoritos</h2>
        ${listaConciertos(fav, "Todavía no tienes favoritos. Márcalos con el corazón en el detalle de cada concierto.")}
      </section>

      <form id="prefs" class="bloque">
        <h2>Mis salas favoritas</h2>
        <div class="opciones">${opciones("sala", salas, perfil.salas)}</div>
        <h2>Mis géneros</h2>
        <div class="opciones">${opciones("gen", generos, perfil.generos)}</div>
        <p><button class="btn btn-primary" type="submit">Guardar favoritos</button> <span id="guardado" class="nota" role="status"></span></p>
      </form>

      <p><button class="btn" id="salir" type="button">Cerrar sesión</button></p>`;

    document.getElementById("prefs").addEventListener("submit", async (e) => {
      e.preventDefault();
      const marcados = (n) => [...e.target.querySelectorAll(`input[name="${n}"]:checked`)].map((i) => i.value);
      const estado = document.getElementById("guardado");
      try {
        await Cuenta.guardarPerfil({ salas: marcados("sala"), generos: marcados("gen") });
        estado.textContent = "Guardado.";
      } catch (err) {
        estado.textContent = "No se ha podido guardar: " + err.message;
      }
    });
    document.getElementById("salir").addEventListener("click", async () => {
      await Cuenta.salir();
      pintarEntrada();
    });
  }

  async function iniciar() {
    if (!Cuenta.activa) {
      raiz.innerHTML = `<h1>Mi cuenta</h1><p class="nota">Las cuentas todavía no están activadas.</p>`;
      return;
    }
    const usuario = await Cuenta.usuario();
    if (usuario) await pintarCuenta(usuario);
    else pintarEntrada();
  }

  iniciar();
})();
