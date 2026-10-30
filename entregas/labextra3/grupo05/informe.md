# Informe — Lab Extra 3 · Defendé PhantomCorp (hardening)

**Grupo:** 05 · **Integrantes:** Magni, Gastón (@nosungam) · Mosconi, Ignacio
(@ignamosconi) · Presuttari, Matías (@matiaspresuttari) · Terreno, Valentino
(@vterreno) · **Fecha:** 2026-10-30

## 0. Declaración de uso de IA

Usamos Claude Code (Opus 4.8) como asistente para: ordenar el entorno de prueba
(WSL/Ubuntu, porque el verificador ataca con `../../etc/passwd` y en Windows ese
archivo no existe), correr el verificador-atacante del docente, capturar la
evidencia cruda y redactar este informe. **Los parches los escribimos y
entendemos nosotros**: cada fix de `objetivo/server.py` lo discutimos como grupo
y lo justificamos en la tabla de abajo. Las cinco flags no se copiaron de ningún
lado: las entregó el verificador cuando cada ataque dejó de funcionar contra
nuestra copia, y las validamos con `./ctf submit`. Como este lab nos pone del
lado del defensor, el foco del informe no es "capturar flags" sino mostrar que
cada puerta quedó cerrada de forma **estructural** y con argumento.

## 1. Tabla de defensas (antes → después)

Las flags las dio el verificador; la evidencia cruda está en `evidencia/salidas/`
(`verificador-inicial-0de5.txt` = objetivo roto, `verificador-final-5de5.txt` =
nuestra copia).

| Defensa | Ataque que funcionaba (antes) | Fix aplicado (estructural) | Verificación (después) |
|---|---|---|---|
| **D1** · banner | `Server: PhantomServer/2.4.1-debug` cantaba producto, versión y modo debug. | `server_version = "PhantomCorp"`, `sys_version = ""`: banner genérico, sin producto ni versión. | `header Server: 'PhantomCorp'` → `FLAG{def_banner_neutralizado}` |
| **D2** · debug en prod | `GET /api/status` devolvía `{"debug":true, "env":"produccion", "db":"/tmp/...", "pid":...}`. | Se **elimina el endpoint**: la rama cae al `404` general. En producción no existe un `/api/status`. | `GET /api/status -> 404` → `FLAG{def_debug_apagado}` |
| **D3** · rutas sensibles | `robots.txt` listaba `/backup` y `/backup` respondía `200` sin auth. | robots neutro (`Disallow:` vacío) **y** `/backup` exige `Authorization: Basic`; sin credencial → `401`. El fix es proteger el recurso, no esconderlo. | `GET /backup -> 401`; robots ya no menciona `/backup` → `FLAG{def_rutas_blindadas}` |
| **D4** · SQLi | `"... WHERE user = '" + user + "' AND password = '" + pwd + "'"`: `admin'--` y `' OR 1=1 --` logueaban. | Consulta **parametrizada**: `execute("... WHERE user = ? AND password = ?", (user, pwd))`. Los valores viajan separados del SQL. | `admin'--: bloqueado; OR 1=1: bloqueado` → `FLAG{def_sqli_parametrizado}` |
| **D5** · path traversal | `ruta = DESCARGAS + "/" + nombre`: `../../../../etc/passwd` leía cualquier archivo. | Confinamiento con `realpath` + `commonpath`: se exige que la ruta resuelta quede **dentro** de `DESCARGAS`; si no, `403`. | `traversal /etc/passwd -> 403 (bloqueado)` → `FLAG{def_traversal_bloqueado}` |

Diff conceptual de los dos fixes estructurales que más importan (D4 y D5):

```python
# D4 — antes (vulnerable):
cur = db.execute("SELECT user FROM usuarios WHERE user = '" + user
                 + "' AND password = '" + pwd + "'")
# D4 — después (parametrizado):
cur = db.execute("SELECT user FROM usuarios WHERE user = ? AND password = ?",
                 (user, pwd))

# D5 — antes (vulnerable):
ruta = DESCARGAS + "/" + nombre
with open(ruta, "rb") as fh: ...
# D5 — después (confinado):
base = os.path.realpath(DESCARGAS)
ruta = os.path.realpath(os.path.join(base, nombre))
if os.path.commonpath([base, ruta]) != base:
    self._txt(403, "prohibido"); return
```

