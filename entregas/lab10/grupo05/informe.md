# Informe — Laboratorio 10 · Detección y evasión

**Grupo:** 05 · **Integrantes:** Magni, Gastón (@nosungam) · Mosconi, Ignacio
(@ignamosconi) · Presuttari, Matías (@matiaspresuttari) · Terreno, Valentino
(@vterreno) · **Fecha:** 2026-10-27

## 0. Declaración de uso de IA

Usamos Claude Code (Opus 4.8) como asistente para: levantar el entorno Docker del
lab, correr los retos R1–R5 contra el target real, ordenar la evidencia y redactar
este informe y el `research.md`. Todas las flags se obtuvieron ejecutando el
entorno real (`./ctf lab 10` + consola atacante contra `phantomcorp`), no se
copiaron de ningún `solucion.md`. Revisamos y entendemos cada request, cada firma
del IDS y cada respuesta de análisis. Este lab nos pone del lado del defensor, así
que el foco del informe no es "capturar flags" sino entender **qué nos delata y
por qué una firma se evade**.

## 1. Flags capturadas

Salida de `./ctf status 10` (evidencia: `evidencia/ctf-status.txt`):

```
   ✓  R1     Acceso a la vista del SOC
   ✓  R2     Disparar una deteccion (te vieron)
   ✓  R3     Conocer el ruleset del IDS
   ✓  R4     Evadir una firma de deteccion
   ✓  R5     Encontrar la intrusion en el ruido
   ██████████████████████████████  5/5 (100%)
```

| Reto | Cara | Flag | Evidencia |
|---|---|---|---|
| R1 | Blue | `FLAG{soc_log_access}` | `evidencia/r1-soc.txt` |
| R2 | Red | `FLAG{detection_triggered}` | `evidencia/r2-deteccion.txt` |
| R3 | Blue | `FLAG{signature_ruleset}` | `evidencia/r3-reglas.txt` |
| R4 | Red | `FLAG{signature_evaded}` | `evidencia/r4-evasion.txt` |
| R5 | Blue | `FLAG{intrusion_in_the_noise}` | `evidencia/r5-intrusion.txt` |

Recorrido de los retos:

- **R1 (Blue) — acceder al SOC.** `GET /soc` concede la vista de eventos del
  defensor: 120 líneas de tráfico y el flag en la cabecera. Es el punto de
  partida: para evadir o para cazar, primero hay que ver lo que ve el defensor.
- **R2 (Red) — hacer que te detecten.** Un `curl -A sqlmap` matchea la firma
  `scanner-ua` y devuelve `403` con la alerta. La detección nos dice **qué firma**
  disparó: eso, que para el SOC es un evento, para el atacante es el mapa de lo que
  hay que esquivar.
- **R3 (Blue) — leer el ruleset.** `GET /soc/reglas` publica las cuatro firmas
  activas. La clave: `sqli-union` matchea `/union\s+select/`, **exige un espacio**.
- **R4 (Red) — evadir.** Reescribimos `UNION SELECT` sin el espacio literal usando
  un comentario SQL inline (`union/**/select`). Mismo efecto en un motor SQL, otra
  cadena: ninguna firma matchea y el server lo procesa como benigno pero reconoce
  que la request era maliciosa → `FLAG{signature_evaded}`.
- **R5 (Blue) — la aguja en el pajar.** Filtrando `/soc` por `ALERT` aparece una
  línea que **no disparamos nosotros**: `185.220.101.42 - GET /admin/../../etc/passwd`
  (una IP de salida de Tor conocida), escondida entre 120 líneas benignas. Esa es
  la intrusión real no atribuida.

## 2. Tabla de firmas

Para cada firma: cómo la evadimos (o cómo se evade) y cómo la mejoraríamos como
defensores. Pensamos la mejora, no solo la evasión.

