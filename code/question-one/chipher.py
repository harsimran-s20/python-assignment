import json
import os
import difflib
from typing import List, Tuple

RAW_FILE = "raw_text.txt"
ENC_FILE = "encrypted_text.txt"
META_FILE = "encrypted_text_meta.json"
DEC_FILE = "decrypted_text.txt"


# ---------- Helpers Functions ----------
def is_lower(c: str) -> bool:
    return 'a' <= c <= 'z'


def is_upper(c: str) -> bool:
    return 'A' <= c <= 'Z'


def shift_char(c: str, shift: int) -> str:
    """Shift ASCII letter c by `shift` positions with wrap-around. Non-letters returned unchanged."""
    if is_lower(c):
        base = ord('a')
        return chr((ord(c) - base + shift) % 26 + base)
    if is_upper(c):
        base = ord('A')
        return chr((ord(c) - base + shift) % 26 + base)
    return c


# Metadata codes (one per input character)
# 'L1' = lowercase a-m
# 'L2' = lowercase n-z
# 'U1' = uppercase A-M
# 'U2' = uppercase N-Z
# 'O'  = other (unchanged)


def classify_plain(c: str) -> str:
    if is_lower(c):
        return "L1" if 'a' <= c <= 'm' else "L2"
    if is_upper(c):
        return "U1" if 'A' <= c <= 'M' else "U2"
    return "O"


def encrypt_char_and_meta(c: str, shift1: int, shift2: int) -> Tuple[str, str]:
    """Encrypt one char and return (cipher_char, meta_code)."""
    code = classify_plain(c)
    # reducing shift components mod 26 for safety
    s1 = shift1 % 26
    s2 = shift2 % 26
    if code == "L1":
        return shift_char(c, (s1 * s2) % 26), code
    if code == "L2":
        # shifting backward by (shift1 + shift2)
        return shift_char(c, -((s1 + s2) % 26)), code
    if code == "U1":
        # shifting backward by shift1
        return shift_char(c, -s1), code
    if code == "U2":
        # shifting forward by shift2^2
        return shift_char(c, (s2 * s2) % 26), code
    return c, code


def inverse_by_meta(cipher_c: str, meta_code: str, shift1: int, shift2: int) -> str:
    """Undo a single char using its saved metadata."""
    s1 = shift1 % 26
    s2 = shift2 % 26
    if meta_code == "L1":
        return shift_char(cipher_c, -((s1 * s2) % 26))
    if meta_code == "L2":
        return shift_char(cipher_c, (s1 + s2) % 26)
    if meta_code == "U1":
        return shift_char(cipher_c, s1)
    if meta_code == "U2":
        return shift_char(cipher_c, -((s2 * s2) % 26))
    return cipher_c


# ---------- File Operations ----------
def encrypt_file(raw_path: str, enc_path: str, meta_path: str, shift1: int, shift2: int) -> None:
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"'{raw_path}' not found.")

    with open(raw_path, "r", encoding="utf-8") as f:
        raw = f.read()

    enc_chars: List[str] = []
    meta: List[str] = []

    for ch in raw:
        e, code = encrypt_char_and_meta(ch, shift1, shift2)
        enc_chars.append(e)
        meta.append(code)

    with open(enc_path, "w", encoding="utf-8") as f:
        f.write("".join(enc_chars))

    # Compacting metadata - list of small strings length == len(raw)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)

    print(f"Encrypted -> '{enc_path}' and metadata -> '{meta_path}' written.")


def decrypt_file(enc_path: str, dec_path: str, meta_path: str, shift1: int, shift2: int) -> None:
    if not os.path.exists(enc_path):
        raise FileNotFoundError(f"'{enc_path}' not found.")

    with open(enc_path, "r", encoding="utf-8") as f:
        enc_text = f.read()

    # Trying to load metadata; fallback to brute-force if missing or invalid
    meta = None
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as mf:
                meta = json.load(mf)
            if not isinstance(meta, list) or len(meta) != len(enc_text):
                print("Warning: metadata exists but is invalid or length mismatch -> will attempt brute-force fallback.")
                meta = None
        except Exception as e:
            print(f"Warning reading metadata: {e} -> attempting brute-force fallback.")
            meta = None
    else:
        print("Metadata file not found -> attempting brute-force fallback.")

    if meta is not None:
        dec_chars = [inverse_by_meta(c, m, shift1, shift2) for c, m in zip(enc_text, meta)]
        ambiguities = []
    else:
        dec_chars, ambiguities = brute_force_decrypt(enc_text, shift1, shift2)
        if ambiguities:
            print(f"Brute-force decryption produced {len(ambiguities)} ambiguous positions (see output).")

    with open(dec_path, "w", encoding="utf-8") as f:
        f.write("".join(dec_chars))

    print(f"Decrypted -> '{dec_path}' written.")
    if meta is None and ambiguities:
        # Showing a few ambiguities
        print("Ambiguous positions (index, cipher, candidates):")
        for pos, cipher_ch, candidates in ambiguities[:20]:
            print(f"  {pos}: '{cipher_ch}' -> {candidates}")
        if len(ambiguities) > 20:
            print(f"  ... and {len(ambiguities)-20} more ambiguous positions.")


