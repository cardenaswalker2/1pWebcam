# FLUJO DE TRABAJO OPERATIVO (WORKFLOW) — PASO A PASO
## SISTEMA DE VISIÓN ARTIFICIAL PARA INSPECCIÓN DE LÁMINAS CON IP WEBCAM

Este documento es la **guía operativa definitiva para el usuario**. Explica de manera simple y rigurosa cómo usar el sistema desde cero, realizar capturas, validar la conexión y registrar decisiones de calidad.

---

## 🚀 PASO 1: Arrancar la Aplicación en Windows

Tienes dos formas directas de abrir el programa:

- **Opción Rápida (Recomendada):** Haz doble clic en el archivo [`iniciar_sistema.bat`](file:///c:/Users/USUARIO/Music/CASA/Ipwebcam/iniciar_sistema.bat) en la carpeta del proyecto.
- **Opción por Consola:** Abre una terminal PowerShell en la carpeta del proyecto y ejecuta:
  ```powershell
  python src/main.py
  ```

Se abrirá la ventana principal con interfaz oscura profesional titulada:
**«SISTEMA DE VISIÓN ARTIFICIAL — INSPECCIÓN DE LÁMINAS»**.

---

## 🧪 PASO 2: Prueba Inicial Rápida (Sin Celular)

Si aún no tienes el teléfono configurado o quieres verificar que todo funciona en el PC:

1. En el panel lateral derecho, busca la casilla **«Modo Sintético (Prueba sin cámara)»** y márcala ✅.
2. Verás que la insignia superior cambia a: `MODO: SIMULACIÓN SINTÉTICA`.
3. Haz clic en el botón verde **«▶ Iniciar Transmisión»**.
4. **¿Qué verás?**
   - El monitor central mostrará una simulación en vivo del avance continuo de una lámina metálica.
   - Debajo de la pantalla se actualizarán los **FPS de Captura (aprox. 25-30 FPS)**, la **Resolución (1280 x 720)** y la **Latencia**.
5. Haz clic en el botón azul **«📸 Capturar Imagen de Prueba»**.
   - Aparecerá una ventana confirmando que la evidencia fue guardada con su número de ID y su ruta física.
6. Haz clic en el botón rojo **«⏹ Detener»** para liberar los recursos.

---

## 📱 PASO 3: Conectar tu Teléfono Android con IP Webcam

Cuando vayas a inspeccionar láminas reales con la cámara de tu celular:

### A. En el Celular
1. Asegúrate de que el **computador y el celular estén conectados a la misma red Wi-Fi**.
2. Abre la app **IP Webcam** en Android.
3. Desplázate al fondo de la pantalla y pulsa **«Iniciar servidor»** (*Start server*).
4. La pantalla del celular mostrará la cámara y en la parte inferior un texto con la dirección de red. Por ejemplo:
   ```text
   http://192.168.1.55:8080
   ```
   *(Anota los números que salgan en tu pantalla; la IP depende de tu red).*

### B. En el Programa (Computador)
1. Desmarca la casilla **«Modo Sintético»** si estaba activa.
2. En el panel **CONFIGURACIÓN DE CÁMARA**:
   - En el campo **IP / Host**, escribe la IP de tu celular (por ejemplo: `192.168.1.55`).
   - En **Puerto**, confirma que esté en `8080`.
   - En **Ruta stream**, confirma que diga `/video`.
3. Haz clic en el botón **«Probar Conexión»**:
   - El sistema comprobará la red y la imagen en menos de 2 segundos.
   - Si todo está bien, saldrá un mensaje verde: **«Conexión exitosa. Flujo verificado»**, informándote la resolución de tu celular (ej. 1920x1080) y la latencia.
4. Haz clic en **«Guardar Ajustes»** (así no tendrás que volver a escribir la IP la próxima vez).
5. Haz clic en **«▶ Iniciar Transmisión»**:
   - La insignia superior pasará a `CÁMARA: CONECTADA` en color verde.
   - Verás el video de la lámina en tiempo real en la pantalla central, con su proporción nativa exacta sin deformación.

---

## 📸 PASO 4: Capturar Evidencias de Defectos o Zonas Sospechosas

Durante la inspección de la lámina:

1. Cuando la cámara apunte a una zona que quieras registrar (una raya, una abolladura, un poro o una lámina en buen estado), haz clic en:
   **«📸 Capturar Imagen de Prueba»**.
2. El sistema guarda automáticamente:
   - La imagen original en alta resolución sin comprimir en: `data/evidence/YYYY-MM-DD/evidencia_..._orig.png`.
   - Si hubiera detecciones de modelos, una copia anotada `..._annot.png`.
   - Los metadatos completos en la base de datos local SQLite (`data/inspection.db`).

---

## 📋 PASO 5: Revisión de Calidad Humana e Historial

Para auditar lo inspeccionado y emitir el veredicto técnico:

1. Haz clic en el botón **«📋 Ver Historial y Revisiones»**.
2. Se abrirá la ventana de historial con:
   - La lista completa de capturas realizadas, con fecha, hora, resolución y estado.
3. Haz clic sobre cualquier fila de la lista:
   - A la derecha se cargará la imagen capturada para que puedas inspeccionarla en detalle.
4. En el panel inferior derecho **«Decisión de Calidad (Revisión Humana)»**:
   - Selecciona el veredicto: `PASA`, `NO PASA`, `FALSA ALERTA` o `PENDIENTE`.
   - En el cuadro de texto escribe tus observaciones técnicas (por ejemplo: *"Se observa marca longitudinal de rodillo en extremo izquierdo"*).
   - Haz clic en **«Guardar Decisión de Revisión»**.
5. Esta decisión queda registrada permanentemente en la base de datos SQLite y no se pierde al cerrar la aplicación.

---

## 🛑 PASO 6: Finalizar la Jornada de Inspección

1. En el programa, haz clic en **«⏹ Detener»**.
2. Cierra la ventana del programa.
3. En el teléfono celular, pulsa **«Acciones...»** -> **«Detener servidor»** para apagar la cámara y ahorrar batería.

---

## 🔧 Solución Rápida de Dudas Frecuentes

- **¿Qué pasa si «Probar Conexión» da error TIMEOUT?**
  Verifica que el celular y el PC estén en la misma red Wi-Fi y que no tengas una red de invitados que aísle dispositivos.
- **¿Por qué dice "DETECTOR: NO DISPONIBLE"?**
  Porque actualmente no hay un archivo de pesos `.pt` entrenado colocado en `models/yolov8_custom.pt`. El sistema no inventa detecciones falsas. Al agregar un modelo entrenado, se habilitará automáticamente.
- **¿Dónde están mis fotos guardadas?**
  Haz clic en el botón **«📁 Abrir Carpeta de Evidencias»** del panel lateral y se abrirá directamente el explorador de Windows en la carpeta correspondiente.
