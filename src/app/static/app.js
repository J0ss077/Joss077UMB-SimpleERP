/*
 * ERP - Tienda de Tecnologia
 * JavaScript del frontend:
 *   - Cambio de tema claro/oscuro con persistencia en localStorage
 *   - Animaciones de aparicion (reveal) al hacer scroll
 *   - Contadores animados en el panel de metricas
 *   - Sombra de la barra de navegacion al hacer scroll
 */
(function () {
    'use strict';

    /* ===== Tema claro/oscuro ===== */
    var botonTema = document.getElementById('themeToggle');

    function aplicarTema(tema, guardar) {
        document.documentElement.setAttribute('data-theme', tema);
        document.documentElement.setAttribute('data-bs-theme', tema);
        if (guardar) {
            localStorage.setItem('erp-tema', tema);
        }
    }

    if (botonTema) {
        botonTema.addEventListener('click', function () {
            var actual = document.documentElement.getAttribute('data-theme');
            var nuevo = actual === 'dark' ? 'light' : 'dark';
            aplicarTema(nuevo, true);
            botonTema.classList.remove('girar');
            void botonTema.offsetWidth;
            botonTema.classList.add('girar');
        });
    }

    /* ===== Sombra del navbar al hacer scroll ===== */
    var navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', function () {
            navbar.classList.toggle('navbar-scrolled', window.scrollY > 10);
        }, { passive: true });
    }

    /* ===== Animacion reveal al hacer scroll ===== */
    var observador = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (entrada) {
            if (entrada.isIntersecting) {
                entrada.target.classList.add('is-visible');
                observador.unobserve(entrada.target);
            }
        });
    }, { threshold: 0.12 });

    document.querySelectorAll('.card, .producto-card').forEach(function (el, indice) {
        el.classList.add('reveal');
        if (el.classList.contains('producto-card') || el.classList.contains('metrica-card')) {
            el.style.transitionDelay = (indice % 3) * 90 + 'ms';
        }
        observador.observe(el);
    });

    /* ===== Contadores animados en metricas ===== */
    document.querySelectorAll('.metrica-card .valor').forEach(function (el) {
        var texto = el.textContent.trim();
        var objetivo = parseFloat(texto.replace(/[^0-9.\-]/g, ''));
        if (isNaN(objetivo)) return;

        var conDecimales = texto.indexOf('.') !== -1;
        var duracion = 900;
        var inicio = performance.now();

        function paso(ahora) {
            var progreso = Math.min((ahora - inicio) / duracion, 1);
            var suavizado = 1 - Math.pow(1 - progreso, 3);
            var valor = objetivo * suavizado;
            el.textContent = conDecimales
                ? valor.toFixed(2)
                : Math.round(valor).toLocaleString('es-CO');
            if (progreso < 1) requestAnimationFrame(paso);
        }
        requestAnimationFrame(paso);
    });
})();
