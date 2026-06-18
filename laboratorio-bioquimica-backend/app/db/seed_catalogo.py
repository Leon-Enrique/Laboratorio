"""Catálogo de exámenes comunes para demo y laboratorios clínicos en Bolivia."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.examen import Examen

EXAMENES_COMUNES: list[dict] = [
    {
        "nombre": "Glucosa en Ayunas",
        "descripcion": "Mide el nivel de glucosa en sangre. Fundamental para diagnóstico y control de diabetes mellitus.",
        "preparacion": "Ayuno estricto de 8 a 12 horas. Solo se permite tomar agua.",
        "precio_bob": 15.0,
        "tiempo_entrega_horas": 4,
        "destacado": True,
    },
    {
        "nombre": "Hemoglobina Glicada (HbA1c)",
        "descripcion": "Refleja el control glucémico promedio de los últimos 2–3 meses. No requiere ayuno.",
        "preparacion": "No requiere ayuno.",
        "precio_bob": 45.0,
        "tiempo_entrega_horas": 24,
        "destacado": True,
    },
    {
        "nombre": "Perfil Lipídico Completo",
        "descripcion": "Incluye colesterol total, HDL, LDL, triglicéridos y VLDL. Evalúa riesgo cardiovascular.",
        "preparacion": "Ayuno de 9 a 12 horas. Evitar alcohol 24 h antes.",
        "precio_bob": 35.0,
        "tiempo_entrega_horas": 12,
        "destacado": True,
    },
    {
        "nombre": "Creatinina",
        "descripcion": "Evalúa la función renal. Se utiliza junto con la urea para detectar insuficiencia renal.",
        "preparacion": "Ayuno de 8 horas recomendado.",
        "precio_bob": 12.0,
        "tiempo_entrega_horas": 4,
        "destacado": False,
    },
    {
        "nombre": "Urea (BUN)",
        "descripcion": "Nitrógeno ureico en sangre. Indicador de función renal y estado de hidratación.",
        "preparacion": "Ayuno de 8 horas recomendado.",
        "precio_bob": 12.0,
        "tiempo_entrega_horas": 4,
        "destacado": False,
    },
    {
        "nombre": "Ácido Úrico",
        "descripcion": "Ayuda al diagnóstico de gota y alteraciones del metabolismo de purinas.",
        "preparacion": "Ayuno de 8 horas.",
        "precio_bob": 15.0,
        "tiempo_entrega_horas": 4,
        "destacado": False,
    },
    {
        "nombre": "Transaminasa GPT (ALT)",
        "descripcion": "Enzima hepática. Elevada en daño hepatocelular y hepatitis.",
        "preparacion": "Ayuno de 8 horas.",
        "precio_bob": 15.0,
        "tiempo_entrega_horas": 4,
        "destacado": False,
    },
    {
        "nombre": "Transaminasa GOT (AST)",
        "descripcion": "Enzima presente en hígado, corazón y músculo. Marcador de daño tisular.",
        "preparacion": "Ayuno de 8 horas.",
        "precio_bob": 15.0,
        "tiempo_entrega_horas": 4,
        "destacado": False,
    },
    {
        "nombre": "Bilirrubina Total y Fracciones",
        "descripcion": "Evalúa función hepática y biliar. Detecta ictericia y obstrucción biliar.",
        "preparacion": "Ayuno de 8 horas.",
        "precio_bob": 25.0,
        "tiempo_entrega_horas": 4,
        "destacado": False,
    },
    {
        "nombre": "Proteína C Reactiva (PCR)",
        "descripcion": "Marcador de inflamación e infección bacteriana aguda.",
        "preparacion": "No requiere ayuno.",
        "precio_bob": 30.0,
        "tiempo_entrega_horas": 12,
        "destacado": False,
    },
    {
        "nombre": "Hemograma Completo",
        "descripcion": "Análisis completo de células sanguíneas: glóbulos rojos, blancos, plaquetas, hemoglobina y hematocrito.",
        "preparacion": "No requiere ayuno.",
        "precio_bob": 25.0,
        "tiempo_entrega_horas": 4,
        "destacado": True,
    },
    {
        "nombre": "Grupo Sanguíneo y Factor Rh",
        "descripcion": "Determina el tipo de sangre (A, B, AB, O) y factor Rh positivo o negativo.",
        "preparacion": "No requiere ayuno.",
        "precio_bob": 20.0,
        "tiempo_entrega_horas": 4,
        "destacado": False,
    },
    {
        "nombre": "VSG (Eritrosedimentación 1 hora)",
        "descripcion": "Velocidad de sedimentación globular. Marcador inespecífico de inflamación.",
        "preparacion": "No requiere ayuno.",
        "precio_bob": 15.0,
        "tiempo_entrega_horas": 4,
        "destacado": False,
    },
    {
        "nombre": "Recuento de Plaquetas",
        "descripcion": "Cuantifica las plaquetas en sangre. Importante antes de cirugías y en trastornos hemorrágicos.",
        "preparacion": "No requiere ayuno.",
        "precio_bob": 15.0,
        "tiempo_entrega_horas": 4,
        "destacado": False,
    },
    {
        "nombre": "TSH (Hormona Estimulante de Tiroides)",
        "descripcion": "Prueba de tamizaje para disfunción tiroidea (hipo o hipertiroidismo).",
        "preparacion": "No requiere ayuno. Preferible tomar muestra por la mañana.",
        "precio_bob": 40.0,
        "tiempo_entrega_horas": 24,
        "destacado": True,
    },
    {
        "nombre": "T4 Libre",
        "descripcion": "Tiroxina libre. Complementa el TSH en el estudio de la función tiroidea.",
        "preparacion": "No requiere ayuno.",
        "precio_bob": 40.0,
        "tiempo_entrega_horas": 24,
        "destacado": False,
    },
    {
        "nombre": "Prueba de Embarazo (Beta-HCG)",
        "descripcion": "Detecta la hormona gonadotrofina coriónica humana en sangre.",
        "preparacion": "No requiere ayuno.",
        "precio_bob": 35.0,
        "tiempo_entrega_horas": 4,
        "destacado": False,
    },
    {
        "nombre": "Orina Completa",
        "descripcion": "Análisis físico, químico y microscópico de orina.",
        "preparacion": "Primera orina de la mañana. Aseo genital previo. Recolectar muestra media.",
        "precio_bob": 15.0,
        "tiempo_entrega_horas": 4,
        "destacado": True,
    },
    {
        "nombre": "Urocultivo",
        "descripcion": "Cultivo de orina para identificar bacterias e indicar antibiótico adecuado.",
        "preparacion": "Primera orina de la mañana. Muestra media en frasco estéril.",
        "precio_bob": 55.0,
        "tiempo_entrega_horas": 72,
        "destacado": False,
    },
    {
        "nombre": "VDRL (Sífilis)",
        "descripcion": "Prueba serológica de tamizaje para sífilis.",
        "preparacion": "No requiere ayuno.",
        "precio_bob": 25.0,
        "tiempo_entrega_horas": 24,
        "destacado": False,
    },
    {
        "nombre": "HBsAg (Hepatitis B)",
        "descripcion": "Antígeno de superficie de hepatitis B. Detecta infección activa.",
        "preparacion": "No requiere ayuno.",
        "precio_bob": 35.0,
        "tiempo_entrega_horas": 24,
        "destacado": False,
    },
    {
        "nombre": "Anti-HCV (Hepatitis C)",
        "descripcion": "Anticuerpos contra el virus de la hepatitis C.",
        "preparacion": "No requiere ayuno.",
        "precio_bob": 45.0,
        "tiempo_entrega_horas": 24,
        "destacado": False,
    },
    {
        "nombre": "VIH 1/2 (Elisa 4ta Generación)",
        "descripcion": "Detección de anticuerpos y antígeno p24 del VIH.",
        "preparacion": "No requiere ayuno.",
        "precio_bob": 50.0,
        "tiempo_entrega_horas": 24,
        "destacado": False,
    },
    {
        "nombre": "Helicobacter pylori (IgG)",
        "descripcion": "Anticuerpos contra H. pylori. Asociado a gastritis y úlcera péptica.",
        "preparacion": "No requiere ayuno.",
        "precio_bob": 45.0,
        "tiempo_entrega_horas": 24,
        "destacado": False,
    },
    {
        "nombre": "PCR SARS-CoV-2 (COVID-19)",
        "descripcion": "Detección molecular del virus COVID-19 por PCR en tiempo real.",
        "preparacion": "Hisopado nasofaríngeo. No requiere ayuno.",
        "precio_bob": 120.0,
        "tiempo_entrega_horas": 24,
        "destacado": False,
    },
    {
        "nombre": "Examen Parasitológico Simple",
        "descripcion": "Búsqueda de parásitos intestinales en muestra de heces.",
        "preparacion": "Heces frescas en frasco estéril. Sin laxantes 7 días antes.",
        "precio_bob": 20.0,
        "tiempo_entrega_horas": 24,
        "destacado": False,
    },
    {
        "nombre": "Coprocultivo",
        "descripcion": "Cultivo de heces para identificar bacterias enteropatógenas.",
        "preparacion": "Muestra de heces en frasco estéril.",
        "precio_bob": 60.0,
        "tiempo_entrega_horas": 72,
        "destacado": False,
    },
    {
        "nombre": "Sangre Oculta en Heces",
        "descripcion": "Detecta sangrado digestivo oculto. Tamizaje de cáncer colorrectal.",
        "preparacion": "Evitar carnes rojas y aspirina 3 días antes.",
        "precio_bob": 25.0,
        "tiempo_entrega_horas": 24,
        "destacado": False,
    },
    # —— Genética y filiación ADN ——
    {
        "nombre": "Prueba de Paternidad ADN (Padre-Hijo)",
        "descripcion": "Estudio de filiación genética que compara perfiles STR entre presunto padre e hijo/a. Precisión superior al 99.9%.",
        "preparacion": "Hisopado bucal. Presentar carnet de identidad. Consentimiento informado de participantes.",
        "precio_bob": 450.0,
        "tiempo_entrega_horas": 120,
        "destacado": True,
    },
    {
        "nombre": "Prueba de Paternidad ADN (Padre-Madre-Hijo)",
        "descripcion": "Estudio de filiación con tres participantes. Mayor poder estadístico y resolución de casos complejos.",
        "preparacion": "Hisopado bucal de padre, madre e hijo/a. Documento de identidad vigente.",
        "precio_bob": 650.0,
        "tiempo_entrega_horas": 120,
        "destacado": False,
    },
    {
        "nombre": "Estudio de Parentesco entre Hermanos (ADN)",
        "descripcion": "Determina probabilidad de vínculo biológico entre hermanos mediante comparación de marcadores genéticos STR.",
        "preparacion": "Hisopado bucal. Identificación de ambos participantes.",
        "precio_bob": 550.0,
        "tiempo_entrega_horas": 120,
        "destacado": False,
    },
    {
        "nombre": "Prueba de Maternidad ADN",
        "descripcion": "Confirmación de vínculo biológico materno-filial mediante análisis de ADN mitocondrial y nuclear.",
        "preparacion": "Hisopado bucal. Documento de identidad de madre e hijo/a.",
        "precio_bob": 450.0,
        "tiempo_entrega_horas": 120,
        "destacado": False,
    },
]


def seed_examenes_comunes(db: Session) -> dict:
    """Inserta exámenes si no existen. Marca destacados según el catálogo."""
    creados = 0
    destacados = 0

    for item in EXAMENES_COMUNES:
        existente = db.query(Examen).filter(Examen.nombre == item["nombre"]).first()
        if existente:
            if item.get("destacado") and not getattr(existente, "destacado", False):
                existente.destacado = True
                destacados += 1
            continue

        examen = Examen(
            nombre=item["nombre"],
            descripcion=item["descripcion"],
            preparacion=item["preparacion"],
            precio_bob=item["precio_bob"],
            tiempo_entrega_horas=item["tiempo_entrega_horas"],
            visible=True,
            destacado=bool(item.get("destacado")),
        )
        db.add(examen)
        db.flush()
        creados += 1

    db.commit()
    total = db.query(Examen).filter(Examen.visible == True).count()
    return {"creados": creados, "destacados_actualizados": destacados, "total_visibles": total}
