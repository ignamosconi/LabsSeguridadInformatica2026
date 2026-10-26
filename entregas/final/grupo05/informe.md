# Informe de Penetration Test — PhantomCorp "Clientes"

**Cliente:** PhantomCorp S.A.  ·  **Auditor (grupo):** 05
**Integrantes:** Gastón Magni (nosungam) — Ignacio Mosconi (ignamosconi) —
Matías Presuttari (matiaspresuttari) — Valentino Terreno (vterreno)
**Fecha:** 2026-10-26  ·  **Tipo:** Caja negra  ·  **Alcance:** host
`phantomcorp` (lab, red `labnet` aislada)

## 0. Declaración de uso de IA

Se usó Claude Code (Anthropic) como asistente durante el engagement: para
automatizar la ejecución y el formateo de los comandos de `curl` contra el
target, y para redactar un primer borrador de este informe a partir de la
evidencia recolectada. Cada hallazgo fue **validado por el grupo** contra la
salida real de los comandos (ver `loot/bitacora.md` y `loot/ctf-status-final.txt`):
ningún CVSS ni ninguna flag fue copiado de `solucion.md` ni inventado — las
cuatro flags se obtuvieron ejecutando el ataque de punta a punta sobre el
contenedor `cyberlab-phantomcorp` y se confirmaron con `./ctf submit`.

---

## 1. Resumen ejecutivo

- **Qué se hizo:** una auditoría de caja negra sobre el sistema "Clientes"
  de PhantomCorp, sin credenciales ni documentación previas, siguiendo la
  cadena recon → enumeración → explotación → post-explotación → impacto.
- **Resultado global:** compromiso total. Se encontró un portal interno no
  enlazado, se evadió su autenticación por inyección SQL, se robó un token
  de una API interna desde un backup de configuración expuesto, y con ese
  token se logró ejecución remota de comandos como **root** dentro del host,
  llegando a exfiltrar el archivo con los datos de clientes.
- **Riesgo de negocio:** exposición completa de la base de clientes
  (≈48.210 registros con nombre, DNI y número de tarjeta) y control total del
  servidor que la aloja. En producción esto es una violación de datos
  personales y financieros con exposición regulatoria y reputacional directa.
- **Recomendación prioritaria:** parametrizar la consulta de login (la causa
  raíz que habilita toda la cadena) y sacar inmediatamente el endpoint de
  ejecución de comandos (`/api/reporte`) de producción; ningún "token" alcanza
  para justificar una interfaz que ejecuta shell arbitrario.

| Severidad | Cantidad de hallazgos |
|---|---|
| Crítica | 2 |
| Alta | 2 |
| Media | 1 |
| Baja | 1 |

---

## 2. Alcance y metodología

**Alcance:** únicamente el host `phantomcorp` dentro de la red aislada del
lab (`labnet`), levantado vía `./ctf lab final`. Ningún otro host, servicio
ni red fue tocado. Ventana: la fijada por la cátedra para el práctico final.
**Permitido:** recon, enumeración, explotación y post-explotación sobre el
target. **Prohibido y no realizado:** cualquier acción destructiva (no se
borraron ni modificaron datos; `id`, `cat` y lectura de archivos fueron las
únicas acciones ejecutadas vía RCE, sin escritura ni destrucción).

Metodología seguida (la misma cadena de las Unidades 5 a 10):

1. **Reconocimiento y enumeración** (Lab 05/06) — descubrimiento de
   superficie HTTP sin asumir nada: `robots.txt`, rutas no enlazadas.
2. **Explotación** (Lab 07) — abuso de una inyección SQL en el formulario de
   login para lograr un foothold de autenticación.
3. **Post-explotación** (Lab 08) — desde el acceso ganado, búsqueda de
   credenciales/secretos adicionales que amplíen el alcance (pivoting lógico,
   no de red).
4. **Impacto** (Lab 09/10 aplicados a la práctica) — uso del secreto robado
   para alcanzar ejecución de comandos y demostrar el impacto final sobre el
   activo más sensible del sistema (los datos de clientes).

Herramientas: `curl` desde la consola atacante del lab (`cyberlab-attacker`).
No hizo falta `sqlmap`/`gobuster`/`nmap` para esta cadena puntual — la
inyección y las rutas se confirmaron manualmente porque el objetivo es
mostrar la explotación precisa, no un barrido genérico.

---

## 3. Narrativa del ataque

```
recon/enum  ->  foothold  ->  loot  ->  impacto
```

