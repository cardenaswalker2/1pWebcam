import pytest
from src.app.settings import AppSettings, CameraSettings

def test_camera_settings_default_url():
    cam = CameraSettings(ip_or_host="192.168.1.50", port=8080, stream_path="/video")
    assert cam.get_stream_url() == "http://192.168.1.50:8080/video"

def test_camera_settings_with_protocol_in_ip():
    cam = CameraSettings(ip_or_host="http://192.168.1.60", port=8080, stream_path="video")
    assert cam.get_stream_url() == "http://192.168.1.60:8080/video"

def test_camera_settings_custom_url():
    cam = CameraSettings(use_custom_url=True, custom_url="rtsp://192.168.1.99:554/live")
    assert cam.get_stream_url() == "rtsp://192.168.1.99:554/live"

def test_settings_save_and_load(tmp_path):
    config_file = str(tmp_path / "test_settings.json")
    settings = AppSettings()
    settings.camera.ip_or_host = "10.0.0.123"
    settings.camera.port = 9090
    settings.save_to_file(config_file)

    loaded = AppSettings.load_from_file(config_file)
    assert loaded.camera.ip_or_host == "10.0.0.123"
    assert loaded.camera.port == 9090
