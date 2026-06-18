"""Parámetros analíticos (formularios de resultado) por examen del catálogo."""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.examen import Examen
from app.models.parametro_examen import ParametroExamen
from app.models.orden import Orden, Resultado
from app.services.parametros_service import parametro_clave


def _num(nombre: str, unidad: str, ref: str, orden: int = 0, decimales: int = 2) -> dict:
    return {
        "nombre": nombre,
        "tipo": "Numero",
        "unidad": unidad,
        "valor_referencia": ref,
        "decimales": decimales,
        "orden": orden,
    }


def _txt(nombre: str, ref: str = "", orden: int = 0) -> dict:
    return {"nombre": nombre, "tipo": "Texto", "valor_referencia": ref or None, "orden": orden}


def _area(nombre: str, ref: str = "", orden: int = 0) -> dict:
    return {"nombre": nombre, "tipo": "Texto Area", "valor_referencia": ref or None, "orden": orden}


def _fecha(nombre: str, orden: int = 0) -> dict:
    return {"nombre": nombre, "tipo": "Fecha", "orden": orden}


def _hora(nombre: str, orden: int = 0) -> dict:
    return {"nombre": nombre, "tipo": "Hora", "orden": orden}


PARAMETROS_POR_EXAMEN: dict[str, list[dict]] = {
    "Glucosa en Ayunas": [_num("Glucosa", "mg/dL", "70 – 100 mg/dL")],
    "Hemoglobina Glicada (HbA1c)": [_num("HbA1c", "%", "4.0 – 5.6 %")],
    "Perfil Lipídico Completo": [
        _num("Colesterol Total", "mg/dL", "< 200 mg/dL", 0),
        _num("Triglicéridos", "mg/dL", "< 150 mg/dL", 1),
        _num("HDL", "mg/dL", "> 40 mg/dL", 2),
        _num("LDL", "mg/dL", "< 100 mg/dL", 3),
        _num("VLDL", "mg/dL", "5 – 40 mg/dL", 4),
    ],
    "Creatinina": [_num("Creatinina", "mg/dL", "0.6 – 1.2 mg/dL")],
    "Urea (BUN)": [_num("Urea", "mg/dL", "15 – 40 mg/dL")],
    "Ácido Úrico": [_num("Ácido Úrico", "mg/dL", "3.5 – 7.2 mg/dL")],
    "Transaminasa GPT (ALT)": [_num("ALT (GPT)", "U/L", "7 – 56 U/L")],
    "Transaminasa GOT (AST)": [_num("AST (GOT)", "U/L", "10 – 40 U/L")],
    "Bilirrubina Total y Fracciones": [
        _num("Bilirrubina Total", "mg/dL", "0.1 – 1.2 mg/dL", 0),
        _num("Bilirrubina Directa", "mg/dL", "0.0 – 0.3 mg/dL", 1),
        _num("Bilirrubina Indirecta", "mg/dL", "0.1 – 0.9 mg/dL", 2),
    ],
    "Proteína C Reactiva (PCR)": [_num("PCR", "mg/L", "< 3.0 mg/L")],
    "Hemograma Completo": [
        _num("Hemoglobina", "g/dL", "12 – 16 g/dL", 0),
        _num("Hematocrito", "%", "36 – 48 %", 1),
        _num("Glóbulos Rojos", "mill/mm³", "4.2 – 5.4", 2),
        _num("Glóbulos Blancos", "/mm³", "4 500 – 11 000", 3),
        _num("Neutrófilos", "%", "40 – 70 %", 4),
        _num("Linfocitos", "%", "20 – 45 %", 5),
        _num("Plaquetas", "/mm³", "150 000 – 450 000", 6),
    ],
    "Grupo Sanguíneo y Factor Rh": [
        _txt("Grupo ABO", "A, B, AB u O", 0),
        _txt("Factor Rh", "Positivo o Negativo", 1),
    ],
    "VSG (Eritrosedimentación 1 hora)": [_num("VSG", "mm/h", "0 – 20 mm/h")],
    "Recuento de Plaquetas": [_num("Plaquetas", "/mm³", "150 000 – 450 000")],
    "TSH (Hormona Estimulante de Tiroides)": [_num("TSH", "µIU/mL", "0.4 – 4.0 µIU/mL")],
    "T4 Libre": [_num("T4 Libre", "ng/dL", "0.8 – 1.8 ng/dL")],
    "Prueba de Embarazo (Beta-HCG)": [
        _txt("Resultado cualitativo", "Positivo / Negativo", 0),
        _num("Beta-HCG", "mIU/mL", "< 5 mIU/mL (no embarazo)", 1),
    ],
    "Orina Completa": [
        _txt("Color", "Amarillo paja", 0),
        _txt("Aspecto", "Limpio", 1),
        _txt("Densidad", "1.005 – 1.030", 2),
        _txt("pH", "4.5 – 8.0", 3),
        _txt("Proteínas", "Negativo", 4),
        _txt("Glucosa", "Negativo", 5),
        _txt("Sedimento", "Ver microscopía", 6),
        _area("Microscopía", "0–5 leucocitos/campo; sin bacterias", 7),
    ],
    "Urocultivo": [
        _txt("Germen aislado", "Negativo / Identificar", 0),
        _area("Recuento de colonias", "Menos de 10³ UFC/mL: no significativo", 1),
        _area("Antibiograma", "Según sensibilidad", 2),
        _fecha("Fecha de toma de muestra", 3),
        _hora("Hora de toma de muestra", 4),
    ],
    "VDRL (Sífilis)": [_txt("VDRL", "No reactivo / Reactivo")],
    "HBsAg (Hepatitis B)": [_txt("HBsAg", "No reactivo")],
    "Anti-HCV (Hepatitis C)": [_txt("Anti-HCV", "No reactivo")],
    "VIH 1/2 (Elisa 4ta Generación)": [_txt("VIH 1/2", "No reactivo")],
    "Helicobacter pylori (IgG)": [_txt("Anti-H. pylori IgG", "Negativo / Positivo")],
    "PCR SARS-CoV-2 (COVID-19)": [_txt("SARS-CoV-2 PCR", "Detectado / No detectado")],
    "Examen Parasitológico Simple": [
        _area("Hallazgos", "No se observan parásitos ni huevos", 0),
        _txt("Técnica", "Directo en fresco", 1),
    ],
    "Coprocultivo": [
        _txt("Germen aislado", "Negativo", 0),
        _area("Antibiograma", "No aplica si negativo", 1),
    ],
    "Sangre Oculta en Heces": [_txt("Sangre oculta", "Negativo")],
    "Prueba de Paternidad ADN (Padre-Hijo)": [
        _txt("Índice de paternidad", "> 99.9 % probabilidad", 0),
        _area("Conclusión", "Compatibilidad genética con paternidad biológica", 1),
        _txt("Marcadores STR analizados", "21 loci", 2),
    ],
    "Prueba de Paternidad ADN (Padre-Madre-Hijo)": [
        _txt("Índice de paternidad", "> 99.9 %", 0),
        _area("Conclusión", "Compatibilidad con relación biológica padre-hijo", 1),
    ],
    "Estudio de Parentesco entre Hermanos (ADN)": [
        _txt("Índice de parentesco", "Probabilidad calculada", 0),
        _area("Conclusión", "Compatibilidad con hermandad biológica", 1),
    ],
    "Prueba de Maternidad ADN": [
        _txt("Índice de maternidad", "> 99.9 %", 0),
        _area("Conclusión", "Compatibilidad con maternidad biológica", 1),
    ],
}

