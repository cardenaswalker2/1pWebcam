import os
import json
from dataclasses import dataclass, asdict, field

@dataclass
class CameraSettings:
    ip_or_host: str = "192.168.1.100"
    port: int = 8080
    stream_path: str = "/video"
    custom_url: str = ""
    use_custom_url: bool = False
    source_mode: str = "ip_webcam"  # 'ip_webcam' o 'usb_camera'
    usb_camera_index: int = 0
    timeout_seconds: float = 3.5
    reconnect_attempts: int = 5
    reconnect_delay_seconds: float = 2.0

    def get_stream_url(self) -> str:
        """
        Retorna la URL completa normalizada para el flujo de video.
        """
        if self.use_custom_url and self.custom_url.strip():
            url = self.custom_url.strip()
            if not url.startswith("http://") and not url.startswith("https://") and not url.startswith("rtsp://"):
                url = "http://" + url
            return url

        host = self.ip_or_host.strip()
        if host.startswith("http://"):
            host = host[7:]
        elif host.startswith("https://"):
            host = host[8:]

        # Quitar trailing slashes
        host = host.rstrip("/")

        path = self.stream_path.strip()
        if not path.startswith("/"):
            path = "/" + path

        return f"http://{host}:{self.port}{path}"

@dataclass
class StorageSettings:
    evidence_dir: str = "data/evidence"
    db_path: str = "data/inspection.db"

@dataclass
class VisionSettings:
    enable_yolo: bool = True
    yolo_weights_path: str = "models/yolov8_custom.pt"
    confidence_threshold: float = 0.35
    enable_patchcore: bool = False
    patchcore_weights_path: str = "models/patchcore_weights.ckpt"
    anomaly_threshold: float = 0.50
    mm_per_pixel: float = 0.25  # Factor de calibración milimétrica (1 px = 0.25 mm)

@dataclass
class AppSettings:
    camera: CameraSettings = field(default_factory=CameraSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    vision: VisionSettings = field(default_factory=VisionSettings)

    def save_to_file(self, config_path: str = "config/settings.json") -> None:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        data = {
            "camera": asdict(self.camera),
            "storage": asdict(self.storage),
            "vision": asdict(self.vision),
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, config_path: str = "config/settings.json") -> "AppSettings":
        if not os.path.exists(config_path):
            return cls()
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            camera = CameraSettings(**data.get("camera", {}))
            storage = StorageSettings(**data.get("storage", {}))
            vision = VisionSettings(**data.get("vision", {}))
            return cls(camera=camera, storage=storage, vision=vision)
        except Exception:
            return cls()
