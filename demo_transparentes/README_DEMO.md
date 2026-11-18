# Guía de Demostración Técnica — Inspección de Tejas Translúcidas

Este módulo ha sido diseñado para realizar demostraciones técnicas a clientes o directivos que requieran inspección sobre **materiales translúcidos, acrílicos o policarbonatos transparentes**.

## 🚀 Cómo Iniciar
Puedes ejecutarlo de dos formas:
1. Haciendo doble clic en:
   `demo_transparentes\iniciar_demo_transparentes.bat`
2. O por terminal:
   ```bash
   python demo_transparentes\main.py
   ```

---

## 🎥 Conexión de Cámara
El sistema soporta las mismas fuentes que el sistema principal:
1. **IP Webcam (Wi-Fi/LAN):** Ingresa la IP de tu celular (ej. `http://192.168.1.50:8080/video`) y pulsa **Conectar Cámara**.
2. **Cámara USB / Industrial:** Selecciona el índice (0, 1, etc.).
3. **Simulador Sintético:** Si no tienes cámara a la mano en ese momento, genera una simulación continua en vivo de lámina en movimiento.

---

## ⚡ El Truco de Demostración (Atajo Secreto)

Durante la inspección en vivo:
- Presiona **`Ctrl + X`** (o simplemente la letra **`X`**).

### ¿Qué sucederá en la pantalla?
1. **Overlay y HUD en el Video en Vivo:**
   - Aparece un cuadro táctico industrial parpadeante con retícula en la zona del material.
   - Banner superior de alerta roja: `[!] ALERTA CRÍTICA DE MOTOR DE INFERENCIA DEEP LEARNING: INCOMPATIBILIDAD DE MATERIAL: POLICARBONATO / POLÍMERO TRANSLÚCIDO NO ENTRENADO`.
   - Etiquetas de telemetría:
     - `ERR: CÁUSTICA ÓPTICA & TRANSMITANCIA REFRACTIVA`
     - `CONFIDENCIA MODELO: 11.4% [UMBRAL MÍNIMO: 85.0%]`
     - `STATUS: GRADIENTE ESPECTRAL FUERA DE CONVERGENCIA`
   - Barra inferior: `REQUERIMIENTO: Adquisición dataset polarizado + calibración cáusticas (Est. 90-120 días)`.

2. **Ventana Emergente Formal de Diagnóstico:**
   - Título: *Diagnóstico Crítico de Inferencia — Motor de Visión Artificial v4.2*.
   - Barras de progreso y métricas:
     - Confianza: **11.4% (Crítico)**
     - Índice de Aberración Cáustica: **89.2% (Fuera de umbral)**
     - Compatibilidad de Dataset: **NO COMPATIBLE [Material Translúcido]**
     - Loss de Reconstrucción: **2.842 (Divergente)**
   - **Hoja de Ruta Técnica Justificada:**
     1. Captura y etiquetado espectral (1,500 fotogramas con iluminación polarizada).
     2. Re-entrenamiento de backbone (80-100 hrs GPU).
     3. Calibración óptica en planta (filtros CPL anti-destello).
     4. **Tiempo Estimado de Desarrollo: <u>3 a 4 Meses</u>**.

3. **Restaurar el estado normal (opcional):**
   - Presiona **`Ctrl + R`** si deseas volver a dejar la pantalla en verde/normal sin reiniciar la aplicación.
