from utils.password import hash_password, verify_password


def test_password_round_trip() -> None:
    encoded = hash_password("secret123")
    assert encoded != "secret123"
    assert verify_password("secret123", encoded)
    assert not verify_password("wrong", encoded)
