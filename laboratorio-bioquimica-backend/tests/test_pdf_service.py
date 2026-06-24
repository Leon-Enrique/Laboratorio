"""Smoke test: generación de informe PDF sin NameError."""
from datetime import date, datetime, timezone
from types import SimpleNamespace

from app.services.pdf_service import generar_informe_orden, ruta_informe


def _orden_minima():
    paciente = SimpleNamespace(
        nombre="Carlos",
        apellido="Perez",
        dni="1234567",
        fecha_nacimiento=date(1990, 5, 15),
        id=1,
    )
    examen = SimpleNamespace(
        nombre="Glucosa",
        parametros=[
            SimpleNamespace(
                nombre="Glucosa",
                unidad="mg/dL",
                tipo="Numero",
                valor_min=70.0,
                valor_max=100.0,
                valor_referencia=None,
                orden=1,
            )
        ],
    )
    resultado = SimpleNamespace(
        examen=examen,
        valor_resultado={"Glucosa": "95"},
    )
    orden = SimpleNamespace(
        codigo_orden="TEST-PDF-001",
        paciente=paciente,
        medico_solicitante="Dr. Prueba",
        fecha_creacion=datetime.now(timezone.utc),
        fecha_completado=datetime.now(timezone.utc),
        resultados=[resultado],
    )
    return orden


def test_generar_informe_orden_smoke(tmp_path, monkeypatch):
    reports = tmp_path / "reports"
    reports.mkdir()
    monkeypatch.setattr(
        "app.services.pdf_service._reports_dir",
        lambda: str(reports),
    )

    path = generar_informe_orden(_orden_minima(), "Bioquímico Demo")

    assert path == ruta_informe("TEST-PDF-001")
    assert reports.joinpath("TEST-PDF-001.pdf").is_file()
    assert reports.joinpath("TEST-PDF-001.pdf").stat().st_size > 500
