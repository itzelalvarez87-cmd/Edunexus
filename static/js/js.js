let avatarElegido = "🐱";
let jugadorActual = null;
let preguntaActual = 0;
let juegoActual = "";

const bancoPreguntas = {
    algebra: [
        { p: "Si 2x + 4 = 10, ¿cuánto vale x?", r: ["x = 3", "x = 2", "x = 5"], c: 0 },
        { p: "Si x - 5 = 12, ¿cuánto vale x?", r: ["x = 17", "x = 7", "x = 10"], c: 0 }
    ],
    fracciones: [
        { p: "¿Cuánto es 1/2 + 1/4?", r: ["3/4", "2/6", "1/8"], c: 0 },
        { p: "¿Cuál es la fracción equivalente a 2/4?", r: ["1/2", "3/4", "4/2"], c: 0 }
    ],
    operaciones: [
        { p: "¿Cuánto es 5 + 3 x 2?", r: ["11", "16", "10"], c: 0 },
        { p: "¿Cuánto es (8 - 2) / 2?", r: ["3", "4", "2"], c: 0 }
    ],
    pitagoras: [
        { p: "En un triángulo rectángulo con catetos 3 y 4, ¿cuánto mide la hipotenusa?", r: ["5", "7", "6"], c: 0 }
    ],
    articulos: [
        { p: "¿Cuál es el objetivo principal de un artículo científico?", r: ["Divulgar investigación", "Entretener", "Vender productos"], c: 0 }
    ],
    informacion: [
        { p: "¿Qué técnica ayuda a localizar datos específicos en un texto?", r: ["Lectura rápida (Scanning)", "Memorización", "Escribir un resumen"], c: 0 }
    ],
    ideas: [
        { p: "¿Qué resume el contenido principal de un párrafo?", r: ["La idea principal", "La idea secundaria", "El título"], c: 0 }
    ],
    ortografia: [
        { p: "¿Cuál palabra lleva tilde correctamente?", r: ["Canción", "Cancion", "Cáncion"], c: 0 }
    ]
};

function obtenerCuentas() {
    return JSON.parse(localStorage.getItem("cuentasAprendeMas") || "{}");
}

function guardarCuentas(cuentas) {
    localStorage.setItem("cuentasAprendeMas", JSON.stringify(cuentas));
}

function mostrarFormulario(tipo) {
    document.getElementById("formLogin").classList.toggle("oculto", tipo !== "login");
    document.getElementById("formRegistro").classList.toggle("oculto", tipo !== "registro");
    document.getElementById("pestanaLogin").classList.toggle("activa", tipo === "login");
    document.getElementById("pestanaRegistro").classList.toggle("activa", tipo === "registro");
}

function elegirAvatar(btn) {
    document.querySelectorAll(".avatar-opcion").forEach(b => b.classList.remove("seleccionado"));
    btn.classList.add("seleccionado");
    avatarElegido = btn.dataset.avatar;
}

function registrarUsuario(e) {
    e.preventDefault();
    const nombre = document.getElementById("registroNombre").value.trim();
    const clave = document.getElementById("registroClave").value;
    const correo = document.getElementById("registroCorreo").value.trim();
    const cuentas = obtenerCuentas();

    if (cuentas[nombre]) {
        document.getElementById("mensajeRegistro").innerText = "El usuario ya existe.";
        return;
    }

    cuentas[nombre] = { clave, correo, avatar: avatarElegido, puntos: 0, aciertos: 0, retos: 0, nivel: 1 };
    guardarCuentas(cuentas);
    document.getElementById("mensajeRegistro").innerText = "¡Cuenta creada con éxito! Ya puedes iniciar sesión.";
    document.getElementById("formRegistro").reset();
    mostrarFormulario("login");
}

function iniciarSesion(e) {
    e.preventDefault();
    const nombre = document.getElementById("loginUsuario").value.trim();
    const clave = document.getElementById("loginClave").value;
    const cuentas = obtenerCuentas();

    if (cuentas[nombre] && cuentas[nombre].clave === clave) {
        jugadorActual = nombre;
        cargarDatosUsuario();
        document.getElementById("pantallaAcceso").classList.add("oculto");
        document.getElementById("aplicacion").style.display = "block";
        document.getElementById("formLogin").reset();
        document.getElementById("mensajeLogin").innerText = "";
    } else {
        document.getElementById("mensajeLogin").innerText = "Usuario o contraseña incorrectos.";
    }
}

function cargarDatosUsuario() {
    const cuentas = obtenerCuentas();
    const datos = cuentas[jugadorActual];

    document.getElementById("nombreJugador").innerText = jugadorActual;
    document.getElementById("avatarGrande").innerText = datos.avatar;
    document.getElementById("usuarioHeader").innerText = datos.avatar;
    document.getElementById("puntos").innerText = datos.puntos;
    document.getElementById("aciertos").innerText = datos.aciertos;
    document.getElementById("retos").innerText = datos.retos;
    document.getElementById("nivel").innerText = Math.floor(datos.puntos / 50) + 1;
}

function cerrarSesion() {
    jugadorActual = null;
    document.getElementById("pantallaAcceso").classList.remove("oculto");
    document.getElementById("aplicacion").style.display = "none";
    cerrarJuego();
}

function iniciarJuego(juego) {
    if (!bancoPreguntas[juego]) return;
    juegoActual = juego;
    preguntaActual = 0;
    document.getElementById("zonaJuego").classList.remove("oculto");
    cargarPregunta();
}

function cargarPregunta() {
    const lista = bancoPreguntas[juegoActual];
    if (preguntaActual >= lista.length) {
        document.getElementById("resultado").innerText = "🎉 ¡Has completado este reto!";
        document.getElementById("respuestas").innerHTML = "";
        actualizarEstadisticasReto();
        return;
    }

    const data = lista[preguntaActual];
    document.getElementById("tituloJuego").innerText = `🎯 Reto: ${juegoActual.toUpperCase()}`;
    document.getElementById("pregunta").innerText = data.p;
    document.getElementById("resultado").innerText = "";

    const contenedor = document.getElementById("respuestas");
    contenedor.innerHTML = "";

    data.r.forEach((opcion, index) => {
        const btn = document.createElement("button");
        btn.className = "respuesta";
        btn.innerText = opcion;
        btn.type = "button";
        btn.onclick = () => verificarRespuesta(index);
        contenedor.appendChild(btn);
    });
}

function verificarRespuesta(opcionSeleccionada) {
    const data = bancoPreguntas[juegoActual][preguntaActual];
    const cuentas = obtenerCuentas();

    if (opcionSeleccionada === data.c) {
        document.getElementById("resultado").innerText = "¡Correcto! +10 Puntos 🌟";
        cuentas[jugadorActual].puntos += 10;
        cuentas[jugadorActual].aciertos += 1;
    } else {
        document.getElementById("resultado").innerText = "Incorrecto. ¡Sigue intentándolo! 💪";
    }

    guardarCuentas(cuentas);
    cargarDatosUsuario();
}

function siguientePregunta() {
    const lista = bancoPreguntas[juegoActual];
    if (preguntaActual < lista.length - 1) {
        preguntaActual++;
        cargarPregunta();
    } else {
        document.getElementById("resultado").innerText = "¡Fin del reto! Elige otra categoría.";
    }
}

function actualizarEstadisticasReto() {
    const cuentas = obtenerCuentas();
    cuentas[jugadorActual].retos += 1;
    guardarCuentas(cuentas);
    cargarDatosUsuario();
}

function cerrarJuego() {
    document.getElementById("zonaJuego").classList.add("oculto");
}