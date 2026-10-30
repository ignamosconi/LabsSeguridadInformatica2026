#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Fernando Boiero — CyberLab UTN FRVM
"""
cracker.py — Lab Extra 4. Tu cracker de contraseñas. Solo biblioteca estándar.

Looteaste `caso/sombra.txt` de phantomcorp-web: un volcado de hashes con sus
algoritmos y salts. Tu trabajo: recuperar las contraseñas y con ellas abrir el
loot cifrado de cada usuario (`caso/loot/<usuario>.enc`).

Completá los TODO. NO cambies las firmas ni la CLI.
`descifrar_loot()` ya viene implementada como referencia: leela.

Uso:
  python3 cracker.py crackear caso/sombra.txt caso/diccionario.txt
  python3 cracker.py descifrar caso/loot/operador.enc --password riverplate

Extra (R3): la contraseña del admin NO está literal en el diccionario.
Implementá reglas de "mangling" en `aplicar_reglas()`: sufijos de año, de
números, mayúscula inicial, etc.
"""
import argparse
import hashlib
import sys
import time

ITER_PBKDF2 = 200_000   # tiene que coincidir con sombra.txt


# ---------------------------------------------------------------------------
# REFERENCIA (ya implementada). Leela: es la mitad del lab.
# ---------------------------------------------------------------------------
def descifrar_loot(hex_cifrado: str, password: str) -> str:
    """El loot se cifró con XOR contra sha256(password) repetido.
    XOR es involutivo: con la contraseña correcta, esto devuelve el texto."""
    clave = hashlib.sha256(password.encode()).digest()
    datos = bytes.fromhex(hex_cifrado.strip())
    return bytes(b ^ clave[i % len(clave)] for i, b in enumerate(datos)).decode("utf-8", "ignore")


def hash_de(algo: str, salt_hex: str, password: str) -> str:
    """Calcula el hash de un candidato EXACTAMENTE como lo hizo el servidor.
    Para md5/sha256: hash(salt_bytes + password_bytes).
    Para pbkdf2: pbkdf2_hmac('sha256', password_bytes, salt_bytes, ITER_PBKDF2)."""
    salt = bytes.fromhex(salt_hex)
    pwd = password.encode()
    if algo == "pbkdf2":
        return hashlib.pbkdf2_hmac("sha256", pwd, salt, ITER_PBKDF2).hex()
    h = hashlib.new(algo)
    h.update(salt + pwd)
    return h.hexdigest()


def cargar_sombra(ruta: str) -> list:
    """Devuelve una lista de tuplas (usuario, algo, salt_hex, hash_hex)
    parseando sombra.txt (ignorá líneas de comentario que empiezan con #)."""
    entradas = []
    with open(ruta) as fh:
        for linea in fh:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            partes = linea.split(":")
            entradas.append((partes[0], partes[1], partes[2], partes[3]))
    return entradas


def aplicar_reglas(palabra: str) -> list:
    """Dado un lemma del diccionario, devolvé variantes probables.
    Cubre los patrones más comunes que usan los humanos al "endurecer" contraseñas."""
    variantes = [palabra]
    # mayúscula inicial
    variantes.append(palabra.capitalize())
    # todo mayúsculas
    variantes.append(palabra.upper())
    # sufijos de año (políticas de rotación anual)
    for anio in ("2023", "2024", "2025", "2026"):
        variantes.append(palabra + anio)
        variantes.append(palabra.capitalize() + anio)
    # sufijos numéricos comunes
    for sufijo in ("1", "12", "123", "1234", "01", "007", "99", "00"):
        variantes.append(palabra + sufijo)
    # prefijos numéricos
    variantes.append("1" + palabra)
    variantes.append("123" + palabra)
    # reemplazos leet básicos (a→@, e→3, i→1, o→0, s→$)
    leet = palabra.replace("a", "@").replace("e", "3").replace("i", "1").replace("o", "0").replace("s", "$")
    if leet != palabra:
        variantes.append(leet)
    return variantes


def crackear(sombra: list, diccionario: str, con_reglas: bool = False) -> dict:
    """Para cada usuario, probá cada candidato del diccionario (y sus variantes
    si con_reglas=True) hasta que hash_de() coincida con el hash looteado.
    Devolvé {usuario: password} de los que cayeron. Imprimí el progreso.

    OJO con pbkdf2: 200.000 iteraciones por intento. ¿Conviene probarlo con el
    diccionario entero? ¿Qué te dice eso del algoritmo? (Pista: es la P4.)"""
    with open(diccionario) as fh:
        palabras = [l.strip() for l in fh if l.strip() and not l.startswith("#")]

    halladas = {}
    for usuario, algo, salt_hex, hash_esperado in sombra:
        # No intentamos crackear pbkdf2 con el diccionario completo —
        # 200k iteraciones × 50 palabras × variantes = minutos; y la contraseña
        # de root no está en el diccionario de todos modos. Eso es la lección.
        if algo == "pbkdf2":
            print(f"  ⏭  {usuario} ({algo}): omitido — 200k iteraciones/intento hacen el ataque inviable")
            continue

        candidatos = []
        for palabra in palabras:
            if con_reglas:
                candidatos.extend(aplicar_reglas(palabra))
            else:
                candidatos.append(palabra)

        t0 = time.perf_counter()
        intentos = 0
        for candidato in candidatos:
            intentos += 1
            if hash_de(algo, salt_hex, candidato) == hash_esperado:
                elapsed = time.perf_counter() - t0
                vel = intentos / elapsed if elapsed > 0 else float("inf")
                print(f"  ✓ {usuario} ({algo}): '{candidato}' — {intentos} intentos en {elapsed:.4f}s ({vel:.0f} intentos/s)")
                halladas[usuario] = candidato
                break
        else:
            elapsed = time.perf_counter() - t0
            vel = intentos / elapsed if elapsed > 0 else float("inf")
            print(f"  ✗ {usuario} ({algo}): no cayó — {intentos} intentos en {elapsed:.4f}s ({vel:.0f} intentos/s)")

    return halladas


def main() -> int:
    ap = argparse.ArgumentParser(description="Cracker de contraseñas (Lab Extra 4)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("crackear", help="atacar un volcado de hashes")
    c.add_argument("sombra")
    c.add_argument("diccionario")
    c.add_argument("--reglas", action="store_true", help="aplicar reglas de mangling")
    d = sub.add_parser("descifrar", help="abrir un loot con la contraseña crackeada")
    d.add_argument("loot")
    d.add_argument("--password", required=True)
    args = ap.parse_args()

    if args.cmd == "crackear":
        sombra = cargar_sombra(args.sombra)
        halladas = crackear(sombra, args.diccionario, args.reglas)
        for usuario, _algo, _salt, _h in sombra:
            if usuario in halladas:
                print(f"  ✓ {usuario}: {halladas[usuario]}")
            else:
                print(f"  ✗ {usuario}: no cayó (¿falta una regla? ¿es pbkdf2?)")
        print(f"\n{len(halladas)}/{len(sombra)} contraseñas recuperadas")
    else:
        with open(args.loot) as fh:
            print(descifrar_loot(fh.read(), args.password))
    return 0


if __name__ == "__main__":
    sys.exit(main())
