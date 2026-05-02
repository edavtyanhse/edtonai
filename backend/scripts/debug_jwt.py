import base64
import os

import jwt

SECRET_STR = os.environ.get("JWT_SECRET_KEY", "")


def test():
    if not SECRET_STR:
        print("Set JWT_SECRET_KEY in the environment before running this script.")
        return

    print(f"Secret string length: {len(SECRET_STR)}")

    # 1. Decode to bytes
    try:
        secret_bytes = base64.b64decode(SECRET_STR)
        print(f"Secret decodes to {len(secret_bytes)} bytes.")
    except Exception as e:
        print(f"Secret is NOT Base64: {e}")
        return

    payload = {"sub": "123", "aud": "authenticated"}

    # Simulate Supabase: Sign with BYTES
    print("\n--- Scenario A: Supabase signs with DECODED BYTES ---")
    token_bytes = jwt.encode(payload, secret_bytes, algorithm="HS256")

    # Verify with STRING (Current Code)
    try:
        jwt.decode(
            token_bytes, SECRET_STR, algorithms=["HS256"], audience="authenticated"
        )
        print("[FAIL] Current Code worked? (Unexpected if key is bytes)")
    except jwt.InvalidSignatureError:
        print("[SUCCESS] Current Code Failed (Expected behavior: Signature mismatch)")
    except Exception as e:
        print(f"[ERROR] Current Code Other Error: {e}")

    # Verify with BYTES (Proposed Fix)
    try:
        jwt.decode(
            token_bytes, secret_bytes, algorithms=["HS256"], audience="authenticated"
        )
        print("[PASS] Proposed Fix Verification Succeeded")
    except Exception as e:
        print(f"[FAIL] Proposed Fix Failed: {e}")

    # Simulate Supabase: Sign with STRING (Alternative hypothesis)
    print("\n--- Scenario B: Supabase signs with RAW STRING ---")
    token_str = jwt.encode(
        payload, SECRET_STR, algorithm="HS256"
    )  # PyJWT encodes str to utf-8 bytes

    # Verify with STRING (Current Code)
    try:
        jwt.decode(
            token_str, SECRET_STR, algorithms=["HS256"], audience="authenticated"
        )
        print("[PASS] Current Code Succeeded")
    except Exception as e:
        print(f"[FAIL] Current Code Failed: {e}")


if __name__ == "__main__":
    test()
