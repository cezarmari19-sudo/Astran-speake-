import hmac
from .config import get_settings

settings = get_settings()


def verify_identity(full_id: str, display_id: str) -> bool:
    """
    Verifică că display_id sunt primele 7 caractere din full_id.
    Folosim compare_digest pentru a preveni timing attacks.
    """
    if len(full_id) != settings.full_id_length:
        return False
    expected = full_id[:settings.display_id_length]
    return hmac.compare_digest(expected, display_id)


def validate_full_id(full_id: str) -> bool:
    """Validează lungimea și caracterele permise în full_id."""
    if len(full_id) != settings.full_id_length:
        return False
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    return all(c in allowed for c in full_id)