ALIAS_PARAMETROS: list[tuple[str, list[dict]]] = [
    ("embarazo", PARAMETROS_POR_EXAMEN["Prueba de Embarazo (Beta-HCG)"]),
    ("vih", PARAMETROS_POR_EXAMEN["VIH 1/2 (Elisa 4ta Generación)"]),
    ("glucosa", PARAMETROS_POR_EXAMEN["Glucosa en Ayunas"]),
    ("hemograma", PARAMETROS_POR_EXAMEN["Hemograma Completo"]),
    ("leucemia", PARAMETROS_POR_EXAMEN["Hemograma Completo"]),
    ("lipídico", PARAMETROS_POR_EXAMEN["Perfil Lipídico Completo"]),
    ("lipidico", PARAMETROS_POR_EXAMEN["Perfil Lipídico Completo"]),
]


def parametros_para_nombre(nombre: str) -> list[dict] | None:
    if nombre in PARAMETROS_POR_EXAMEN:
        return PARAMETROS_POR_EXAMEN[nombre]
    nombre_lower = nombre.lower()
    for clave, params in ALIAS_PARAMETROS:
        if clave in nombre_lower:
            return params
    return None


def _parametros_para_examen(examen: Examen) -> list[dict] | None:
    return parametros_para_nombre(examen.nombre)


def aplicar_parametros_catalogo(db: Session) -> int:
    """Reemplaza parámetros genéricos por el formulario correcto de cada prueba."""
    actualizados = 0
    for examen in db.query(Examen).all():
        params = _parametros_para_examen(examen)
        if not params:
            continue
        existentes = db.query(ParametroExamen).filter(ParametroExamen.examen_id == examen.id).all()
        es_generico = len(existentes) == 1 and existentes[0].nombre in ("Resultado", "Resultado VIH")
        es_catalogo_oficial = examen.nombre in PARAMETROS_POR_EXAMEN
        if not es_generico and not es_catalogo_oficial:
            continue

        db.query(ParametroExamen).filter(ParametroExamen.examen_id == examen.id).delete()
        for i, p in enumerate(params):
            db.add(
                ParametroExamen(
                    examen_id=examen.id,
                    nombre=p["nombre"],
                    tipo=p.get("tipo", "Numero"),
                    unidad=p.get("unidad"),
                    valor_referencia=p.get("valor_referencia"),
                    decimales=p.get("decimales", 2),
                    orden=p.get("orden", i),
                )
            )
        actualizados += 1
    db.commit()
    return actualizados