## 2. Regresión funcional

La app sigue operando después del parche (evidencia: `evidencia/salidas/regresion.txt`):

- `GET /` → **200** (`<h1>PhantomCorp</h1>...`).
- Login legítimo `admin` / `sup3r-s3cr3t0` → **200** `Bienvenido, admin`.
- `GET /descargar?archivo=manual.txt` → **200**, descarga el manual.
- `GET /backup` **con** `Basic admin:sup3r-s3cr3t0` → **200** (la autorización
  deja pasar al legítimo; sin credencial da 401). Un parche que rompe la app no
  es un parche: acá no rompimos nada.

## 3. Evidencia de progreso

- **Inicial 0/5** (objetivo roto): `evidencia/salidas/verificador-inicial-0de5.txt`
  — las cinco `✗ todavía vulnerable`.
- **Final 5/5** (nuestra copia): `evidencia/salidas/verificador-final-5de5.txt`
  — las cinco `✓ ataque BLOQUEADO` con su flag.
- `./ctf status extra3` (`evidencia/salidas/ctf-status.txt`):

```
   ✓  D1     Banner neutralizado (info leak de version)
   ✓  D2     Endpoint de debug apagado en produccion
   ✓  D3     Rutas sensibles blindadas (backup + robots)
   ✓  D4     Login parametrizado (SQLi bloqueado)
   ✓  D5     Path traversal bloqueado en /descargar
   ██████████████████████████████  5/5 (100%)
```

## 4. Preguntas P1–P5

**P1. Antes/después de una defensa (elegimos D5, path traversal).**
*Ataque que funcionaba* — contra el objetivo roto, el verificador pide
`/descargar?archivo=../../../../etc/passwd` y el server concatena
`DESCARGAS + "/" + nombre`, abre `/tmp/phantom_descargas/../../../../etc/passwd`,
que el SO resuelve a `/etc/passwd`, y lo devuelve:
`traversal /etc/passwd -> 200 (FILTRADO (vulnerable))` (ver
`verificador-inicial-0de5.txt`).
*Parche* — en vez de bloquear la cadena `..`, **canonicalizamos y confinamos**:
`base = realpath(DESCARGAS)`, `ruta = realpath(join(base, nombre))`, y si
`commonpath([base, ruta]) != base` devolvemos `403`. Como `realpath` colapsa
`..`, resuelve rutas absolutas y normaliza, cae cualquier variante
(`..`, `%2e%2e%2f` que `parse_qs` ya decodifica, `....//`, `/etc/passwd`
absoluto).
*Ataque bloqueado* — `traversal /etc/passwd -> 403 (bloqueado)` (ver
`verificador-final-5de5.txt`), y a la vez `manual.txt` sigue descargando (sección 2).

**P2. En D3: sacar la ruta del `robots.txt` vs proteger la ruta.**
Son cosas distintas y solo una es defensa. `robots.txt` es una *sugerencia* para
crawlers bien portados: no es un control de acceso, no lo aplica el servidor, y
cualquiera lo lee para descubrir rutas "ocultas" (de hecho, el robots roto era un
mapa de lo sensible). Sacar `/backup` del robots solo lo hace menos evidente: la
ruta sigue respondiendo `200` a quien la pida. La defensa **real** es que el
servidor **niegue el acceso**: pusimos `/backup` detrás de `Authorization` y sin
credencial válida responde `401`. Por prolijidad también limpiamos el robots,
pero aunque alguien adivine la ruta, el `401` la frena. Esconder ≠ proteger.

