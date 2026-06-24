from app.core.config import settings
from app.services import qr_service


def test_url_resultados_usa_public_site_url(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_SITE_URL", "https://genotipia-lab.com")
    url = qr_service.url_resultados_orden("abc-123")
    assert url == "https://genotipia-lab.com/resultados?codigo=ABC-123"


def test_url_resultados_fallback_sin_localhost(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_SITE_URL", "")
    monkeypatch.setattr(settings, "FRONTEND_URL", "http://localhost:4200")
    url = qr_service.url_resultados_orden("xyz")
    assert url == "https://genotipia-lab.com/resultados?codigo=XYZ"
