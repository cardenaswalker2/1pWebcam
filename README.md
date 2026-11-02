# Sistema de Visión Artificial para Inspección de Láminas Metálicas

Sistema de inspección visual y captura para control de calidad en láminas metálicas destinadas a conformado de tejas onduladas. Diseñado para pruebas y validación experimental en tiempo real utilizando un teléfono Android con **IP Webcam** como cámara de adquisición por red Wi-Fi local.

---

## Características Principales

- **Conexión Flexible a IP Webcam**: Configuración directa de IP, puerto y ruta de transmisión (`/video`), con diagnóstico de red en tiempo real.
- **Transmisión Fluida y Robusta**: Motor de captura en segundo plano con OpenCV y backend FFmpeg, desacoplado de la interfaz gráfica para evitar bloqueos.
- **Interfaz Gráfica de Grado de Ingeniería**: Construida con PySide6 en modo oscuro moderno, con monitor central que respeta la relación de aspecto y telemetría de FPS, latencia y resolución.
- **Modo Sintético para Pruebas**: Permite simular el paso de láminas metálicas para verificar toda la lógica de captura, telemetría y base de datos sin necesidad de tener el celular conectado.
- **Gestión de Evidencias de Alta Calidad**: Guardado en disco de capturas originales en resolución nativa y sin compresión destructiva, junto con imágenes anotadas.
- **Persistencia en SQLite y Revisión Humana**: Registro de sesiones, metadatos de capturas e historial con clasificación de calidad (`PASA`, `NO PASA`, `FALSA ALERTA`, `PENDIENTE`).
- **Arquitectura de Visión Desacoplada**: Adaptadores listos para Ultralytics YOLO y modelos de anomalías (PatchCore/Anomalib) con inspección estricta de pesos reales.

---

## Requisitos del Sistema

- **Sistema Operativo**: Windows 10 / 11 (64-bit)
- **Python**: 3.11 a 3.13
- **Conectividad**: Teléfono Android y PC en la misma red Wi-Fi local

---

## Instalación y Puesta en Marcha

### 1. Clonar o abrir el proyecto
Abra una consola de PowerShell en la carpeta del proyecto:
```powershell
cd c:\Users\USUARIO\Music\CASA\Ipwebcam
```

### 2. Instalar dependencias
Las dependencias requeridas son `opencv-python`, `PySide6`, `requests`, `numpy` y para pruebas `pytest`, `pytest-qt`:
```powershell
python -m pip install -e .
# o directamente:
python -m pip install opencv-python PySide6 requests numpy pytest pytest-qt
```

### 3. Ejecutar las pruebas automatizadas
```powershell
python -m pytest
```

### 4. Iniciar la aplicación
```powershell
python src/main.py
```

---

## Estructura del Repositorio

```text
Ipwebcam/
├── src/
│   ├── main.py                     # Punto de entrada de la aplicación
│   ├── app/
│   │   ├── main_window.py          # Ventana principal PySide6
│   │   ├── camera_worker.py        # Hilo QThread de adquisición desacoplada
│   │   ├── history_dialog.py       # Diálogo modal de historial y revisión humana
│   │   └── settings.py             # Configuración persistente JSON
│   ├── camera/
│   │   ├── video_source.py         # Interfaz abstracta VideoSource
│   │   ├── ip_webcam_source.py     # Captura IP Webcam mediante OpenCV/FFmpeg
│   │   ├── synthetic_source.py     # Generador sintético de láminas para pruebas
│   │   └── stream_diagnostics.py   # Diagnóstico de red, latencia y decodificación
│   ├── vision/
│   │   ├── detection_service.py    # Interfaces de detección y estructuras de datos
│   │   ├── image_processor.py      # Renderizado de contornos y división por parches
│   │   ├── yolo_adapter.py         # Adaptador para modelos YOLO
│   │   └── anomaly_adapter.py      # Adaptador preparado para PatchCore / Anomalib
│   ├── storage/
│   │   ├── database.py             # Base de datos SQLite (sesiones, evidencias, logs)
│   │   └── evidence_repository.py  # Guardado físico de capturas originales y anotadas
│   └── utils/
│       └── logging_config.py       # Registro rotativo de eventos y sanitización de URLs
├── tests/                          # 17 pruebas unitarias e integración con Pytest
├── docs/                           # Documentación técnica completa en español
│   ├── IP_WEBCAM_SETUP.md          # Guía detallada de conexión con el celular
│   ├── SYSTEM_ARCHITECTURE.md      # Diagrama y descripción de arquitectura
│   ├── TEST_PLAN.md                # Protocolo de pruebas automatizadas y manuales
│   ├── KNOWN_LIMITATIONS.md        # Análisis de defectos ≤ 1 mm y limitaciones
│   └── NEXT_STEPS.md               # Hoja de ruta técnica priorizada
├── config/                         # Ajustes de la aplicación (settings.json)
├── data/evidence/                  # Directorio de evidencias fotográficas capturadas
├── pyproject.toml                  # Declaración de proyecto y dependencias
└── README.md
```

---

## Documentación Adicional

- [**Guía Rápida de Uso Paso a Paso (Workflow)**](docs/WORKFLOW_PASO_A_PASO.md)
- [Guía de Configuración con IP Webcam](docs/IP_WEBCAM_SETUP.md)
- [Arquitectura del Sistema](docs/SYSTEM_ARCHITECTURE.md)
- [Plan de Pruebas](docs/TEST_PLAN.md)
- [Limitaciones Técnicas y Detección de Defectos de 1 mm](docs/KNOWN_LIMITATIONS.md)
- [Próximos Pasos Recomendados](docs/NEXT_STEPS.md)
