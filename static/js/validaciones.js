/* =====================================================================
   validaciones.js — Formulario de registro de Fundación Beit Shalom

   JavaScript revisa los datos ANTES de enviarlos para dar una respuesta
   inmediata. Python vuelve a validar todo en el servidor, porque
   cualquier persona podría enviar datos sin ejecutar este código.
   ===================================================================== */
"use strict";

document.addEventListener("DOMContentLoaded", () => {

    const formulario = document.getElementById("formRegistro");

    if (!formulario) {
        return;
    }

    // Con JavaScript activo, los mensajes se muestran debajo de cada campo.
    // Sin JavaScript, el navegador aplica las validaciones nativas de HTML5.
    formulario.noValidate = true;

    // Los mismos patrones que usa Python en models/colaborador.py
    const PATRON_NOMBRE = /^[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ '.\-]*$/;
    const PATRON_CORREO = /^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/;
    const PATRON_TELEFONO = /^\+?[0-9\s()\-]{7,30}$/;

    const nombre = document.getElementById("nombre");
    const pais = document.getElementById("pais");
    const telefono = document.getElementById("telefono");
    const correo = document.getElementById("correo");
    const modalidad = document.getElementById("modalidad");
    const disponibilidad = document.getElementById("disponibilidad");
    const motivacion = document.getElementById("motivacion");
    const privacidad = document.getElementById("privacidad");
    const grupoAreas = document.getElementById("areas");
    const casillasAreas = Array.from(formulario.querySelectorAll('input[name="areas"]'));
    const contador = document.getElementById("contadorMotivacion");
    const errorFormulario = document.getElementById("errorFormulario");
    const boton = formulario.querySelector(".btn-enviar");
    const textoBoton = boton.textContent.trim();

    const MIN_NOMBRE = Number(nombre.getAttribute("minlength")) || 5;
    const MAX_NOMBRE = Number(nombre.getAttribute("maxlength")) || 150;
    const MAX_MOTIVACION = Number(motivacion.getAttribute("maxlength")) || 1000;

    /* ---------------------------------------------------------------
       Funciones de apoyo
       --------------------------------------------------------------- */

    // Quita espacios al inicio y al final, y une los espacios repetidos
    function normalizar(texto) {
        return texto.trim().replace(/\s+/g, " ");
    }

    function contarDigitos(texto) {
        return (texto.match(/\d/g) || []).length;
    }

    // Los saltos de línea cuentan como un carácter, igual que en Python
    function longitudMotivacion() {
        return motivacion.value.replace(/\r\n/g, "\n").trim().length;
    }

    /* ---------------------------------------------------------------
       Reglas, en el mismo orden en que aparecen en pantalla.
       Cada regla devuelve "" si el dato es correcto o el mensaje de error.
       --------------------------------------------------------------- */
    const reglas = [
        {
            campo: nombre,
            idError: "errorNombre",
            validar() {
                const valor = normalizar(nombre.value);
                if (valor === "") return "El nombre es obligatorio.";
                if (valor.length < MIN_NOMBRE) return "Ingresa tu nombre completo (mínimo 5 caracteres).";
                if (valor.length > MAX_NOMBRE) return "El nombre no puede superar 150 caracteres.";
                if (!PATRON_NOMBRE.test(valor)) {
                    return "El nombre solo puede contener letras, espacios, apóstrofos, puntos y guiones.";
                }
                return "";
            },
        },
        {
            campo: pais,
            idError: "errorPais",
            validar() {
                return pais.value === "" ? "Debes seleccionar un país." : "";
            },
        },
        {
            campo: telefono,
            idError: "errorTelefono",
            validar() {
                const valor = normalizar(telefono.value);
                if (valor === "") return "";   // El teléfono es opcional
                const digitos = contarDigitos(valor);
                if (!PATRON_TELEFONO.test(valor) || digitos < 7 || digitos > 15) {
                    return "Revisa el número de teléfono (solo números, espacios, +, guiones o paréntesis).";
                }
                return "";
            },
        },
        {
            campo: correo,
            idError: "errorCorreo",
            validar() {
                const valor = correo.value.trim();
                if (valor === "") return "El correo electrónico es obligatorio.";
                if (correo.validity.typeMismatch || !PATRON_CORREO.test(valor)) {
                    return "Ingresa un correo electrónico válido.";
                }
                return "";
            },
        },
        {
            campo: casillasAreas[0],
            grupo: grupoAreas,
            idError: "errorAreas",
            validar() {
                const seleccionadas = casillasAreas.filter((casilla) => casilla.checked).length;
                return seleccionadas === 0 ? "Selecciona al menos un área de colaboración." : "";
            },
        },
        {
            campo: modalidad,
            idError: "errorModalidad",
            validar() {
                return modalidad.value === "" ? "Selecciona la modalidad de colaboración." : "";
            },
        },
        {
            campo: disponibilidad,
            idError: "errorDisponibilidad",
            validar() {
                return disponibilidad.value === "" ? "Selecciona tu disponibilidad." : "";
            },
        },
        {
            campo: motivacion,
            idError: "errorMotivacion",
            validar() {
                return longitudMotivacion() > MAX_MOTIVACION
                    ? "La motivación no puede superar 1,000 caracteres."
                    : "";
            },
        },
        {
            campo: privacidad,
            grupo: privacidad.closest("label"),
            idError: "errorPrivacidad",
            validar() {
                return privacidad.checked
                    ? ""
                    : "Debes aceptar la política de privacidad para enviar la solicitud.";
            },
        },
    ];

    /* ---------------------------------------------------------------
       Mostrar u ocultar el mensaje de una regla.
       Devuelve true si el dato es válido.
       --------------------------------------------------------------- */
    function aplicar(regla) {
        const mensaje = regla.validar();
        const invalido = mensaje !== "";

        // setCustomValidity mantiene sincronizada la validación nativa del navegador
        regla.campo.setCustomValidity(mensaje);
        document.getElementById(regla.idError).textContent = mensaje;

        if (regla.grupo) {
            regla.grupo.classList.toggle("grupo-invalido", invalido);
        } else {
            regla.campo.classList.toggle("campo-invalido", invalido);
            regla.campo.classList.toggle("campo-valido", !invalido && regla.campo.value.trim() !== "");
            regla.campo.setAttribute("aria-invalid", String(invalido));
        }

        return !invalido;
    }

    // Cuando ya no quedan errores, desaparece el aviso general junto al botón
    function actualizarAvisoGeneral() {
        if (errorFormulario.textContent !== "" && reglas.every((regla) => regla.validar() === "")) {
            errorFormulario.textContent = "";
        }
    }

    /* ---------------------------------------------------------------
       Validación mientras la persona completa el formulario
       --------------------------------------------------------------- */
    reglas.forEach((regla) => {
        const elementos = regla.grupo === grupoAreas ? casillasAreas : [regla.campo];
        const esTexto = regla.campo.tagName !== "SELECT" && regla.campo.type !== "checkbox";

        // Si el servidor ya marcó este campo con un error, se revisa mientras se corrige
        regla.revisar = document.getElementById(regla.idError).textContent.trim() !== "";

        elementos.forEach((elemento) => {

            if (esTexto) {
                // Al salir del campo: se limpia el texto y se valida si tiene contenido
                elemento.addEventListener("blur", () => {
                    if (elemento !== motivacion) {
                        elemento.value = normalizar(elemento.value);
                    }
                    if (elemento.value.trim() !== "" || regla.revisar) {
                        regla.revisar = true;
                        aplicar(regla);
                        actualizarAvisoGeneral();
                    }
                });

                // Mientras escribe: el mensaje desaparece en cuanto el dato es correcto
                elemento.addEventListener("input", () => {
                    if (regla.revisar) {
                        aplicar(regla);
                        actualizarAvisoGeneral();
                    }
                });
            } else {
                elemento.addEventListener("change", () => {
                    regla.revisar = true;
                    aplicar(regla);
                    actualizarAvisoGeneral();
                });
            }

        });
    });

    /* ---------------------------------------------------------------
       Contador de caracteres de la motivación
       --------------------------------------------------------------- */
    function actualizarContador() {
        const longitud = longitudMotivacion();
        contador.textContent = `${longitud} / ${MAX_MOTIVACION} caracteres`;
        contador.classList.toggle("cerca-del-limite", longitud >= MAX_MOTIVACION * 0.9);
    }

    motivacion.addEventListener("input", actualizarContador);
    actualizarContador();

    /* ---------------------------------------------------------------
       Envío del formulario
       --------------------------------------------------------------- */
    formulario.addEventListener("submit", (evento) => {

        [nombre, telefono, correo].forEach((campo) => {
            campo.value = normalizar(campo.value);
        });

        let primerInvalido = null;

        reglas.forEach((regla) => {
            regla.revisar = true;
            if (!aplicar(regla) && primerInvalido === null) {
                primerInvalido = regla.campo;
            }
        });

        // Validar campos obligatorios restantes con la validación nativa de HTML5
        if (primerInvalido === null && !formulario.checkValidity()) {
            primerInvalido = formulario.querySelector("input:invalid, select:invalid, textarea:invalid");
        }

        // Evitar envío si hay errores
        if (primerInvalido !== null) {
            evento.preventDefault();
            errorFormulario.textContent = "Revisa los campos marcados en rojo antes de enviar la solicitud.";
            primerInvalido.focus();
            return;
        }

        // Todo correcto: se bloquea el botón para evitar un doble envío
        errorFormulario.textContent = "";
        boton.disabled = true;
        boton.classList.add("enviando");
        boton.textContent = "Enviando solicitud…";
    });

    // Si la persona regresa con el botón "Atrás", el botón vuelve a estar disponible
    window.addEventListener("pageshow", () => {
        boton.disabled = false;
        boton.classList.remove("enviando");
        boton.textContent = textoBoton;
    });

});
