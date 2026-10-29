// URL base de la API de Pokémon
const API_URL = "https://pokeapi.co/api/v2/pokemon";
const POR_PAGINA = 20;

let paginaActual = 0;

// Referencias al DOM
const formBusqueda = document.getElementById("form-busqueda");
const entrada = document.getElementById("entrada");
const btnAleatorio = document.getElementById("btn-aleatorio");
const mensaje = document.getElementById("mensaje");
const detalle = document.getElementById("detalle");
const lista = document.getElementById("lista");
const btnAnterior = document.getElementById("btn-anterior");
const btnSiguiente = document.getElementById("btn-siguiente");
const etiquetaPagina = document.getElementById("pagina");

// Muestra un mensaje normal o de error
function mostrarMensaje(texto, esError = false) {
  mensaje.textContent = texto;
  mensaje.className = esError ? "error" : "";
}

// Solicitud GET: devuelve el JSON o lanza un error
async function pedirDatos(url) {
  const respuesta = await fetch(url);
  console.log("Estado de la respuesta:", respuesta.status);

  if (!respuesta.ok) {
    throw new Error(
      respuesta.status === 404 ? "No se encontró ese Pokémon" : "Error al consultar la API"
    );
  }
  return respuesta.json();
}

// Busca un Pokémon por nombre o número y muestra su detalle
async function buscarPokemon(consulta) {
  try {
    mostrarMensaje("Buscando...");
    const datos = await pedirDatos(`${API_URL}/${String(consulta).toLowerCase().trim()}`);
    console.log("Datos recibidos:", datos);
    mostrarDetalle(datos);
    mostrarMensaje("");
  } catch (error) {
    console.log("Error:", error.message);
    detalle.classList.add("oculto");
    mostrarMensaje(error.message, true);
  }
}

// Pinta el detalle de un Pokémon
function mostrarDetalle(p) {
  const imagen = p.sprites.other["official-artwork"].front_default || p.sprites.front_default;
  const tipos = p.types.map(t => `<span class="tipo">${t.type.name}</span>`).join("");
  const estadisticas = p.stats.map(s => `
    <div class="stat">
      <span>${s.stat.name}</span>
      <div class="barra"><div style="width:${Math.min(s.base_stat, 150) / 1.5}%"></div></div>
      <span>${s.base_stat}</span>
    </div>`).join("");

  detalle.innerHTML = `
    <img src="${imagen}" alt="${p.name}">
    <div>
      <h2>#${p.id} ${p.name}</h2>
      <p>${tipos}</p>
      <p>Altura: ${p.height / 10} m | Peso: ${p.weight / 10} kg</p>
      <h3>Estadísticas</h3>
      ${estadisticas}
    </div>`;
  detalle.classList.remove("oculto");
  detalle.scrollIntoView({ behavior: "smooth" });
}

// Carga una página de la lista de Pokémon
async function cargarLista() {
  try {
    lista.innerHTML = "";
    mostrarMensaje("Cargando lista...");
    const offset = paginaActual * POR_PAGINA;
    const datos = await pedirDatos(`${API_URL}?limit=${POR_PAGINA}&offset=${offset}`);

    datos.results.forEach(item => {
      // La URL termina en /{id}/, de ahí sacamos el número
      const id = item.url.split("/").filter(Boolean).pop();
      const tarjeta = document.createElement("article");
      tarjeta.className = "tarjeta";
      tarjeta.innerHTML = `
        <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${id}.png"
             alt="${item.name}" loading="lazy">
        <h3>${item.name}</h3>
        <small>#${id}</small>`;
      tarjeta.addEventListener("click", () => buscarPokemon(id));
      lista.appendChild(tarjeta);
    });

    etiquetaPagina.textContent = `Página ${paginaActual + 1}`;
    btnAnterior.disabled = paginaActual === 0;
    btnSiguiente.disabled = !datos.next;
    mostrarMensaje("");
  } catch (error) {
    console.log("Error:", error.message);
    mostrarMensaje(error.message, true);
  }
}

// Eventos
formBusqueda.addEventListener("submit", e => {
  e.preventDefault();
  buscarPokemon(entrada.value);
});

btnAleatorio.addEventListener("click", () => {
  const id = Math.floor(Math.random() * 1025) + 1;
  buscarPokemon(id);
});

btnAnterior.addEventListener("click", () => { paginaActual--; cargarLista(); });
btnSiguiente.addEventListener("click", () => { paginaActual++; cargarLista(); });

// Al iniciar
cargarLista();