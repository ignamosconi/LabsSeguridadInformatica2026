# Informe — Laboratorio 07 · Explotación

**Grupo:** 05 · **Integrantes:** *Gastón Magni (@nosungam), Ignacio Mosconi (@ignamosconi), Matías Presuttari (@matiaspresuttari), Valentino Terreno (@vterreno)* · **Fecha:** 09/10/2026

## 0. Declaración de uso de IA

Se utilizó Claude (Anthropic) como asistente durante la resolución del laboratorio.
Usos concretos:
- Estructuración del informe y redacción de las secciones de análisis.
- Apoyo para reconstruir, a partir de las respuestas del servidor, cómo queda
  armada cada consulta/comando/ruta final tras la inyección.
- Redacción del mini-research (sección en `research.md`).

El grupo levantó el entorno Docker de la cátedra (`make setup && ./ctf lab 07`)
y ejecutó cada exploit contra `phantomcorp` desde la consola del atacante
(`make shell`), razonando el payload a partir de la teoría del README (Parte 1
y 3) y verificando cada respuesta HTTP obtenida. Las flags se capturaron
explotando los endpoints reales, **no** se leyeron de `solucion.md` ni del
código fuente del target.

## 1. Flags capturadas

```text
  ╭────────────────────────────────────────────────────────────╮
  │                     PROGRESO · LAB 07                      │
  ╰────────────────────────────────────────────────────────────╯

   ✓  R1     SQLi - bypass de autenticacion
   ✓  R2     SQLi - extraccion de datos con UNION
   ✓  R3     Inyeccion de comandos (RCE)
   ✓  R4     Path traversal / LFI
   ✓  R5     IDOR - control de acceso roto

  ██████████████████████████████  5/5 (100%)

[ OK ] ¡Lab 07 COMPLETO! Ponete las pilas con la próxima unidad.
```

## 2. Tabla de explotación

| Vuln | Payload usado | Consulta/comando/ruta resultante | Impacto | Defensa concreta |
|---|---|---|---|---|
| SQLi auth (R1) | `user=admin' -- ` / `pass=x` | `SELECT user, rol FROM users WHERE user='admin' -- ' AND pass='x'` | Login como `admin` sin conocer su contraseña; acceso total al panel de administración | Consultas parametrizadas / *prepared statements* (nunca concatenar el input en el SQL) |
| SQLi UNION (R2) | `q=' UNION SELECT clave,valor FROM secrets -- ` | `SELECT nombre, precio FROM productos WHERE nombre LIKE '%' UNION SELECT clave,valor FROM secrets -- %'` | Extracción completa de la tabla `secrets` (fuera del alcance previsto del buscador) | Consultas parametrizadas; además, principio de mínimo privilegio en el usuario de BD de la app (sin acceso a tablas que no necesita) |
