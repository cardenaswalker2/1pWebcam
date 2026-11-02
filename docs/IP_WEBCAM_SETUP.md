# Guía de Conexión y Configuración de IP Webcam

Esta guía describe el procedimiento paso a paso para transformar un teléfono móvil Android en una cámara de adquisición para el sistema de visión artificial en red local.

---

## 1. Requisitos Previos

1. **Teléfono Android**: Con cámara funcional y batería suficiente (se aconseja mantenerlo conectado al cargador durante sesiones prolongadas).
2. **Aplicación IP Webcam**: Descargada desde Google Play Store (desarrollada por Pavel Khlebovich) o repositorio de confianza.
3. **Red Wi-Fi Local**: Tanto el computador de inspección como el teléfono deben estar conectados a la **misma red Wi-Fi** o punto de acceso.
   > **Nota de Seguridad**: No active redirección de puertos (Port Forwarding) ni exponga la cámara a Internet. Toda la prueba se realiza en red de área local privada.

---

## 2. Puesta en Marcha en el Celular

1. Abra la aplicación **IP Webcam** en el teléfono.
2. Desplácese hasta la sección inferior y configure:
   - **Ajustes de video**:
     - *Resolución*: Se sugiere iniciar en `1280x720` o `1920x1080` (resoluciones mayores exigen más ancho de banda Wi-Fi).
     - *Calidad de imagen*: 70% a 85% para mantener estabilidad en FPS.
3. Presione el botón final: **"Iniciar servidor"** (Start server).
4. La pantalla del teléfono mostrará la imagen de la cámara y en la parte inferior un texto con la dirección asignada, por ejemplo:
   ```text
   http://192.168.1.100:8080
   ```
   *(La IP real variará según su router o red local).*

---

## 3. Verificación de Transmisión desde el Navegador

Antes de abrir el programa Python, verifique que la transmisión esté activa:
1. Abra un navegador (Chrome, Edge o Firefox) en la computadora.
2. Ingrese la dirección mostrada por el teléfono: `http://<IP_DE_SU_CELULAR>:8080`
3. Si carga el panel web de IP Webcam, el servidor está operando correctamente.
4. Para comprobar el flujo de video crudo decodificable por OpenCV, ingrese a:
   ```text
   http://<IP_DE_SU_CELULAR>:8080/video
   ```
   Deberá ver el video en vivo en la ventana del navegador.

---

## 4. Conexión en el Software de Inspección

1. Inicie la aplicación de visión artificial:
   ```powershell
   python src/main.py
   ```
2. En el panel lateral derecho **"CONFIGURACIÓN DE CÁMARA"**:
   - Ingrese la IP de su celular en el campo **IP / Host** (ejemplo: `192.168.1.100`).
   - Verifique el puerto (habitualmente `8080`).
   - Mantenga la ruta del stream en `/video`.
3. Presione el botón **"Probar Conexión"**:
   - El sistema ejecutará un diagnóstico de red HTTP y decodificación con OpenCV.
   - Si todo es correcto, verá un mensaje de confirmación con la resolución detectada y la latencia en milisegundos.
4. Presione **"Guardar Ajustes"** para conservar los datos para sesiones futuras.
5. Presione **"▶ Iniciar Transmisión"**:
   - El monitor central mostrará el video del teléfono en vivo sin deformar la imagen.
   - En la barra inferior verá los FPS reales capturados y la resolución nativa.

---

## 5. Diagnóstico de Problemas Comunes

| Síntoma | Causa Probable | Solución |
| :--- | :--- | :--- |
| `TIMEOUT` al probar conexión | Teléfono y PC en redes distintas o aislamiento de clientes AP | Compruebe que ambos equipos estén en la misma red Wi-Fi y desactive la opción "AP Isolation" en el router si aplica. |
| `CONNECTION_REFUSED` | El servidor de IP Webcam no está iniciado | Abra la app en el celular y presione "Iniciar servidor". |
| `OPENCV_CANNOT_OPEN` | Ruta incorrecta (se ingresó `/` en vez de `/video`) | Verifique que la ruta de flujo sea `/video` o use la casilla "Usar URL manual completa". |
| Imagen congelada o retardo alto | Saturación de la red Wi-Fi o interferencias | Reduzca la resolución de la cámara en IP Webcam (ej. a 1280x720) o aproxime el teléfono al router. |
| Firewall de Windows bloqueando | Restricción de tráfico entrante/saliente de Python | Permita el acceso de Python en las redes privadas en el Firewall de Windows Defender. |

---

## 6. Finalización Segura

1. En la aplicación, presione **"⏹ Detener"**.
2. En el teléfono, presione la opción **"Acciones..."** -> **"Detener servidor"** para liberar la cámara y conservar la batería del dispositivo.
