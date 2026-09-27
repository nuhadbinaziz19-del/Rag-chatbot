from app.services.ratelimit import SlidingWindowLimiter
from app.services.security import create_token, decode_token, hash_password, verify_password


def test_password_roundtrip_including_long_bangla():
    pw = "পাসওয়ার্ড" * 20  # far beyond bcrypt's 72-byte limit
    h = hash_password(pw)
    assert verify_password(pw, h)
    assert not verify_password(pw + "x", h)


def test_verify_rejects_garbage_hash():
    assert verify_password("x", "not-a-hash") is False


def test_token_roundtrip_and_tamper_checks():
    t = create_token(42, "secret", 5)
    assert decode_token(t, "secret") == 42
    assert decode_token(t, "other-secret") is None
    assert decode_token(t + "x", "secret") is None
    assert decode_token(create_token(42, "secret", -1), "secret") is None  # expired


def test_rate_limiter_window_and_isolation():
    now = [0.0]
    lim = SlidingWindowLimiter(2, 60, clock=lambda: now[0])
    assert lim.allow("a") and lim.allow("a")
    assert not lim.allow("a")
    assert lim.allow("b")  # separate key
    now[0] = 61
    assert lim.allow("a")  # window slid