Arrancamos sin nada: ni credenciales ni mapa del sitio. Lo primero que pedimos
fue `robots.txt`, por costumbre más que por expectativa — y ahí estaba:
`Disallow: /portal-rrhh`. Un `robots.txt` no es un control de acceso, es un
cartel que dice "no indexen esto", y lo leímos igual. `/portal-rrhh` resultó
ser un portal de RRHH con un formulario de login, y el HTML traía, en un
comentario, la primera flag — una confirmación de que el equipo de desarrollo
sabe que esto "no debería" estar expuesto, pero lo dejó ahí.

El formulario pedía usuario y contraseña que no teníamos. Probamos la
inyección SQL clásica en el campo usuario: `admin' -- `. Si el backend arma
la consulta por concatenación de strings (y lo hace), ese payload cierra el
literal del usuario y convierte el resto de la cláusula `WHERE` en un
comentario SQL, anulando el chequeo de password. Funcionó: el dashboard nos
recibió como admin, entregó la segunda flag, y — generosamente — nos dijo
dónde mirar después: `/backup/rrhh.conf`.

Ese backup, servido sin ninguna autenticación adicional, tenía credenciales
de base de datos y, más interesante, un `API_TOKEN` para una API interna de
"reportes" (`/api/reporte`), junto con la tercera flag y una pista explícita
de cómo usarlo (`?token=...&cmd=...`). El nombre del parámetro ya adelantaba
el problema.

Con el token en mano, el endpoint resultó ser exactamente lo que el nombre
del parámetro sugería: ejecución de comandos del sistema operativo. `cmd=id`
confirmó que corríamos como `root` dentro del contenedor. De ahí al archivo
que el propio hito buscaba fue un solo comando: `cat
/app/priv/clientes.db.txt`, que contenía la cuarta flag junto con la
confirmación de que ahí viven los 48.210 registros de clientes (nombre, DNI,
tarjeta) — los crown jewels del alcance.

Cuatro pasos, cada uno habilitado por una falla distinta, pero todos
reducibles a una sola idea: **el sistema confía en que el atacante no llega
al paso siguiente**, en vez de defender cada paso por sí mismo.

---

## 4. Hallazgos (detalle técnico)

### H-01 · Inyección SQL en el login del portal RRHH (bypass de autenticación)
- **Severidad:** Crítica · **CVSS:** `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N` —
  **9.1 (CVSS 3.1)**. Vector de red, sin complejidad ni privilegios ni
  interacción de usuario, acceso sin restricción a toda la base; no afecta
  disponibilidad directamente (por eso `A:N`), de ahí 9.1 y no 9.8-10.0.
- **Ubicación:** `POST /portal-rrhh/login` (también aliasado como
  `/portal/login`), parámetros `user` y `pass`.
- **Descripción:** el backend arma la consulta por concatenación directa de
  strings: `SELECT user, rol FROM users WHERE user='<user>' AND
  pass='<pass>'`. Cualquier entrada que incluya una comilla simple rompe la
  sintaxis esperada, y un comentario SQL (`-- `) anula el resto de la
  cláusula.
- **Evidencia (reproducible):**
  ```bash
  curl -s -X POST http://phantomcorp/portal-rrhh/login \
    --data-urlencode "user=admin' -- " --data-urlencode 'pass=x'
  # -> "Bienvenido admin. Dashboard RRHH." + FLAG{final_sqli_foothold}
  ```
- **Impacto:** bypass total de autenticación sin conocer ninguna
  credencial. Es la puerta de entrada de toda la cadena: sin este hallazgo no
  hay foothold, y sin foothold no hay acceso al resto del sistema.
- **Remediación:** usar **consultas parametrizadas / prepared statements**
  (`cursor.execute("... WHERE user=? AND pass=?", (user, pass))`) en lugar de
  interpolar strings. Adicionalmente: no comparar contraseñas en texto plano
  contra la DB (hashearlas, como se trabajó en el Lab 03), y no asumir que el
  front valida nada — la validación de verdad es server-side.

### H-02 · Ejecución remota de comandos en `/api/reporte` (command injection)
- **Severidad:** Crítica · **CVSS:** `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` —
  **10.0 (CVSS 3.1)**. El parámetro `cmd` se ejecuta en una shell del sistema
  sin ninguna lista blanca ni sanitización: control total del contenedor,
  incluida la capacidad de modificar o borrar (aunque no lo hicimos, por las
  reglas del engagement).
