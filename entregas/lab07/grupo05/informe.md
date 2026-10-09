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
| Command injection (R3) | `host=127.0.0.1; cat /app/flags/cmdi.txt` | `ping -c1 127.0.0.1; cat /app/flags/cmdi.txt` ejecutado por el shell del servidor | Ejecución de comandos arbitrarios (RCE) con los privilegios del proceso web | No invocar un shell: usar una librería de red (sockets, `ping3`) o `subprocess` con lista de argumentos y sin `shell=True`; validar `host` contra una whitelist (IP/hostname) |
| Path traversal (R4) | `archivo=../flags/lfi.txt` | `open("public/" + "../flags/lfi.txt")` → resuelve a `flags/lfi.txt`, fuera de `public/` | Lectura de archivos arbitrarios del servidor fuera del directorio público | Normalizar la ruta resultante (`os.path.realpath`) y rechazar si no queda dentro del directorio permitido; además, lista blanca de nombres de archivo descargables |
| IDOR (R5) | `GET /perfil?id=1` (perfil propio es `id=3`) | El servidor responde el recurso `perfil/1` sin verificar que `1` pertenezca al usuario autenticado | Lectura de datos privados de otro usuario (nota privada del `admin`) | Verificar en el servidor, con el usuario autenticado de la sesión, que el objeto solicitado le pertenece (o que su rol lo autoriza) — nunca confiar en que el cliente "no va a cambiar el id" |

## 3. Preguntas de análisis

### P1 — por qué funciona el bypass (con la query)

La consulta del login se arma concatenando el input tal cual:

```sql
SELECT user, rol FROM users WHERE user='<user>' AND pass='<pass>'
```

Con `user = admin' -- ` y `pass = x`, la consulta final queda:

```sql
SELECT user, rol FROM users WHERE user='admin' -- ' AND pass='x'
```

El `--` es el marcador de comentario de línea en SQL (en el dialecto usado por
el motor del lab, seguido de un espacio). Todo lo que sigue en la línea —
incluida la comilla de cierre del `user` que faltaba, el `AND pass='x'` y la
comilla final— queda comentado y el motor nunca lo evalúa. La consulta
efectiva que se ejecuta es:

```sql
SELECT user, rol FROM users WHERE user='admin'
```

Esto devuelve la fila de `admin` sin haber verificado jamás la contraseña: el
chequeo de `pass` no es que falle, es que **nunca se ejecuta**. El servidor,
al recibir una fila, asume autenticación correcta.

### P2 — por qué el UNION necesita igual número de columnas

`UNION` en SQL combina el resultado de dos `SELECT` en una sola tabla de
salida, fila a fila. Para que el motor pueda alinear esas filas necesita que
ambas consultas devuelvan la **misma cantidad de columnas** (y, en los motores
más estrictos, tipos compatibles columna a columna). Si la consulta original
trae 2 columnas y la nuestra trae 3, el motor no sabe cómo "empalmar" las
filas y devuelve un error en lugar de resultados.

Si no supiéramos de antemano cuántas columnas tiene la consulta original, se
descubre por fuerza bruta incremental con `ORDER BY`:

```text
q=Router' ORDER BY 1 -- 
q=Router' ORDER BY 2 -- 
q=Router' ORDER BY 3 -- 
```

Se va subiendo el número hasta que el motor responde con un error del tipo
*"ORDER BY term out of range"* (que fue exactamente el error que obtuvimos al
probar con `3`, confirmando que la consulta real trae 2 columnas). El número
anterior al que rompe es la cantidad real de columnas, y ese mismo número es
el que hay que replicar en el `UNION SELECT`.

### P3 — qué sigue después del RCE

Con ejecución de comandos (R3) un atacante real no se queda en "leí un
archivo": el siguiente paso lógico es **afianzar y expandir** el acceso,
exactamente el tema del Lab 08 (post-explotación):

- Reconocimiento del entorno comprometido: `whoami`, `id`, `uname -a`, ver qué
  procesos corren y con qué privilegios corre la app web.
- Búsqueda de credenciales y secretos en el filesystem (archivos de
  configuración, variables de entorno, historiales de shell).
- Establecer **persistencia** (una cron job, una clave SSH agregada, un
  usuario nuevo) para no depender de que la vulnerabilidad original siga
  abierta.
- **Pivoting**: desde este host, explorar la red interna en busca de otros
  sistemas alcanzables que no estén expuestos directamente a Internet.
- Escalar privilegios si el proceso web corre con un usuario sin privilegios
  (por ejemplo, buscando binarios SUID mal configurados).

### P4 — por qué parametrizar mata la SQLi de raíz

Una consulta parametrizada (*prepared statement*) separa, a nivel del
protocolo con la base de datos, **la estructura de la consulta** del
**valor de los datos**. El motor primero recibe y compila la plantilla:

```sql
SELECT user, rol FROM users WHERE user = ? AND pass = ?
```

y *después* recibe los valores (`admin' -- `, `x`) para llenar esos
placeholders. En ningún momento esos valores se insertan como texto SQL que el
parser vuelva a interpretar: se tratan como **datos literales**, sin importar
qué caracteres contengan. Una comilla, un `--` o un `UNION` dentro del valor
nunca se convierte en sintaxis SQL, porque el parser ya terminó de leer la
estructura de la consulta antes de que el valor exista en esa posición.

Esto es categóricamente distinto de "escapar comillas" (sanitizar), que sigue
operando sobre un único string donde datos y código conviven: siempre puede
aparecer un caso borde o una codificación que el escapado no contempló.
Parametrizar no mitiga el riesgo, lo elimina: la inyección deja de ser
posible porque la frontera datos/código nunca se vuelve a construir
concatenando texto.

### P5 — dónde va el control de acceso (IDOR)

El control de acceso **no puede** depender de que el cliente "no cambie el
id" porque el cliente está completamente fuera del control del servidor: es
simplemente texto que viaja en una URL, y cualquier usuario puede editarlo a
mano, con `curl`, con las herramientas de desarrollador del navegador o con un
proxy como Burp. Confiar en el id que manda el cliente es confiar en que el
atacante va a portarse bien — exactamente la regla de oro del Lab 07: "toda
entrada del usuario es una mentira potencial".

La verificación tiene que ocurrir **en el servidor**, usando la identidad que
el servidor ya conoce de forma confiable (la sesión autenticada), no el
parámetro que llega en la request:

```python
# mal: confía en el id del cliente
perfil = db.get_perfil(request.args["id"])

# bien: el servidor decide a quién pertenece el recurso
usuario_actual = sesion.usuario_autenticado
perfil = db.get_perfil(request.args["id"])
if perfil.user_id != usuario_actual.id and not usuario_actual.es_admin:
    return 403
```

El id en la URL puede seguir existiendo (es útil para navegar), pero el
servidor tiene que validar, en cada request, que el recurso solicitado
pertenece a quien está autenticado o que su rol lo autoriza explícitamente.