| Firma | Qué detecta | Cómo se evade | Cómo se mejora la detección |
|---|---|---|---|
| **scanner-ua** | `User-Agent` contiene `sqlmap\|nikto\|nmap\|dirb` | Cambiar la User-Agent por la de un navegador (`-A "Mozilla/5.0 ..."`). La misma herramienta, otra identidad, y la firma no la ve: miraba *quién decís ser*, no *qué hacés*. | No confiar en un campo que el cliente controla libremente. Detectar por **comportamiento**: tasa de requests, cantidad de 404 en ráfaga, recorrido secuencial de rutas, patrones de payload. La UA sirve como señal de bajo peso que suma a un score, no como regla única. |
| **sqli-union** | Query matchea `/union\s+select/` (exige un **espacio**) | Quitar el espacio literal: `union/**/select` (comentario SQL inline) o codificarlo (`union%20select` queda como `%20` en el query crudo y tampoco matchea `\s`). Mismo efecto SQL, la cadena ya no coincide con la firma. | Normalizar/canonicalizar **antes** de matchear: URL-decode, colapsar comentarios `/**/`, unificar mayúsculas y espacios en blanco, y recién ahí aplicar la regla sobre tokens (`union` … `select` con cualquier separador o ninguno). Mejor aún: parametrizar las consultas en la app para que el SQLi no exista, y dejar la firma como alarma, no como única barrera. |
| **path-traversal** *(contraste)* | La ruta contiene `../` | Codificar los separadores (`%2e%2e%2f`, double-encoding `%252e`) o usar variantes (`..%2f`, `....//`) que decodifican a `../` después del match. (curl incluso normaliza `../` si no se usa `--path-as-is`.) | Decodificar y canonicalizar la ruta a su forma absoluta antes de inspeccionar, y comparar contra una allowlist de rutas válidas en vez de buscar una subcadena prohibida. |
| **git-probe** *(contraste)* | La ruta contiene `/.git` | Acceder a los objetos por su hash o a rutas alternativas de metadatos que no contengan literalmente `/.git`. | Igual criterio: no servir nunca directorios de control de versiones (bloqueo en el servidor web), que es defensa por diseño y no por firma. |

Las dos primeras filas son las que pide la rúbrica (las que tocamos en R2 y R4);
las dos de contraste las agregamos porque las vimos en el ruleset y nos ayudaron a
entender el patrón general: **toda firma que busca una subcadena exacta se esquiva
cambiando la cadena sin cambiar el efecto**. Evidencia del contraste en
`evidencia/r2b-otras-firmas.txt`.

## 3. Preguntas P1–P5

**P1. ¿Por qué la detección por firmas es evadible por diseño? ¿Qué la
complementa?**
Una firma describe un ataque **conocido** por su forma exacta (una cadena, un
regex, una UA). Reconoce lo que ya vio, instantáneamente y con bajo costo; pero
una misma acción maliciosa admite infinitas representaciones (encoding, comentarios,
sinónimos, fragmentación), y basta con una que la firma no describa para colarse.
Es la asimetría de fondo: el defensor debe enumerar todas las formas del ataque, el
atacante necesita una sola que falte. La complementan dos cosas: **detección por
anomalía/comportamiento** (qué se desvía de la línea base, independiente de la forma
exacta) y el **analista humano** correlacionando logs (SIEM), que es el único que
encuentra lo que ninguna regla anticipó. Firmas *y* analistas, no una sola.

**P2. La firma `sqli-union` exigía un espacio. Reescribí la regla para que NO se
evada con `/**/`. ¿Se puede hacer una firma "perfecta"?**
El problema es matchear sobre el texto crudo. La regla hay que aplicarla **después
de canonicalizar**: (1) URL-decode del query, (2) eliminar comentarios inline
`/\*.*?\*/`, (3) colapsar todo espacio en blanco a uno solo y pasar a minúsculas.
Recién ahí matchear algo como `/union\s+select/`. En pseudo-regla:

```
q_norm = collapse_ws(strip_sql_comments(url_decode(q))).lower()
if re.search(r"union\s+select", q_norm): -> ALERTA
```

Con eso, `union/**/select` y `union%20select` caen en la misma forma normalizada y
disparan. Pero **no existe la firma "perfecta"**: siempre queda espacio para
`UNI/**/ON`, encodings anidados (`%2575` → `%75` → `u`), charsets alternativos,
fragmentación, o reescrituras equivalentes que el normalizador no previó. Cada
mejora sube el costo de evadir, no lo lleva a cero. La defensa robusta no es una
firma mejor: es **no tener la vulnerabilidad** (consultas parametrizadas) y usar la
firma como alarma, no como muro.