- **Ubicación:** `GET /api/reporte?token=...&cmd=...`.
- **Descripción:** el valor de `cmd` se pasa directo a `os.popen(cmd)`. El
  único control es que `token` matchee un valor fijo — una vez conocido ese
  valor, el endpoint es una shell remota sin restricciones.
- **Evidencia (reproducible):**
  ```bash
  curl -s 'http://phantomcorp/api/reporte?token=phantom-api-7c1e&cmd=id'
  # -> uid=0(root) gid=0(root) groups=0(root)
  curl -s --data-urlencode 'cmd=cat /app/priv/clientes.db.txt' -G \
    'http://phantomcorp/api/reporte' --data-urlencode 'token=phantom-api-7c1e'
  # -> clientes: 48210 registros (nombre, DNI, tarjeta). FLAG{final_crown_jewels}
  ```
- **Impacto:** control total del host (el proceso corre como root dentro del
  contenedor) y exfiltración confirmada de los datos de clientes — el peor
  escenario del alcance.
- **Remediación:** eliminar la ejecución de comandos del sistema a partir de
  input de usuario. Si el endpoint necesita generar un reporte, que invoque
  una función específica con parámetros tipados (whitelisting de reportes
  predefinidos), nunca una shell. Un token estático nunca debe ser el único
  control de autorización sobre una funcionalidad de este riesgo — además,
  rotarlo y no commitearlo/servirlo en ningún archivo de configuración.

### H-03 · Backup de configuración expuesto sin autenticación, con secretos en texto plano
- **Severidad:** Alta · **CVSS:** `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N` —
  **7.5 (CVSS 3.1)**. Divulgación de información sin requerir ningún
  privilegio ni interacción.
- **Ubicación:** `GET /backup/rrhh.conf`.
- **Descripción:** un archivo de configuración/backup queda accesible por
  HTTP sin control de acceso, y contiene credenciales de base de datos
  (`DB_USER`/`DB_PASS`) y el token de una API interna en texto plano.
- **Evidencia (reproducible):**
  ```bash
  curl -s http://phantomcorp/backup/rrhh.conf
  # -> DB_USER=rrhh_app / DB_PASS=Rh-2026 / API_TOKEN=phantom-api-7c1e
  #    + FLAG{final_token_looted}
  ```
- **Impacto:** es el eslabón de post-explotación: convierte un foothold web
  en credenciales reutilizables y en el token que habilita H-02. Es el típico
  "secreto de más" que amplifica cualquier acceso previo.
- **Remediación:** los backups y archivos de configuración nunca deben
  quedar bajo una ruta servida por el webserver de la aplicación; moverlos
  fuera del document root o detrás de autenticación/red interna. Los
  secretos no van en archivos de texto plano versionados ni servidos: usar
  un vault de secretos (o como mínimo variables de entorno inyectadas en
  runtime, nunca expuestas vía HTTP) y rotarlos periódicamente.

### H-04 · Portal interno sin control de acceso, descubierto vía `robots.txt`
- **Severidad:** Alta · **CVSS:** `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` —
  **7.5 (CVSS 3.1)**. Nota: puntaje ajustado al contexto — el portal en sí
  solo expone un formulario de login y un comentario con metadatos, pero es
  la puerta a H-01, por lo que se lo trata como hallazgo de alta prioridad
  pese a no divulgar datos sensibles por sí mismo.
- **Ubicación:** `/portal-rrhh` (referenciado desde `robots.txt`); HTML con
  comentario interno.
- **Descripción:** un portal administrativo de RRHH es alcanzable
  públicamente, sin segmentación de red ni control de acceso previo (ni
  siquiera un 404 genérico), y su única protección es "no estar linkeado" —
  lo cual `robots.txt` contradice activamente, ya que ese archivo existe
  justamente para decirle a los crawlers qué rutas existen y evitar.
- **Evidencia (reproducible):**
  ```bash
  curl -s http://phantomcorp/robots.txt        # -> Disallow: /portal-rrhh
  curl -s http://phantomcorp/portal-rrhh       # -> formulario + FLAG{final_recon_portal}
  ```
- **Impacto:** "seguridad por oscuridad" como único control. Expone la
  superficie de ataque completa (H-01) a cualquiera en la red, sin exigir
  ni siquiera estar en una VPN o segmento interno.
