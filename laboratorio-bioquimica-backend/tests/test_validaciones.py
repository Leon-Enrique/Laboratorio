from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.ordenes import _validar_datos_factura, _validar_fecha_nacimiento


def test_fecha_nacimiento_valida():
    _validar_fecha_nacimiento(date(1990, 5, 15))


def test_fecha_nacimiento_futura_rechazada():
    futura = date.today() + timedelta(days=1)
    with pytest.raises(HTTPException) as exc:
        _validar_fecha_nacimiento(futura)
    assert exc.value.status_code == 400


def test_nit_factura_requerido_si_factura():
    with pytest.raises(HTTPException):
        _validar_datos_factura(True, "", "Empresa SA")


def test_nit_factura_valido():
    _validar_datos_factura(True, "123456789", "Genotipia SRL")


def test_sin_factura_no_valida_nit():
    _validar_datos_factura(False, None, None)
