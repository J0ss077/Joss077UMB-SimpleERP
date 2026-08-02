"""
ERP - Tienda de Tecnologia
Punto de entrada principal de la aplicacion.

Ejecucion:
    python run.py

La aplicacion se levanta en modo debug (desarrollo) en el puerto 5000.
Escucha en todas las interfaces (0.0.0.0) para ser accesible desde
el host cuando se ejecuta dentro de Docker.
"""

from app import create_app

# Crear la aplicacion usando la fabrica
app = create_app()

if __name__ == '__main__':
    # debug=True: recarga automatica al detectar cambios en el codigo
    # host='0.0.0.0': permite conexiones externas (necesario en Docker)
    app.run(debug=True, host='0.0.0.0', port=5000)