**P3. D1 es ocultar información: ¿es defensa "real"? Seguridad por oscuridad.**
Neutralizar el banner **no arregla ninguna vulnerabilidad**: la app es igual de
(in)segura con o sin el header. Es seguridad por oscuridad, y como *única* medida
engaña: da sensación de seguridad sin cambiar la superficie de ataque, y además
es frágil (el producto/versión se puede inferir por comportamiento, cabeceras,
errores o rutas típicas). Dónde **sí** ayuda: como defensa en capas, subir el
costo de reconocimiento. Un `Server: PhantomServer/2.4.1-debug` le regala al
atacante el CVE exacto a probar y le confirma que hay un modo *debug*; quitarlo le
hace trabajar el fingerprinting. O sea: D1 es higiene legítima que **reduce
señal**, no un control que **cierre una puerta**. Vale hacerlo, pero nunca en
lugar de D2–D5, sino además de ellos.

**P4. En D4: ¿por qué `user.replace("'", "")` no alcanza y la consulta
parametrizada sí?**
`replace("'", "")` es un filtro de strings: intenta adivinar y borrar lo
"peligroso", y siempre se le escapa algo. Se bypassea con comillas codificadas
(`%27`, que `parse_qs` decodifica *después* del filtro), con payloads que no
necesitan comilla (inyección numérica: `pass=1 OR 1=1`), o rompiendo la app con
entradas legítimas que llevan apóstrofo (`O'Brien`). Trata el síntoma (un
carácter) sin tocar la causa (que datos del usuario se **concatenan como código
SQL**). La consulta parametrizada es la solución **estructural**: el `?` le dice
al motor "esto es un *valor*, no SQL"; el driver envía la sentencia y los datos
por canales separados y el valor nunca se interpreta como instrucción.
`' OR 1=1 --` pasa a buscar, literalmente, un usuario llamado `' OR 1=1 --`, no
existe, y no hay bypass. Arregla la clase entera de bug, no una de sus formas.

**P5. De los cinco, ¿cuál era el más grave? Ranking por impacto.**
1. **D4 (SQLi en login)** — el #1. Da **bypass de autenticación** (entrar sin
   credenciales) y, con `UNION`/consultas ciegas, lectura/escritura de toda la
   base: usuarios, hashes, datos. Compromete confidencialidad, integridad y el
   control de acceso de un saque, y es trivial de automatizar. A gerencia: *"un
   atacante entra como admin y se lleva la base sin contraseña"*.
2. **D5 (path traversal)** — **lectura arbitraria de archivos** del server
   (`/etc/passwd`, claves, config con secretos, código). No da ejecución directa,
   pero suele ser el trampolín: con lo que lee, escala.
3. **D3 (`/backup` sin auth)** — **exposición directa de datos**: un dump servido
   a cualquiera. Gravedad alta por lo concreto de la fuga, acotada a lo que haya
   en ese backup.
4. **D2 (`/api/status` debug)** — **info leak** que no daña por sí solo pero
   acelera todo lo demás: confirma entorno, ruta de la DB y PID. Insumo de
   reconocimiento.
5. **D1 (banner)** — el de menor impacto: **solo** revela producto y versión. No
   abre ninguna puerta; ayuda al atacante a elegir cuál golpear.

El criterio del ranking: arriba, lo que da **acceso o datos directos** (D4, D5,
D3); abajo, lo que solo da **información** para atacar mejor (D2, D1). El #1 es D4
porque combina el peor impacto (control total) con el menor esfuerzo.

## 5. Conclusión

Fue claramente más difícil **arreglar** que romper. Atacando PhantomCorp (labs
05–07) bastaba encontrar *una* puerta: un `' OR 1=1 --` y entrábamos. Defendiendo
tuvimos que cerrarlas **todas** y, encima, sin romper la app ni mentirnos con
parches cosméticos: distinguir "sacar del robots" de "proteger la ruta", y
"filtrar comillas" de "parametrizar". El atacante gana con un acierto; el defensor
pierde con un solo olvido. Esa asimetría —y el hecho de que la defensa real es
casi siempre *estructural* (parametrizar, confinar, autorizar), no *cosmética*
(ocultar, filtrar)— es lo que nos llevamos del lab.
