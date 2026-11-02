import pytest
from src.camera.stream_diagnostics import diagnose_stream, ConnectionDiagnosis

def test_diagnose_empty_url():
    diag = diagnose_stream("")
    assert not diag.success
    assert diag.error_code == "URL_EMPTY"
    assert "vacía" in diag.status_message

def test_diagnose_unreachable_ip():
    # IP no enrutable o fuera de servicio local para verificar manejo de timeout o connection error
    diag = diagnose_stream("http://192.0.2.1:8080/video", timeout=0.8)
    assert not diag.success
    assert diag.error_code in ["TIMEOUT", "CONNECTION_REFUSED", "HTTP_ERROR"]
    assert len(diag.recommendation) > 0