**P3. Detectar por User-Agent: ¿por qué es una detección débil? ¿Qué mirarías en
lugar de "quién dice ser"?**
Porque la User-Agent la fija el cliente y se cambia con un flag (`curl -A ...`): es
autodeclarada y sin ningún costo falsificarla. Detecta al atacante descuidado, no al
ataque. En lugar de *quién dice ser* miraríamos *qué hace*: volumen y ritmo de
requests por IP, proporción de 404/403, recorrido secuencial o enumerativo de rutas
o IDs, payloads con estructura de ataque, horarios y geolocalización fuera de lo
normal, y reputación de la IP origen (en R5, una IP de salida de Tor). Señales de
comportamiento que el atacante no puede simplemente renombrar.

**P4. El R5: la intrusión estaba en el log. ¿Qué habría hecho que se detecte
automáticamente y no dependiera de que alguien la mire?**
La línea ya traía `ALERT[path-traversal]`: el dato existía, faltaba que algo
*actuara* sobre él. Lo que lo haría automático: **alerting** sobre eventos ALERT
(que una regla del SIEM levante un incidente apenas aparece, no que espere a un
humano), **correlación** (una IP externa de reputación Tor tocando `/etc/passwd` es
un patrón accionable), **enriquecimiento** con threat intel (marcar la IP), y
umbrales/anomalía que saquen esa línea del ruido de 120 GET benignos. La herramienta
no falló en R5: generó la alerta. Falló la **respuesta**: nadie la encaminó. Detección
sin alerting y sin un proceso que responda es un log que nadie lee.

**P5. Cierre del curso: recorriste ataque (05–08), agentes (09) y defensa (10).
¿Por qué un buen atacante tiene que entender al defensor, y viceversa?**
Porque son el mismo conocimiento visto desde dos lados. El atacante que entiende la
firma sabe exactamente qué reescribir para esquivarla; sin esa mirada defensiva,
tira payloads a ciegas y se delata. Y el defensor que entiende cómo ataca el otro
sabe qué firma es frágil, qué comportamiento vigilar y dónde va a aparecer la
evasión; sin esa mirada ofensiva, escribe reglas que buscan la cadena literal y deja
la puerta de al lado abierta. Todo el curso lo muestra: recon (05) es lo que el SOC
ve como barrido; la post-explotación (08) deja huellas que son material de análisis;
el agente (09) automatiza decisiones que amplifican tanto el ataque como la
detección. Red sin Blue es ruido que se delata; Blue sin Red es reglas que se
evaden. Pensar como el otro es, en los dos roles, la diferencia entre ejecutar y
entender.

## 4. Bitácora

Todo corrido desde la consola atacante (`cyberlab-attacker`) contra `phantomcorp`.

```bash
# Entorno
./ctf lab 10                 # levanta atacante + target (SOC monitoreado)

# R1 — Blue: acceder a la vista del SOC
curl -s http://phantomcorp/soc | head -6
#   -> "Acceso a la consola del SOC concedido. FLAG{soc_log_access}"

# R2 — Red: disparar una detección (la UA es lo más fácil de delatar)
curl -s -A sqlmap http://phantomcorp/
#   -> 403 "ALERTA IDS · firma 'scanner-ua' disparada ... FLAG{detection_triggered}"

# R3 — Blue: leer el ruleset
curl -s http://phantomcorp/soc/reglas
#   -> lista las 4 firmas; sqli-union exige un ESPACIO. FLAG{signature_ruleset}

# R4 — Red: evadir sqli-union sin el espacio literal (comentario SQL inline)
curl -s "http://phantomcorp/api?q=1%20union/**/select%201,2"
#   -> 200 "era maliciosa pero NINGUNA firma la detectó. FLAG{signature_evaded}"

# R5 — Blue: cazar la intrusión real escondida entre el tráfico benigno
curl -s http://phantomcorp/soc | grep ALERT
#   -> 185.220.101.42 GET /admin/../../etc/passwd ALERT[path-traversal]
#      # intrusion no atribuida -> FLAG{intrusion_in_the_noise}

# Contraste (para la tabla): firmas que SÍ detectan
curl -s --path-as-is "http://phantomcorp/admin/../../etc/passwd"   # path-traversal
curl -s "http://phantomcorp/.git/config"                           # git-probe

# Verificación
./ctf submit 10 R1 'FLAG{soc_log_access}'
./ctf submit 10 R2 'FLAG{detection_triggered}'
./ctf submit 10 R3 'FLAG{signature_ruleset}'
./ctf submit 10 R4 'FLAG{signature_evaded}'
./ctf submit 10 R5 'FLAG{intrusion_in_the_noise}'
./ctf status 10              # 5/5 (100%)
```
