import uuid


def new_uuid() -> uuid.UUID:
    """Gera UUID v7 (ordenável temporalmente). Usa uuid.uuid7() do Python 3.14+."""
    if hasattr(uuid, "uuid7"):
        return uuid.uuid7()  # type: ignore[attr-defined]
    # Fallback: UUID v7 manual para Python < 3.14
    import random
    import time

    ts_ms = int(time.time() * 1000) & 0xFFFFFFFFFFFF
    rand_a = random.getrandbits(12)
    rand_b = random.getrandbits(62)
    uuid_int = (ts_ms << 80) | (0x7 << 76) | (rand_a << 64) | (0b10 << 62) | rand_b
    return uuid.UUID(int=uuid_int)
