import hashlib
import uuid

def hash(plainpass: str) -> str:
    """Generates hash of the given plain password."""
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + plainpass.encode()).hexdigest() + ":" + salt

def match(hashed: str, plain: str) -> bool:
    """Checks if the given hash matches to given plain password."""
    _hashed, salt = hashed.split(":")
    return _hashed == hashlib.sha256(salt.encode() + plain.encode()).hexdigest()