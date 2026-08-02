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

            // Sincronizar el tema con el perfil del usuario (si hay sesion)
            if (document.body.dataset.usuario === '1') {
                var datos = new URLSearchParams();
                datos.append('tema', nuevo);
                fetch('/perfil/tema', { method: 'POST', body: datos });
            }
        });
    }

    /* ===== Badge del carrito: animacion al cargar ===== */
    var badgeCarrito = document.getElementById('carritoBadge');
    if (badgeCarrito) {
        badgeCarrito.style.animation = 'none';
        void badgeCarrito.offsetWidth;
        badgeCarrito.style.animation = '';
    }

    /* ===== Efecto ripple en botones ===== */
    document.querySelectorAll('.btn').forEach(function (boton) {
        boton.addEventListener('click', function (evento) {
            var rect = boton.getBoundingClientRect();
            var tamano = Math.max(rect.width, rect.height);
            var ondulacion = document.createElement('span');
            ondulacion.className = 'ripple';
            if (boton.classList.contains('btn-outline-secondary') ||
                    boton.classList.contains('btn-warning') ||
                    boton.classList.contains('btn-light')) {
                ondulacion.classList.add('ripple-oscura');
            }
            ondulacion.style.width = tamano + 'px';
            ondulacion.style.height = tamano + 'px';
            ondulacion.style.left = (evento.clientX - rect.left - tamano / 2) + 'px';
            ondulacion.style.top = (evento.clientY - rect.top - tamano / 2) + 'px';
            boton.appendChild(ondulacion);
            setTimeout(function () {
                ondulacion.remove();
            }, 650);
        });
    });

    /* ===== Navbar dinamica: sombra + ocultar al bajar, mostrar al subir ===== */
    var navbar = document.querySelector('.navbar');
    if (navbar) {
        var ultimoScroll = 0;
        window.addEventListener('scroll', function () {
            var y = window.scrollY;
            navbar.classList.toggle('navbar-scrolled', y > 10);
            if (y > 90 && y > ultimoScroll) {
                navbar.classList.add('nav-oculta');
            } else {
                navbar.classList.remove('nav-oculta');
            }
            ultimoScroll = y;
        }, { passive: true });
    }

    /* ===== Resaltar el enlace de la pagina actual ===== */
    var rutaActual = window.location.pathname;
    document.querySelectorAll('.navbar .nav-link[href]').forEach(function (enlace) {
        var urlEnlace = new URL(enlace.href, window.location.origin);
        if (urlEnlace.pathname === rutaActual ||
                (urlEnlace.pathname.length > 1 && rutaActual.startsWith(urlEnlace.pathname))) {
            enlace.classList.add('active');
        }
    });

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

    /* ===== Contadores animados del portal (stats de la tienda) ===== */
    document.querySelectorAll('.stat-num[data-contador]').forEach(function (el) {
        var objetivo = parseInt(el.getAttribute('data-contador'), 10);
        if (isNaN(objetivo)) return;

        var duracion = 1100;
        var inicio = performance.now();

        function pasoStats(ahora) {
            var progreso = Math.min((ahora - inicio) / duracion, 1);
            var suavizado = 1 - Math.pow(1 - progreso, 3);
            el.textContent = Math.round(objetivo * suavizado).toLocaleString('es-CO');
            if (progreso < 1) requestAnimationFrame(pasoStats);
        }
        requestAnimationFrame(pasoStats);
    });
})();
