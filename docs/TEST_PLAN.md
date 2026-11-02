# Plan de Pruebas y Validación del Software

Este documento define la estrategia de pruebas automatizadas y las comprobaciones operativas manuales para la integración con IP Webcam.

---

## 1. Pruebas Automatizadas (Pytest)

Las pruebas automatizadas están diseñadas para ejecutarse de forma independiente en entornos de integración continua o localmente sin requerir hardware físico conectado:

| Módulo de Prueba | Componente Evaluado | Casos Verificados |
| :--- | :--- | :--- |
| `tests/test_settings.py` | Configuración | Generación de URL normalizada con IP o host, tratamiento de protocolos, URL personalizada completa y persistencia JSON. |
| `tests/test_database.py` | Persistencia SQLite | Creación automática de tablas, registro de sesiones, guardado de evidencias y actualización de decisión humana. |
| `tests/test_evidence_repository.py` | Almacenamiento en Disco | Escritura física de archivos PNG, dimensiones reales, carpetas por fecha y rechazo de matrices vacías. |
| `tests/test_diagnostics.py` | Diagnóstico de Flujo | Detección de URL vacía, manejo controlado de timeouts o conexiones rechazadas y emisión de recomendaciones. |
| `tests/test_vision.py` | Adaptadores de Visión | Comportamiento seguro ante ausencia de pesos YOLO/PatchCore, no alteración del fotograma original y partición de parches. |
| `tests/test_camera_worker.py` | Concurrencia PySide6 | Ciclo de vida del `SyntheticSheetSource` e integración en segundo plano con `CameraWorker` vía `pytest-qt`. |

### Ejecución de Pruebas Automatizadas
```powershell
python -m pytest
```

---

## 2. Pruebas Manuales con IP Webcam (Hardware Real)

Una vez disponible el teléfono celular en la red Wi-Fi, se deben verificar los siguientes casos manuales:

1. **Prueba de Conexión Fallida Intencional**:
   - Ingresar una IP errónea (ej. `192.168.1.254`).
   - Presionar "Probar Conexión".
   - **Resultado esperado**: Ventana informativa con error `TIMEOUT` o `CONNECTION_REFUSED` sin colgar la GUI.

2. **Prueba de Conexión Exitosa**:
   - Ingresar la IP real proporcionada por la app IP Webcam.
   - Presionar "Probar Conexión".
   - **Resultado esperado**: Detección de resolución real (ej. 1920x1080 o 1280x720) y latencia menor a 150 ms.

3. **Prueba de Transmisión Continua**:
   - Presionar "▶ Iniciar Transmisión".
   - **Resultado esperado**: Fluidez de video en el monitor central, tasa de FPS actualizada en tiempo real y aspecto de imagen sin distorsión.

4. **Prueba de Desconexión Abrupta**:
   - Durante la transmisión, desactivar el Wi-Fi del celular o detener el servidor en la app.
   - **Resultado esperado**: El programa detecta la interrupción tras intentos controlados, notifica al operador en la barra de estado y permite reiniciar sin reiniciar el sistema operativo.

5. **Prueba de Captura y Revisión**:
   - Capturar una imagen con "📸 Capturar Imagen de Prueba".
   - Abrir el historial ("📋 Ver Historial y Revisiones").
   - Seleccionar la imagen y registrar la decisión "PASA" o "NO PASA" con observaciones.
   - Reiniciar el software y comprobar que la decisión y la imagen permanecen intactas.
