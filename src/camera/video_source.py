import abc
from typing import Optional, Tuple
import numpy as np

class VideoSource(abc.ABC):
    """
    Interfaz abstracta para fuentes de video (cámara real IP Webcam, archivo o sintético).
    """

    @abc.abstractmethod
    def open(self) -> bool:
        """Abre la fuente de video."""
        pass

    @abc.abstractmethod
    def is_opened(self) -> bool:
        """Verifica si la fuente está abierta."""
        pass

    @abc.abstractmethod
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Lee el siguiente fotograma."""
        pass

    @abc.abstractmethod
    def release(self) -> None:
        """Libera todos los recursos asociados."""
        pass

    @abc.abstractmethod
    def get_resolution(self) -> Tuple[int, int]:
        """Retorna (ancho, alto) de la fuente."""
        pass

    @abc.abstractmethod
    def get_source_name(self) -> str:
        """Retorna el nombre o descripción de la fuente."""
        pass
