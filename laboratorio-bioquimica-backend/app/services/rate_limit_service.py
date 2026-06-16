"""Rate limiting simple en memoria para consultas públicas."""
from collections import defaultdict
from time import time

_MAX = 15
_WINDOW = 300  # 5 minutos

_attempts: dict[str, list[float]] = defaultdict(list)


def registrar_intento(client_ip: str) -> bool:
    """Registra intento. Retorna False si se excedió el límite."""
    now = time()
    _attempts[client_ip] = [t for t in _attempts[client_ip] if now - t < _WINDOW]
    if len(_attempts[client_ip]) >= _MAX:
        return False
    _attempts[client_ip].append(now)
    return True
