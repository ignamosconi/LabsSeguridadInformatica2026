# Informe — Laboratorio 05 · Reconocimiento

**Grupo:** 05
**Integrantes:**

- Matías Presuttari — [matiaspresuttari](https://github.com/matiaspresuttari)
- Valentino Terreno — [vterreno](https://github.com/vterreno)
- Ignacio Mosconi — [ignamosconi](https://github.com/ignamosconi)
- Gastón Magni — [nosungam](https://github.com/nosungam)

**Fecha:** 11/09/2026

---

## 0. Declaración de uso de IA

Usamos un asistente de IA (Claude, de Anthropic) como apoyo en dos frentes,
siempre con validación manual del grupo:

- **Operación de las herramientas y redacción.** El asistente nos ayudó a
  ordenar la secuencia de recon (nmap → banner grabbing → análisis de headers →
  enumeración de rutas), a redactar este informe y a completar las dos funciones
  del `escaner.py` opcional. Todo lo que sigue lo **reprodujimos nosotros** dentro
  de la consola del atacante contra `phantomcorp`; las salidas pegadas son las de
  nuestras corridas (ver `evidencia/`).
- **Datos de CVE/CVSS.** Los números de CVE, sus scores y vectores los tomamos
  de NVD (indicando cuando el score es del CNA y no de NVD, como en
  CVE-2024-34069) y los **verificamos uno por uno** contra la versión
  que efectivamente devolvió el objetivo. No dimos por buena ninguna afirmación
  del asistente sin contrastarla con la evidencia del lab o con la fuente citada.

Cada cifra de este informe está marcada como *medida* (reproducida localmente) o
*publicada* (con fuente y fecha).

---

## 1. Parte práctica — flags capturadas

Las 5 flags se obtuvieron **operando las herramientas** contra `phantomcorp`, no
leyendo archivos del target. Salida de `./ctf status 05`:

```
  ╭────────────────────────────────────────────────────────────╮
  │                     PROGRESO · LAB 05                      │
  ╰────────────────────────────────────────────────────────────╯

   ✓  R1     Puerto oculto en rango alto (barrido completo)
   ✓  R2     Banner grabbing del servicio FTP
   ✓  R3     Fuga de informacion en headers HTTP
   ✓  R4     Enumeracion de rutas via robots.txt
   ✓  R5     Servicio dev expuesto en produccion

  ██████████████████████████████  5/5 (100%)

[ OK ] ¡Lab 05 COMPLETO! Ponete las pilas con la próxima unidad.
```

| Reto | Técnica | Flag | Cómo la sacamos |
|---|---|---|---|
| R1 | Barrido completo + banner en puerto alto | `FLAG{high_port_secret_service}` | `ncat -w3 phantomcorp 31337` |
| R2 | Banner grabbing FTP | `FLAG{banner_grab_proftpd_135}` | `ncat -w3 phantomcorp 21` |
| R3 | Fuga en headers HTTP | `FLAG{http_headers_leak_info}` | `curl -sI http://phantomcorp/` |
| R4 | Enumeración de rutas | `FLAG{recon_hidden_path}` | `robots.txt` → `GET /panel-interno-9x2f` |
| R5 | Servicio dev expuesto | `FLAG{dev_service_exposed}` | `curl -s http://phantomcorp:8080/status` |

---

## 2. Mapa de superficie de ataque

Puertos abiertos según `nmap -Pn -sV -p- phantomcorp` (*medida* — 4/65535
puertos abiertos; corrida completa en `evidencia/nmap-full-sv.txt`):

| Puerto | Servicio | Versión (evidencia) | ¿Cómo lo identificaste? | CVE relevante | CVSS | Criticidad | Justificación (contra ESTE caso) |
|---|---|---|---|---|---|---|---|
| 21 | FTP | **ProFTPD 1.3.5** — banner `220 ProFTPD 1.3.5 Server (PhantomCorp FTP)` (*medida*) | Banner grabbing con `ncat` + confirmado por `nmap -sV` | **CVE-2015-3306** (módulo `mod_copy`) | **10.0** CVSSv2 (*publicada*, NVD) | **Crítica** | La versión exacta 1.3.5 es la afectada por `mod_copy`: `SITE CPFR/CPTO` permite lectura/escritura de archivos arbitrarios → RCE sin autenticación. El banner por sí solo ya delata que es explotable. |
| 80 | HTTP | **PhantomServer/2.4.1** con `X-Powered-By: PhantomCMS 2.4.1` (*medida*) | `curl -I` (headers) + `nmap -sV` | Ninguno aplicable | — | **Media** | No hay CVE: es software del propio lab, no aparece en NVD. El problema real es **fuga de información**: los headers cantan producto y versión, y el HTML tiene un comentario `TODO(infra): sacar el panel interno de produccion`. Baja la barrera para el siguiente atacante. |
| 8080 | HTTP (dev API) | **Werkzeug 2.0.1 (Python 3.9.2)** — banner `Server: Werkzeug/2.0.1 Python/3.9.2` (*medida*) | `nmap -sV` + `curl -I`; el body responde `phantom-dev-api` y `/status` da `debug:true` | **CVE-2024-34069** (Werkzeug < 3.0.3, debugger) — *aplica a la versión, bajo condiciones* | **7.5** CVSSv3.1 `AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:H` (*publicada*; score del CNA GitHub, listado en NVD — NVD no asignó score propio) | **Alta** | Es el **servidor de desarrollo de Werkzeug corriendo en “producción”**: `version: 0.9.3-DEV` y `debug:true` expuestos en `/status`. La versión 2.0.1 cae en el rango afectado por CVE-2024-34069, pero ese CVE **no es explotable de forma directa**: exige que el debugger esté activo, engañar a un desarrollador para que use un dominio controlado por el atacante (`UI:R`, `AC:H`) y que ingrese el PIN. Por eso no la marcamos Crítica. La criticidad Alta la sostiene la mala configuración: aunque no hubiera CVE, un dev server con debug nunca debería mirar a la red. |
| 31337 | TCP a medida | **“PhantomCorp maintenance shell v0.1”** — banner (*medida*); nmap lo marca `Elite?` sin fingerprint | Banner grabbing con `ncat` | No clasificable | — | **Alta (indeterminada)** | Servicio de mantenimiento a medida, **sin versión pública ni CVE asociado**: honestamente **no podemos clasificarlo por CVE**. Pero un “maintenance shell” escuchando en un puerto alto, sin autenticación visible, es superficie de ataque de por sí. |

**Evidencia de respaldo** (`nmap -Pn -sV -p- phantomcorp`, extracto):

```
PORT      STATE SERVICE VERSION
21/tcp    open  ftp     ProFTPD 1.3.5
80/tcp    open  http    PhantomServer/2.4.1
8080/tcp  open  http    Werkzeug httpd 2.0.1 (Python 3.9.2)
31337/tcp open  Elite?
```

Banners y headers que sostienen la tabla:

```
# 21/tcp (ncat)
220 ProFTPD 1.3.5 Server (PhantomCorp FTP) [::ffff:0.0.0.0]

# 80/tcp (curl -I)
Server: PhantomServer/2.4.1
X-Powered-By: PhantomCMS 2.4.1
X-Backend-Flag: FLAG{http_headers_leak_info}

# 8080/tcp (curl /status)
{"service":"phantom-dev-api","version":"0.9.3-DEV","debug":true, ...}

# 31337/tcp (ncat)
PhantomCorp maintenance shell v0.1 -- acceso no autorizado prohibido
```

Corridas completas en `evidencia/` (`nmap-full-sv.txt`, `r1-31337.txt`,
`r2-ftp.txt`, `r3-headers.txt`, `r4-robots.txt`, `r4-panel.txt`,
`r5-8080-head.txt`, `r5-status.txt`).

---

## 3. Preguntas de análisis

**P1 — El puerto que el escaneo default se perdió.**
Acá tenemos que ser honestos con la evidencia. El `nmap -Pn phantomcorp`
(top-1000) **sí** listó los cuatro puertos, incluidos el 8080 y el 31337
(`evidencia/nmap-default.txt`). La razón es que los “1000 puertos default” de
nmap **no son el rango 1–1000**: son los 1000 puertos **más frecuentes** según su
base de estadísticas, y tanto el 8080 como el 31337 son puertos “célebres” que
entran en esa lista. Donde el corte por rango **sí** falla es en un escáner
ingenuo: nuestro `escaner.py` con rango `1-1000` (o su default `1-1024`) sólo
encontró el 21 y el 80, porque el 8080 y el 31337 caen **por encima** de ese tope
(`evidencia/escaner-banner.txt` y la corrida `--puertos 1-1000`). La lección
operativa: **nunca confiar en un rango acotado**. `nmap -p-` recorre los 65535 y
es la única garantía de completitud; un “top-N” o un “1-1000” pueden dejar
servicios afuera según cómo estén distribuidos los puertos.

**P2 — El servicio dev en producción.**
El 8080 grita “desarrollo” por varias vías concretas que medimos: (1) el header
`Server: Werkzeug/2.0.1 Python/3.9.2` — Werkzeug es el **servidor de desarrollo**
de Flask, explícitamente desaconsejado para producción por su propia
documentación; (2) el endpoint `/status` devuelve `"version":"0.9.3-DEV"` y
`"debug":true`. Es un problema **aunque no hubiera un CVE**: si ese `debug`
corresponde al modo debug de Flask/Werkzeug, está habilitado el **debugger
interactivo**, que ante cualquier excepción muestra el traceback y ofrece una
consola Python protegida sólo por un PIN — o sea, a un paso de ejecución de
código. (CVE-2024-34069 es una variante de ese riesgo, pero con condiciones
exigentes: requiere engañar a un desarrollador para que use un dominio del
atacante e ingrese el PIN; no la presentamos como explotable directamente
contra PhantomCorp.) Sumado a que un
dev server no está pensado para aguantar carga ni ataques, exponerlo a la red es
regalar una vía de entrada. La ausencia de CVE no lo vuelve seguro: la
**mala configuración** ya es la vulnerabilidad.

**P3 — La ironía de `robots.txt`.**
`robots.txt` se creó para **SEO**: le dice a los crawlers (Google, Bing) qué
rutas **no** indexar. Pero no es un control de acceso — es una sugerencia que el
servidor publica **en claro para cualquiera**. La ironía es que, para “esconder”
una ruta de los buscadores, el administrador termina **publicando la lista de sus
rutas sensibles** justo a quien peor le viene: el atacante. En PhantomCorp el
`robots.txt` tenía `Disallow: /panel-interno-9x2f` y hasta un comentario
(`# ...sigue accesible desde afuera. Migrar a VPN.`). Le pedimos la ruta con
`curl` y entramos directo al panel (R4). Un control pensado para
**visibilidad en buscadores** se convirtió en un **mapa de recon**.

**P4 — Pasivo vs. activo.**
Todo lo que hicimos en este lab fue recon **activo**: cada `nmap`, cada `ncat` al
21/31337 y cada `curl` al 80/8080 **abrió una conexión TCP contra PhantomCorp**,
o sea interactuó con el objetivo y **quedaría en sus logs** (el servidor web
registra cada GET a `/robots.txt`, `/panel-interno-9x2f` y `/status`; el FTP
registra la conexión al 21; el barrido `-p-` deja 65535 intentos de conexión, un
patrón escandaloso en cualquier IDS). Recon **pasivo** hubiera sido no tocar el
objetivo: `whois` del dominio, registros DNS públicos, certificados
(crt.sh), Google dorks, filtraciones. Como `phantomcorp` es un host interno sin
DNS público, el pasivo lo practicamos aparte contra `scanme.nmap.org` (autorizado
por Nmap). En un engagement real se arranca pasivo justamente **para no dejar la
huella** que nosotros dejamos acá.

**P5 — Ahora sos el defensor.**
Elegimos dos hallazgos y una medida concreta para cada uno:

1. **ProFTPD 1.3.5 en el 21 (CVE-2015-3306).** Medida: **actualizar ProFTPD** a
   una versión con el parche de `mod_copy` (≥ 1.3.5a / 1.3.6) o, si no se puede,
   **deshabilitar `mod_copy`** en la config (`LoadModule` fuera). Y si el FTP no
   es necesario de cara a la red, cerrarlo por firewall / migrar a SFTP. Mitiga
   directamente la RCE no autenticada.
2. **Dev API de Werkzeug en el 8080 con `debug:true`.** Medida: **sacar el
   servicio de la red** (no exponer el puerto 8080 al perímetro; que sólo escuche
   en `localhost` o detrás de VPN) y **apagar `debug`** en cualquier despliegue
   accesible; para producción real, servir la app detrás de un WSGI de producción
   (gunicorn/uWSGI) tras un reverse proxy, nunca con el server de desarrollo.
   Reduce la superficie eliminando el debugger y el endpoint `/status`.

Bonus de higiene: quitar los headers que filtran versión (`Server`,
`X-Powered-By`) y limpiar el `robots.txt` de rutas sensibles (el ocultamiento se
hace con **autenticación**, no con `Disallow`).

---

## 4. Bitácora de comandos

Reproducible desde la raíz del repo. El recon se hace **dentro de la consola del
atacante**.

```bash
# --- Levantar el entorno (desde la raíz del repo) ---
make setup                 # una sola vez: construye la consola del atacante
make lab N=05              # levanta atacante + target phantomcorp
make shell                 # entrar a la consola (todo lo de abajo corre acá dentro)

# --- Recon activo contra phantomcorp ---
ping -c1 phantomcorp                       # confirmar alcance
nmap -Pn phantomcorp                       # escaneo default (top-1000)
nmap -Pn -sV -p- phantomcorp               # barrido COMPLETO + versiones (la base del mapa)

# R2 — banner grabbing FTP
ncat -w3 phantomcorp 21 </dev/null
# R1 — banner del puerto alto
ncat -w3 phantomcorp 31337 </dev/null
# R3 — fuga en headers
curl -sI http://phantomcorp/
# R4 — enumeración de rutas
curl -s http://phantomcorp/robots.txt
curl -s http://phantomcorp/panel-interno-9x2f
# R5 — dev service expuesto
curl -sI http://phantomcorp:8080/
curl -s  http://phantomcorp:8080/status

# --- Entregar flags y ver progreso (desde la raíz del repo, fuera de la consola) ---
./ctf submit 05 R1 'FLAG{high_port_secret_service}'
./ctf submit 05 R2 'FLAG{banner_grab_proftpd_135}'
./ctf submit 05 R3 'FLAG{http_headers_leak_info}'
./ctf submit 05 R4 'FLAG{recon_hidden_path}'
./ctf submit 05 R5 'FLAG{dev_service_exposed}'
./ctf status 05

# --- Ampliación opcional: nuestro mini-escáner en Python puro ---
python3 entregas/lab05/grupo05/src/escaner.py phantomcorp --puertos 1-1000
python3 entregas/lab05/grupo05/src/escaner.py phantomcorp --puertos 21,80,8080,31337 --banner
```

> Uso responsable: todo esto se ejecutó **exclusivamente** contra los contenedores
> de la cátedra dentro de nuestra máquina. Correr recon activo contra sistemas de
> terceros sin autorización es delito en Argentina (Ley 26.388).