# ---------- Brute-force fallback (only used if metadata missing/invalid) ----------
def brute_force_decrypt(enc_text: str, shift1: int, shift2: int) -> Tuple[List[str], List[Tuple[int, str, List[str]]]]:
    """
    For each alphabetic position try all plaintext letters and see which map to this ciphertext char.
    If exactly one plaintext maps -> use it. If multiple map -> record ambiguity and pick first deterministically.
    """
    s1 = shift1 % 26
    s2 = shift2 % 26
    decrypted: List[str] = []
    ambiguities: List[Tuple[int, str, List[str]]] = []

    lower_alphabet = [chr(i) for i in range(ord('a'), ord('z') + 1)]
    upper_alphabet = [chr(i) for i in range(ord('A'), ord('Z') + 1)]

    for i, c in enumerate(enc_text):
        if is_lower(c):
            candidates = []
            for p in lower_alphabet:
                # encrypting p to see if it equals c
                code = classify_plain(p)
                if code == "L1":
                    e = shift_char(p, (s1 * s2) % 26)
                else:
                    # L2
                    e = shift_char(p, -((s1 + s2) % 26))
                if e == c:
                    candidates.append(p)
            if len(candidates) == 1:
                decrypted.append(candidates[0])
            else:
                decrypted.append(candidates[0] if candidates else c)
                ambiguities.append((i, c, candidates))
        elif is_upper(c):
            candidates = []
            for p in upper_alphabet:
                code = classify_plain(p)
                if code == "U1":
                    e = shift_char(p, -s1)
                else:
                    # U2
                    e = shift_char(p, (s2 * s2) % 26)
                if e == c:
                    candidates.append(p)
            if len(candidates) == 1:
                decrypted.append(candidates[0])
            else:
                decrypted.append(candidates[0] if candidates else c)
                ambiguities.append((i, c, candidates))
        else:
            decrypted.append(c)

    return decrypted, ambiguities


# ---------- Verification (with small diff preview) ----------
def verify_files(raw_path: str, dec_path: str) -> bool:
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"'{raw_path}' not found.")
    if not os.path.exists(dec_path):
        raise FileNotFoundError(f"'{dec_path}' not found.")

    with open(raw_path, "r", encoding="utf-8") as f:
        raw = f.read()
    with open(dec_path, "r", encoding="utf-8") as f:
        dec = f.read()

    if raw == dec:
        print("Decryption successful! Decrypted text matches the original.")
        return True

    print("Decryption failed: decrypted text does not match original.")
    print("\nShowing a short unified diff (original -> decrypted):\n")
    raw_lines = raw.splitlines(keepends=True)
    dec_lines = dec.splitlines(keepends=True)
    diff_iter = difflib.unified_diff(raw_lines, dec_lines, fromfile=raw_path, tofile=dec_path, n=3)
    shown = 0
    for line in diff_iter:
        print(line.rstrip("\n"))
        shown += 1
        if shown >= 200:
            print("... (diff truncated) ...")
            break
    return False


# ---------- Main ----------
def main() -> None:
    try:
        s1 = int(input("Enter shift1: ").strip())
        s2 = int(input("Enter shift2: ").strip())
    except ValueError:
        print("Please enter valid integer values for shift1 and shift2.")
        return

    try:
        encrypt_file(RAW_FILE, ENC_FILE, META_FILE, s1, s2)
    except Exception as e:
        print(f"Encryption error: {e}")
        return

    try:
        decrypt_file(ENC_FILE, DEC_FILE, META_FILE, s1, s2)
    except Exception as e:
        print(f"Decryption error: {e}")
        return

    try:
        verify_files(RAW_FILE, DEC_FILE)
    except Exception as e:
        print(f"Verification error: {e}")


if __name__ == "__main__":
    main()