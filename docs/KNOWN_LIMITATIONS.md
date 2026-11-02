# Limitaciones Conocidas y Análisis de Riesgos Técnicos

---

## 1. Detección de Defectos Milimétricos (≤ 1 mm)

> [!WARNING]
> En la etapa actual con IP Webcam **no se puede garantizar ni certificar la detección de defectos de 1 mm o menores**.

### Razones Técnicas:
1. **Resolución Espacial (mm/pixel)**: Para detectar un defecto de 1 mm con confianza estadística (requiere al menos 3 a 5 píxeles por defecto), si la lámina mide 1000 mm de ancho, se requeriría una cámara de al menos 3000 a 5000 píxeles horizontales (cámara lineal o matricial industrial de 4K-8K).
2. **Compresión MJPEG/H.264**: La transmisión por Wi-Fi de IP Webcam utiliza compresión con pérdida, lo que genera artefactos de cuantización que suelen borrar o difuminar grietas o abolladuras milimétricas.
3. **Óptica y Enfoque del Celular**: La lente fija de un teléfono inteligente tiene distorsión de barril y autofoco dinámico no reproducible, inadecuado para metrología industrial.
4. **Iluminación Industrial**: Defectos en láminas metálicas brillantes requieren iluminación rasante estructurada o iluminación difusa tipo domo/campo oscuro para revelar relieves sin generar deslumbramientos cegadores.

---

## 2. Dependencia de la Calidad de la Red Wi-Fi

- La estabilidad de los FPS depende de la congestión del canal Wi-Fi local y la distancia al router.
- En caso de alta saturación, pueden perderse fotogramas. El software maneja esto descartando fotogramas antiguos para mantener la transmisión en tiempo real.

---

## 3. Estado de los Modelos de Visión Artificial

- **YOLO**: El software incluye el adaptador desacoplado para Ultralytics YOLO. Si no se colocan pesos preentrenados en `models/yolov8_custom.pt`, el detector se mantiene como "No disponible".
- **PatchCore / Anomalib**: El adaptador está listo estructuralmente. Requiere un dataset de entrenamiento de láminas sin defectos bajo condiciones de iluminación constantes para generar el banco de memoria de incrustaciones (*embeddings*).
- **Prohibición de Falsos Resultados**: El sistema no genera cajas de detección ni mapas de calor ficticios para aparentar funcionamiento.

---

## 4. Rechazo Automático en Línea

- Esta versión es un **prototipo de experimentación y validación**.
- Bajo ninguna circunstancia debe conectarse a actuadores de descarte o expulsión física en línea de producción hasta completar la validación estadística con piezas patrón certificadas.
