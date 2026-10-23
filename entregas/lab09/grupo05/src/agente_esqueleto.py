#!/usr/bin/env python3
"""
agente_esqueleto.py — TU agente (a completar). Entregable del Lab 09.

El agente de referencia (agente_pentest.py) ya funciona. Este es el TUYO: tiene
el andamiaje, pero el LOOP de tool-use está a medio hacer. Completá los TODO para
entender el mecanismo desde adentro. Un agente no es magia: es este loop.

Cuando funcione, corré:
    LLM_PROVIDER=mock python3 agente_esqueleto.py
y tiene que llegar a encadenar /api/token -> POST /api/vault y traer el flag
capstone (FLAG{agente_esqueleto_completo}).
"""
import re
import sys
from herramientas import TOOLS, ejecutar_tool
from llm import crear_cliente

SYSTEM = """Sos un agente de pentesting autorizado. Objetivo único: 'phantomcorp'.
Reconocé, enumerá, seguí las pistas y reportá toda FLAG{...}. Una tool por vez."""

MAX_PASOS = 12

def main() -> int:
    cliente = crear_cliente(SYSTEM, TOOLS)
    flags = set()
    resultados = None

    for n in range(1, MAX_PASOS + 1):
        accion = cliente.paso(resultados)

        # TODO 1 (completado): si la acción es de tipo "final", imprimí el texto
        # y salí del loop. El cliente devuelve {"tipo": "final", "texto": "..."}
        # cuando el LLM (o el mock) considera que terminó la auditoría.
        if accion["tipo"] == "final":
            print(f"\n[agente] Fin: {accion['texto']}")
            break

        # TODO 2 (completado): si es una tool, ejecutala con ejecutar_tool(nombre,
        # argumentos) y guardá la salida.
        # accion["nombre"]     -> string con el nombre de la tool (ej. "http_get")
        # accion["argumentos"] -> dict con los params (ej. {"url": "http://..."})
        nombre, args = accion["nombre"], accion["argumentos"]
        print(f"\n[paso {n}] → {nombre}({args})")
        salida = ejecutar_tool(nombre, args)
        # Mostramos las primeras 12 líneas para no saturar la terminal
        print("\n".join("    " + l for l in salida.splitlines()[:12]))

        # (esto ya estaba: detectar flags en la salida)
        for f in re.findall(r"FLAG\{[^}]*\}", salida):
            if f not in flags:
                print(f"    [+] FLAG NUEVA: {f}")
            flags.add(f)

        # TODO 3 (completado): devolvele el resultado al LLM para que pueda
        # tomar la siguiente decisión. El formato es una lista con un dict que
        # tiene "id" (el ID de la tool call que devolvió el cliente) y "output"
        # (la salida de la tool que acabamos de ejecutar).
        # Esto cierra el ciclo: LLM decide → nosotros ejecutamos → LLM ve el
        # resultado → LLM decide de nuevo.
        resultados = [{"id": accion["id"], "output": salida}]

    else:
        # El for terminó sin break: se agotaron los MAX_PASOS (guardrail de pasos)
        print(f"\n[agente] Alcancé el límite de {MAX_PASOS} pasos (guardrail).")

    print(f"\n=== Flags encontradas ({len(flags)}) ===")
    for f in sorted(flags):
        print(f"  {f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())