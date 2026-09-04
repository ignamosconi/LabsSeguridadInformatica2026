#!/usr/bin/env python3
"""
pruebas.py — verificación de auth.py contra vectores oficiales. Solo stdlib.

No es parte del esqueleto de la cátedra: lo agregamos para no "verificar a ojo".
    python3 src/pruebas.py
"""
import hashlib, hmac, sys, time
from auth import hash_password, verify_password, hotp, totp

fallas = []

def check(nombre, obtenido, esperado):
    ok = obtenido == esperado
    print(f"  [{'OK ' if ok else 'FALLA'}] {nombre:<46} {obtenido}")
    if not ok:
        fallas.append(f"{nombre}: obtenido {obtenido!r}, esperado {esperado!r}")

# --- B.2: RFC 6238, Appendix B (semilla SHA-1 = ASCII "12345678901234567890") ---
print("RFC 6238 Appendix B — TOTP SHA-1, paso 30 s:")
SEMILLA = b"12345678901234567890"
for t, esperado in [(59, "287082"), (1111111109, "081804"), (1111111111, "050471"),
                    (1234567890, "005924"), (2000000000, "279037"), (20000000000, "353130")]:
    check(f"totp(t={t})", totp(SEMILLA, t), esperado)
check("totp(t=59, 8 digitos)", totp(SEMILLA, 59, digitos=8), "94287082")

# --- RFC 4226, Appendix D: HOTP con la misma semilla, contadores 0..9 ---
print("\nRFC 4226 Appendix D — HOTP:")
RFC4226 = ["755224", "287082", "359152", "969429", "338314",
           "254676", "287922", "162583", "399871", "520489"]
for c, esperado in enumerate(RFC4226):
    check(f"hotp(contador={c})", hotp(SEMILLA, c), esperado)

# Coherencia TOTP/HOTP: t=59 cae en el paso 1, y el paso 1 es HOTP(1).
print("\nCoherencia TOTP = HOTP(t // 30):")
check("totp(t=59) == hotp(1)", totp(SEMILLA, 59), hotp(SEMILLA, 1))
check("totp(t=29) == hotp(0)", totp(SEMILLA, 29), hotp(SEMILLA, 0))
check("totp(t=30) != totp(t=29)", totp(SEMILLA, 30) != totp(SEMILLA, 29), True)
check("sin t explicito usa el reloj", totp(SEMILLA), totp(SEMILLA, int(time.time())))

# --- B.1: PBKDF2 ---
print("\nPBKDF2 — formato y verificacion:")
reg = hash_password("Phantom-2026!")
partes = reg.split("$")
check("formato: 4 campos", len(partes), 4)
check("etiqueta del algoritmo", partes[0], "pbkdf2_sha256")
check("iteraciones por defecto", partes[1], "200000")
check("salt de 16 bytes (32 hex)", len(partes[2]), 32)
check("derivada de 32 bytes (64 hex)", len(partes[3]), 64)
check("contrasena correcta", verify_password("Phantom-2026!", reg), True)
check("contrasena incorrecta", verify_password("phantom-2026!", reg), False)
check("contrasena vacia", verify_password("", reg), False)
check("salt aleatorio por registro", hash_password("hola") != hash_password("hola"), True)

# Vector determinista de PBKDF2-HMAC-SHA256 (password="passwd", salt="salt", c=1).
esperado = hashlib.pbkdf2_hmac("sha256", b"passwd", b"salt", 1).hex()
check("salt/iters explicitos son deterministas",
      hash_password("passwd", salt=b"salt", iters=1).split("$")[3], esperado)

# Registros invalidos: devuelven False, no explotan.
print("\nRegistros invalidos (deben dar False sin excepcion):")
for malo in ["", "basura", "sha256$1$00$00", "pbkdf2_sha256$abc$00$00",
             "pbkdf2_sha256$0$00$00", "pbkdf2_sha256$1$zz$00",
             "pbkdf2_sha256$1$$00", "pbkdf2_sha256$1$00$", None]:
    check(f"verify(registro={malo!r})", verify_password("x", malo), False)

# --- Tiempo constante: la comparacion no debe depender de donde difiere ---
print("\nTiempo constante (hmac.compare_digest):")
ref = bytes(range(32))
def medir(f, a, b, reps=20000, bloques=7):
    """ns por llamada; el minimo de varios bloques es lo menos contaminado por ruido."""
    def bloque():
        t0 = time.perf_counter()
        for _ in range(reps): f(a, b)
        return (time.perf_counter() - t0) / reps * 1e9
    return min(bloque() for _ in range(bloques))
tiempos = [medir(hmac.compare_digest, ref, ref[:i] + bytes([ref[i] ^ 0xFF]) + ref[i+1:])
           for i in (0, 15, 31)]
disp = (max(tiempos) - min(tiempos)) / min(tiempos)
print(f"  bytes 0/15/31: {tiempos[0]:.0f} / {tiempos[1]:.0f} / {tiempos[2]:.0f} ns"
      f"  -> dispersion {disp*100:.1f}%")
check("dispersion < 25% (no depende del prefijo)", disp < 0.25, True)

print()
if fallas:
    print(f"{len(fallas)} FALLA(S):")
    for f_ in fallas: print("  -", f_)
    sys.exit(1)
print("Todas las pruebas pasaron.")
sys.exit(0)
