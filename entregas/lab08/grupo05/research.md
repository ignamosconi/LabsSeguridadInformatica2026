# Mini-research — Laboratorio 08

**Tema elegido:** **D. De scripts a agentes** — qué agrega un agente de IA sobre
un script de automatización, y qué NO debería decidir solo.

## Desarrollo

Un **script** de automatización (como nuestro `recolector.py`) ejecuta una
secuencia **fija** que un humano definió de antemano: enumerar 1..250, filtrar por
una clave, cortar al hallar. Es rápido y determinista, pero **no decide**: si el
objetivo cambia, el endpoint se renombra o el patrón del "hallazgo" es otro, el
script falla o devuelve nada hasta que un humano lo reescribe. Su inteligencia es
la que le pusimos nosotros al escribirlo.

Un **agente de IA** agrega una capa de **orquestación y decisión** sobre ese
mismo conjunto de herramientas. En la arquitectura que describe Anthropic, un
agente opera en un **loop**: percibe el estado (salida de una tool), **razona**
sobre qué hacer, **elige** la próxima herramienta y sus argumentos, actúa, y
repite hasta cumplir (o abandonar) un objetivo. La diferencia clave con un
"workflow" (pasos encadenados por código) es que el agente **dirige su propio
flujo**: decide dinámicamente la secuencia en vez de seguir un guion fijo. Sobre
un script, un agente aporta: (1) **adaptación** —reacciona a lo inesperado, un
404 masivo, un servicio nuevo descubierto—, (2) **encadenamiento de objetivos**
—no una tarea, sino "entrá y conseguí el dato", resolviendo subtareas—, y (3)
**manejo de ambigüedad** en lenguaje natural. El puente conceptual del curso:
*si no sabés scriptear el encadenamiento de tools, no vas a saber dirigir al
agente que las encadena* — el agente automatiza la **decisión de qué script
correr y cuándo**, no la ejecución en sí.

**Qué NO debería decidir solo un agente (ofensivo).** Precisamente porque decide,
hay que ponerle límites duros, análogos al P4 del lab:
- **Alcance / autorización**: contra qué hosts puede actuar. Nunca salir del
  perímetro autorizado — en nuestro caso, del lab (Ley 26.388). Esto no se
  delega: lo fija el humano y se hace cumplir por fuera del agente.
- **Acciones destructivas o irreversibles**: borrar datos, apagar servicios,
  persistencia, exfiltración real. Deben requerir confirmación humana
  (human-in-the-loop).
- **Criterio de parada y presupuesto**: cuántos requests, cuánto tiempo, cuándo
  frenar — un agente sin tope puede amplificar el daño a escala de máquina.
- **Juicio legal/ético y manejo de datos sensibles**: qué es un objetivo legítimo
  y qué se hace con lo encontrado.
En defensa esto se formaliza como **mínimo privilegio para el agente** y
**guardarraíles**: el agente propone, el humano aprueba lo riesgoso.

### Bonus — pipeline recon → enum → explotación (hacia el Lab 09)

Encadenando los labs previos, el `recolector.py` es una pieza de un flujo mayor
que un agente podría orquestar (nosotros fijamos objetivo y límites; él decide la
secuencia):

```
objetivo + alcance (humano)
      │
  [recon] escaner.py (Lab 05) ── puertos/servicios abiertos ─┐
      │                                                       │
  [enum]  fingerprint de servicios (Lab 06) ── versiones, endpoints
      │                                                       │
  [explotación] exploit del servicio vulnerable (Lab 07) ── RCE → shell
      │
  [post-explotación] (Lab 08):
      ├─ recon host (id/env/red) ─ loot (.env, history) ─ privesc (SUID)
      └─ pivot a red interna ──→ recolector.py enumera 1..250 ──→ dato objetivo
      │
  reporte (humano revisa) ───────────────────────────────────┘
```

Cada flecha es una **decisión** que hoy tomamos nosotros (qué salida alimenta la
siguiente tool, cuándo pivotear, cuándo parar). Un agente toma esas decisiones
dentro de los límites que le damos; las acciones irreversibles y el alcance
siguen necesitando aprobación humana.

## Fuentes (mín. 3, verificables)

1. Anthropic — *Building Effective Agents* (2024).
   https://www.anthropic.com/engineering/building-effective-agents
   (distinción workflow vs. agente; el loop percibir–decidir–actuar).
2. MITRE ATT&CK — tácticas de post-explotación encadenadas: *Discovery* (TA0007),
   *Credential Access* (TA0006), *Privilege Escalation* (TA0004),
   *Lateral Movement* (TA0008), *Persistence* (TA0003).
   https://attack.mitre.org/tactics/enterprise/
3. GTFOBins — *bash* (SUID): el truco `bash -p` para preservar el euid del dueño.
   https://gtfobins.github.io/gtfobins/bash/#suid
4. OWASP — *Agentic AI / LLM Top 10* (riesgos de autonomía excesiva y necesidad de
   human-in-the-loop y mínimo privilegio para agentes).
   https://genai.owasp.org/

## Reflexión (3–5 líneas)

Hacer el flujo a mano primero dejó clarísima la frontera entre *ejecución* y
*decisión*: el script hace la parte repetitiva, pero cada "qué sigue" lo pusimos
nosotros. Un agente mueve esa frontera: automatiza la decisión, no solo la
repetición. Eso es potente y por eso mismo peligroso — la misma velocidad que nos
ayuda, sin límites de alcance, presupuesto y aprobación humana para lo
irreversible, amplifica el daño a escala de máquina. La lección para el Lab 09 es
que dirigir un agente es, sobre todo, **diseñar sus guardarraíles**.