- **Remediación:** segmentar los portales administrativos en una red/VLAN
  interna no alcanzable desde el mismo origen que el sitio público, sumado a
  autenticación robusta (y, siguiendo el Lab 03, 2FA/TOTP). No depender de
  que una ruta "no esté linkeada" — y jamás anunciarla en `robots.txt`.

### H-05 · Comentarios/metadatos de depuración en HTML de producción
- **Severidad:** Media · **CVSS:** `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` —
  **5.3 (CVSS 3.1)**.
- **Ubicación:** comentario HTML en la respuesta de `/portal-rrhh`.
- **Descripción:** el HTML servido incluye comentarios internos (en este
  caso, con información de depuración/flag) que no deberían llegar al
  cliente en un entorno real.
- **Evidencia (reproducible):** ver respuesta de `curl -s
  http://phantomcorp/portal-rrhh` en H-04.
- **Impacto:** por sí solo es bajo impacto directo, pero es un patrón de
  higiene: cualquier dato de depuración dejado en el frontend es información
  gratis para un atacante durante el recon.
- **Remediación:** build de producción sin comentarios de debug; revisar el
  pipeline de CI/CD para que strip de comentarios/metadatos sea parte del
  build, no una convención manual.

### H-06 · Mensajes de error que revelan la consulta SQL subyacente
- **Severidad:** Baja · **CVSS:** `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` —
  **5.3 (CVSS 3.1)** acotado por el bajo impacto adicional dado que H-01 ya
  es explotable sin necesidad de este detalle.
- **Ubicación:** `POST /portal-rrhh/login` ante un payload que rompe la
  sintaxis SQL sin comentar el resto de la query (p. ej. una sola comilla
  suelta).
- **Descripción:** el backend captura la excepción de SQLite y devuelve el
  mensaje de error crudo (`Error SQL: <excepción>`) en la respuesta HTTP, en
  lugar de un error genérico.
- **Evidencia (reproducible):**
  ```bash
  curl -s -X POST http://phantomcorp/portal-rrhh/login \
    --data-urlencode "user=admin'" --data-urlencode 'pass=x'
  # -> "Error SQL: ..." con el mensaje de sqlite3
  ```
- **Impacto:** acelera la confirmación y el ajuste de una inyección SQL
  (aquí no hizo falta, porque H-01 se explotó a ciegas en el primer intento,
  pero en un caso más defendido esto facilita mucho el diagnóstico al
  atacante).
- **Remediación:** manejar las excepciones del lado del servidor y devolver
  siempre un mensaje genérico ("credenciales inválidas") al cliente,
  logueando el detalle real solo server-side.

---

## 5. Conclusión

El sistema "Clientes" de PhantomCorp quedó completamente comprometido: desde
cero conocimiento y cero credenciales se llegó a ejecución de comandos como
root y exfiltración de la base de clientes completa. Lo más relevante no es
la cantidad de pasos (cuatro) sino que **cada paso individual era, por sí
solo, prevenible con prácticas básicas** — nada de esta cadena requirió un
exploit sofisticado ni un 0-day.

El eslabón que, de haberse corregido primero, habría cortado la cadena antes
es **H-01 (la inyección SQL del login)**: sin ese bypass no hay foothold, y
sin foothold el atacante nunca llega al backup (H-03) ni, por lo tanto, al
token que habilita la RCE (H-02). Dicho de otro modo: el "crown jewel" del
sistema terminó protegido, en la práctica, únicamente por una consulta SQL
mal escrita. Dicho esto, **H-02 (la RCE) es el hallazgo de mayor severidad
aislada**: aun si se hubiera llegado al token por otra vía, un endpoint que
ejecuta shell arbitrario sobre un token estático es inaceptable en
cualquier escenario.

La postura de seguridad general es débil: no hay defensa en profundidad —
una sola falla en el primer paso destapa toda la cadena — y se repite un
patrón de "seguridad por oscuridad" (portal no linkeado, backup "escondido"
en una ruta no obvia) en lugar de controles de acceso reales. Recomendamos
priorizar, en este orden: (1) parametrizar toda consulta SQL dinámica del
sistema, (2) retirar `/api/reporte` o reescribirlo sin invocación de shell,
(3) sacar backups y secretos de rutas servidas por el webserver, y (4)
segmentar el portal administrativo detrás de autenticación y red interna.

---

## 6. Anexo

Bitácora completa de comandos: [`loot/bitacora.md`](loot/bitacora.md).
Salida de `./ctf status final` (4/4 hitos): [`loot/ctf-status-final.txt`](loot/ctf-status-final.txt).
