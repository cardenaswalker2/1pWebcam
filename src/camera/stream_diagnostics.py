import time
import requests
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional
from src.utils.logging_config import sanitize_url_for_logging

@dataclass
class ConnectionDiagnosis:
    success: bool
    status_message: str
    http_reachable: bool = False
    http_status_code: Optional[int] = None
    stream_opened: bool = False
    frame_received: bool = False
    width: int = 0
    height: int = 0
    latency_ms: float = 0.0
    error_code: str = ""
    recommendation: str = ""

def diagnose_stream(stream_url: str, timeout: float = 3.5) -> ConnectionDiagnosis:
    """
    Realiza un diagnóstico escalonado y real de la conexión al flujo de IP Webcam:
    1. Comprobación HTTP inicial (conectividad de red y respuesta de servidor).
    2. Apertura con OpenCV VideoCapture.
    3. Lectura y validación de fotograma real.
    4. Cálculo de latencia y dimensiones.
    """
    clean_url = stream_url.strip()
    safe_url = sanitize_url_for_logging(clean_url)
    start_time = time.time()

    if not clean_url:
        return ConnectionDiagnosis(
            success=False,
            status_message="La dirección URL del flujo está vacía.",
            error_code="URL_EMPTY",
            recommendation="Ingrese la dirección IP o la URL completa de IP Webcam (ejemplo: http://192.168.1.100:8080/video)."
        )

    # 1. Comprobación HTTP inicial
    http_reachable = False
    http_status = None
    try:
        # Se envía HEAD o GET con stream para no descargar todo el video
        resp = requests.get(clean_url, stream=True, timeout=timeout)
        http_status = resp.status_code
        http_reachable = True
        resp.close()
    except requests.exceptions.ConnectTimeout:
        return ConnectionDiagnosis(
            success=False,
            status_message="Tiempo de espera agotado al conectar al servidor.",
            http_reachable=False,
            error_code="TIMEOUT",
            latency_ms=(time.time() - start_time) * 1000.0,
            recommendation="Verifique que el teléfono y el PC estén conectados a la misma red Wi-Fi y que la IP/puerto sean correctos."
        )
    except requests.exceptions.ConnectionError as ce:
        return ConnectionDiagnosis(
            success=False,
            status_message=f"No se pudo establecer conexión de red con {safe_url}.",
            http_reachable=False,
            error_code="CONNECTION_REFUSED",
            latency_ms=(time.time() - start_time) * 1000.0,
            recommendation="Compruebe que la app IP Webcam esté activa e 'Iniciar servidor' haya sido presionado en el teléfono."
        )
    except Exception as e:
        return ConnectionDiagnosis(
            success=False,
            status_message=f"Error HTTP: {str(e)}",
            http_reachable=False,
            error_code="HTTP_ERROR",
            latency_ms=(time.time() - start_time) * 1000.0,
            recommendation="Revise el formato de la URL y asegúrese de que el protocolo sea http://."
        )

    # 2. Apertura con OpenCV VideoCapture
    cap = cv2.VideoCapture(clean_url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        # Fallback a backend predeterminado
        cap = cv2.VideoCapture(clean_url)

    if not cap.isOpened():
        return ConnectionDiagnosis(
            success=False,
            status_message="El servidor respondió por HTTP, pero OpenCV no pudo abrir el flujo de video.",
            http_reachable=http_reachable,
            http_status_code=http_status,
            stream_opened=False,
            error_code="OPENCV_CANNOT_OPEN",
            latency_ms=(time.time() - start_time) * 1000.0,
            recommendation="Asegúrese de usar la ruta de video '/video' y no la página HTML principal '/'."
        )

    # 3. Lectura de fotograma real
    ret, frame = cap.read()
    cap.release()

    latency_ms = (time.time() - start_time) * 1000.0

    if not ret or frame is None or frame.size == 0:
        return ConnectionDiagnosis(
            success=False,
            status_message="El flujo fue abierto, pero no se pudo decodificar ningún fotograma.",
            http_reachable=http_reachable,
            http_status_code=http_status,
            stream_opened=True,
            frame_received=False,
            error_code="FRAME_DECODE_FAILED",
            latency_ms=latency_ms,
            recommendation="Compruebe los ajustes de códec o resolución en la app IP Webcam de su teléfono."
        )

    h, w = frame.shape[:2]
    return ConnectionDiagnosis(
        success=True,
        status_message=f"Conexión exitosa. Flujo verificado ({w}x{h}).",
        http_reachable=http_reachable,
        http_status_code=http_status,
        stream_opened=True,
        frame_received=True,
        width=w,
        height=h,
        latency_ms=latency_ms,
        recommendation="El flujo está listo para iniciar inspección y captura."
    )
