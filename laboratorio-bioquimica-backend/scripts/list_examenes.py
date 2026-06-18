from app.db.session import SessionLocal
from app.models.examen import Examen

db = SessionLocal()
examenes = db.query(Examen).order_by(Examen.nombre).all()
print(f"{len(examenes)} examenes en BD:")
for e in examenes:
    print(f"  - {e.nombre} | destacado={e.destacado} | Bs{e.precio_bob}")
db.close()
