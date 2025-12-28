import hmac
import hashlib


def verify_signature(
    secret: str,
    raw_body: bytes,
    signature_hex: str | None,
) -> bool:
    if not signature_hex:
        return False

    computed = hmac.new(
        key=secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    
    return hmac.compare_digest(computed, signature_hex)
