# Próximos Pasos y Hoja de Ruta

A continuación se presentan las tareas recomendadas para continuar el desarrollo del sistema de visión industrial:

---

## Prioridad 1: Validación Física de Conexión con IP Webcam
- [ ] Ejecutar la aplicación en el PC e iniciar el servidor en el teléfono Android.
- [ ] Comprobar latencia real y estabilidad de fotogramas en la red Wi-Fi de prueba.
- [ ] Ajustar la resolución óptima en la app del celular (evaluar 1080p vs 720p según fluidez).

---

## Prioridad 2: Adquisición de Dataset de Láminas
- [ ] Capturar muestras de láminas metálicas sanas usando la función de evidencia de la aplicación.
- [ ] Capturar muestras con defectos reales conocidos (rayas, abolladuras, ondulaciones irregulares, porosidades).
- [ ] Establecer una regla de escala milimétrica en el encuadre para calcular la resolución espacial real (píxeles por milímetro).

---

## Prioridad 3: Entrenamiento e Integración del Modelo
- [ ] Entrenar un modelo YOLOv8 Nano/Small con las clases de defectos identificadas o entrenar PatchCore con el dataset de láminas normales.
- [ ] Colocar los pesos resultantes en `models/yolov8_custom.pt`.
- [ ] Validar la inferencia en tiempo real y medir el consumo de GPU/CPU.

---

## Prioridad 4: Transición a Hardware Industrial
- [ ] Sustituir la conexión Wi-Fi de IP Webcam por una cámara industrial GigE Vision o USB 3.0 Vision (ej. Basler, FLIR, IDS).
- [ ] Implementar iluminación estructurada (difusa o rasante) fija para eliminar reflejos especulares de la chapa galvanizada o pintada.
