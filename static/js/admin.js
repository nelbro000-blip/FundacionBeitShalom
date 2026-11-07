/* =====================================================================
   admin.js — Interacciones del panel administrativo
   Toda la seguridad se valida en Python; este archivo solo mejora la
   experiencia de uso.
   ===================================================================== */
"use strict";

document.addEventListener("DOMContentLoaded", () => {

    /* 1. Confirmar acciones que no se pueden deshacer (eliminar datos) */
    document.querySelectorAll("form[data-confirmar]").forEach((formulario) => {
        formulario.addEventListener("submit", (evento) => {
            if (!window.confirm(formulario.dataset.confirmar)) {
                evento.preventDefault();
            }
        });
    });

    /* 2. Evaluación: un rechazo siempre debe indicar el motivo */
    const formEvaluacion = document.getElementById("formEvaluacion");

    if (formEvaluacion) {
        const comentario = document.getElementById("comentario");
        const errorComentario = document.getElementById("errorComentario");
        const MINIMO_MOTIVO = 10;
        let enviado = false;

        formEvaluacion.addEventListener("submit", (evento) => {
            const boton = evento.submitter;

            if (enviado) {
                evento.preventDefault();
                return;
            }

            if (boton && boton.value === "Rechazado" && comentario.value.trim().length < MINIMO_MOTIVO) {
                evento.preventDefault();
                errorComentario.textContent = "Indica el motivo del rechazo (mínimo 10 caracteres).";
                comentario.classList.add("campo-invalido");
                comentario.setAttribute("aria-invalid", "true");
                comentario.focus();
                return;
            }

            enviado = true;   // evita que un doble clic envíe el cambio dos veces
        });

        comentario.addEventListener("input", () => {
            if (comentario.value.trim().length >= MINIMO_MOTIVO) {
                errorComentario.textContent = "";
                comentario.classList.remove("campo-invalido");
                comentario.removeAttribute("aria-invalid");
            }
        });

        window.addEventListener("pageshow", () => {
            enviado = false;
        });
    }

    /* 3. Filtros: al elegir una opción se aplica la búsqueda */
    document.querySelectorAll("select[data-autoenvio]").forEach((lista) => {
        lista.addEventListener("change", () => {
            lista.form.requestSubmit();
        });
    });

    // Los filtros vacíos no se envían, así la dirección queda limpia (?estado=Aprobado)
    document.querySelectorAll("form.filtros").forEach((formulario) => {
        const campos = formulario.querySelectorAll("input, select");
        formulario.addEventListener("submit", () => {
            campos.forEach((campo) => {
                campo.disabled = campo.value.trim() === "";
            });
        });
        window.addEventListener("pageshow", () => {
            campos.forEach((campo) => {
                campo.disabled = false;
            });
        });
    });

    /* 4. Tooltips de los gráficos (con el ratón y con el teclado) */
    const tooltip = document.getElementById("tooltipGrafico");

    if (tooltip) {
        const MARGEN = 14;

        function posicionar(x, y) {
            let izquierda = x + MARGEN;
            let arriba = y - tooltip.offsetHeight - MARGEN;

            if (izquierda + tooltip.offsetWidth > window.innerWidth - 8) {
                izquierda = x - tooltip.offsetWidth - MARGEN;
            }
            if (arriba < 8) {
                arriba = y + MARGEN;
            }
            tooltip.style.left = `${Math.max(8, izquierda)}px`;
            tooltip.style.top = `${arriba}px`;
        }

        function mostrar(marca, x, y) {
            // textContent: los textos se insertan como datos, nunca como HTML
            const valor = document.createElement("strong");
            valor.textContent = marca.dataset.detalle;
            const etiqueta = document.createElement("span");
            etiqueta.textContent = marca.dataset.etiqueta;

            tooltip.replaceChildren(valor, etiqueta);
            tooltip.hidden = false;
            posicionar(x, y);
        }

        function ocultar() {
            tooltip.hidden = true;
        }

        document.querySelectorAll(".barra-fila, .columna").forEach((marca) => {
            marca.addEventListener("pointermove", (evento) => {
                mostrar(marca, evento.clientX, evento.clientY);
            });
            marca.addEventListener("pointerleave", ocultar);
            marca.addEventListener("focus", () => {
                const caja = marca.getBoundingClientRect();
                mostrar(marca, caja.left + caja.width / 2, caja.top);
            });
            marca.addEventListener("blur", ocultar);
        });

        document.addEventListener("keydown", (evento) => {
            if (evento.key === "Escape") {
                ocultar();
            }
        });
        window.addEventListener("scroll", ocultar, { passive: true });
    }

});
