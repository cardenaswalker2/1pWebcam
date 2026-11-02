import time
import pytest
from src.camera.synthetic_source import SyntheticSheetSource
from src.app.camera_worker import CameraWorker

def test_synthetic_source_lifecycle():
    source = SyntheticSheetSource(width=640, height=480, fps=30)
    assert not source.is_opened()

    opened = source.open()
    assert opened
    assert source.is_opened()
    assert source.get_resolution() == (640, 480)

    ret, frame = source.read()
    assert ret
    assert frame is not None
    assert frame.shape == (480, 640, 3)

    source.release()
    assert not source.is_opened()

def test_camera_worker_synthetic_integration(qtbot):
    source = SyntheticSheetSource(width=320, height=240, fps=30)
    worker = CameraWorker(source)

    frames_received = []

    def on_frame(orig, annot, res):
        frames_received.append(orig)

    worker.frame_ready.connect(on_frame)

    worker.start()
    # Esperar hasta recibir al menos 3 fotogramas
    qtbot.waitUntil(lambda: len(frames_received) >= 3, timeout=3000)

    worker.stop()
    assert not worker.isRunning()
    assert len(frames_received) >= 3
    assert frames_received[0].shape == (240, 320, 3)