def _valor_demo(param: ParametroExamen, examen_nombre: str) -> str:
    tipo = param.tipo or "Numero"
    nombre_lower = (param.nombre + " " + examen_nombre).lower()

    if tipo == "Fecha":
        return date.today().isoformat()
    if tipo == "Hora":
        return "08:30"

    if tipo == "Texto":
        if any(x in nombre_lower for x in ("vih", "hepatitis", "vdrl", "hbsag", "hcv", "covid", "sífilis", "sifilis")):
            return "No reactivo"
        if "embarazo" in nombre_lower or "hcg" in nombre_lower:
            return "Positivo"
        if "grupo" in nombre_lower and "abo" in nombre_lower:
            return "O"
        if "factor rh" in nombre_lower:
            return "Positivo"
        if "sangre oculta" in nombre_lower:
            return "Negativo"
        if "germen" in nombre_lower:
            return "Negativo"
        if "índice" in nombre_lower or "indice" in nombre_lower:
            return "99.97 %"
        if "marcadores" in nombre_lower:
            return "21 loci"
        if "color" in nombre_lower:
            return "Amarillo paja"
        if "aspecto" in nombre_lower:
            return "Limpio"
        if "proteína" in nombre_lower or "proteina" in nombre_lower:
            return "Negativo"
        if "ph" in nombre_lower:
            return "6.0"
        if "densidad" in nombre_lower:
            return "1.015"
        if "técnica" in nombre_lower or "tecnica" in nombre_lower:
            return "Directo en fresco"
        return "Normal"

    if tipo == "Texto Area":
        if "parasit" in examen_nombre.lower():
            return "No se observan parásitos ni huevos de parásitos."
        if "antibiograma" in nombre_lower:
            return "No aplica — cultivo negativo."
        if "microscopía" in nombre_lower or "microscopia" in nombre_lower:
            return "0–3 leucocitos por campo. Sin bacterias."
        if "conclusión" in nombre_lower or "conclusion" in nombre_lower:
            return "Perfiles genéticos compatibles con la relación biológica declarada."
        if "hallazgos" in nombre_lower:
            return "Sin hallazgos patológicos."
        if "recuento" in nombre_lower:
            return "< 10³ UFC/mL — no significativo."
        return "Sin observaciones relevantes."

    demos = {
        "glucosa": "92",
        "hba1c": "5.4",
        "colesterol total": "185",
        "triglicéridos": "120",
        "hdl": "52",
        "ldl": "98",
        "vldl": "26",
        "creatinina": "0.9",
        "urea": "28",
        "ácido úrico": "5.8",
        "acido urico": "5.8",
        "alt": "22",
        "gpt": "22",
        "ast": "19",
        "got": "19",
        "bilirrubina total": "0.8",
        "bilirrubina directa": "0.2",
        "bilirrubina indirecta": "0.6",
        "pcr": "1.2",
        "hemoglobina": "14.2",
        "hematocrito": "42",
        "glóbulos rojos": "4.8",
        "globulos rojos": "4.8",
        "glóbulos blancos": "7200",
        "globulos blancos": "7200",
        "neutrófilos": "58",
        "neutrofilos": "58",
        "linfocitos": "32",
        "plaquetas": "245000",
        "vsg": "12",
        "tsh": "2.1",
        "t4 libre": "1.2",
        "beta-hcg": "1250",
    }
    key = param.nombre.lower()
    for k, v in demos.items():
        if k in key:
            return v
    return "10.5"


def rellenar_resultados_demo(db: Session) -> int:
    """Rellena valores inventados en órdenes sin resultados cargados."""
    actualizados = 0
    resultados = db.query(Resultado).all()
    for res in resultados:
        vacio = not res.valor_resultado or len(res.valor_resultado) == 0
        solo_generico = (
            res.valor_resultado
            and len(res.valor_resultado) == 1
            and any("Resultado" in k for k in res.valor_resultado)
        )
        if not vacio and not solo_generico:
            continue

        examen = db.query(Examen).filter(Examen.id == res.examen_id).first()
        if not examen:
            continue
        params = (
            db.query(ParametroExamen)
            .filter(ParametroExamen.examen_id == examen.id)
            .order_by(ParametroExamen.orden)
            .all()
        )
        if not params:
            continue
        valores: dict[str, str] = {}
        for p in params:
            clave = parametro_clave(p.nombre, p.unidad)
            valores[clave] = _valor_demo(p, examen.nombre)
        res.valor_resultado = valores
        actualizados += 1
    if actualizados:
        db.commit()
    return actualizados
