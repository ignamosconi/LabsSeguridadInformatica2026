# Mini-research — Laboratorio 05

**Grupo:** 05
**Tema elegido:**

- [x] **A.** El CVE-2015-3306 de ProFTPD 1.3.5: qué es el `mod_copy`, cómo se
  explota el comando `SITE CPFR/CPTO`, y por qué un banner de versión alcanza
  para saber que un servidor es vulnerable.
- [ ] **B.** Tipos de escaneo de `nmap`.
- [ ] **C.** OSINT y recon pasivo.
- [ ] **D.** El estándar CVSS.

Elegimos el tema A porque es **exactamente el hallazgo crítico de nuestro mapa**:
el puerto 21 de PhantomCorp corre ProFTPD 1.3.5, y queríamos entender qué tan
grave es de verdad y por qué el banner solo ya nos dio la respuesta.

---

## Desarrollo

### Qué es `mod_copy`

ProFTPD es un servidor FTP modular: su funcionalidad se arma con módulos.
`mod_copy` es uno de ellos y agrega dos comandos **no estándar** al protocolo,
expuestos vía `SITE`: `SITE CPFR` (*copy from*, el origen) y `SITE CPTO` (*copy
to*, el destino). La idea legítima es copiar archivos **dentro del servidor** sin
tener que bajarlos y volver a subirlos — cómodo para mover backups grandes, por
ejemplo.

### El bug (CVE-2015-3306)

El problema, según la descripción de NVD, es simple y de manual: *«The mod_copy
module in ProFTPD 1.3.5 allows remote attackers to read and write to arbitrary
files via the site cpfr and site cpto commands»* (NVD). Es decir, **`mod_copy`
no verifica autenticación** antes de ejecutar `CPFR/CPTO`. Un cliente que ni
siquiera hizo login puede pedirle al servidor que copie cualquier archivo del
filesystem a cualquier destino. La debilidad está clasificada como **CWE-284 —
Improper Access Control** (control de acceso incorrecto): la operación existe,
pero el control que debería restringirla no está.

La gravedad no es teórica. El score es **CVSSv2 10.0 (AV:N/AC:L/Au:N/C:C/I:C/A:C)
— el máximo posible** (NVD): explotable por **red** (`AV:N`), de **baja
complejidad** (`AC:L`), **sin autenticación** (`Au:N`) y con impacto **completo**
en confidencialidad, integridad y disponibilidad. Y no es sólo un número teórico:
su **EPSS es 96.75 %** (percentil 100 según la GitHub Advisory Database), o sea
que está entre las vulnerabilidades con mayor probabilidad de ser explotadas
activamente. Publicado el **18/05/2015**.

### De "copiar archivos" a ejecución remota de código (RCE)

Leer y escribir archivos arbitrarios ya es grave, pero la cadena hasta **RCE** es
directa y es la que usan los exploits públicos:

1. `mod_copy` corre con los privilegios del proceso ProFTPD (por defecto, el
   usuario `nobody`).
2. El atacante usa `SITE CPFR /proc/self/cmdline` — un truco clásico: la
   pseudo-ruta `/proc/self/cmdline` contiene la línea de comando del propio
   proceso, y el atacante la "envenena" mandando su payload como parte del
   comando FTP.
3. Con `SITE CPTO /ruta/al/webroot/shell.php` copia ese contenido (un webshell
   PHP) dentro del directorio servido por el servidor web del mismo host.
4. Pide `http://objetivo/shell.php?cmd=...` y ya tiene ejecución de comandos.

Todo esto **sin credenciales**. Existen exploits listos: un módulo de Metasploit
(`exploit/unix/ftp/proftpd_modcopy_exec`, Rapid7) y varios PoC en Exploit-DB y
GitHub, además de contenedores vulnerables para practicar. Es de los casos donde
"tener el CVE" equivale casi a "tener el shell".

### Por qué el banner de versión alcanza para saber que es vulnerable

Esta es la parte que conecta con el recon del lab. La vulnerabilidad **está atada
a una versión concreta** (1.3.5 con `mod_copy` cargado, que en esa release venía
habilitado por defecto). Cuando en el R2 hicimos banner grabbing y el 21 nos
contestó `220 ProFTPD 1.3.5 Server`, ese texto **es la evidencia**: no hace falta
tocar nada más para clasificar el servicio como crítico, porque el número de
versión mapea 1:1 contra el CVE. Ese es el corazón del reconocimiento —
*identificar* y *clasificar*, no sólo *descubrir*. Un puerto 21 abierto no es un
hallazgo; "el 21 corre ProFTPD 1.3.5, vulnerable a CVE-2015-3306 (RCE no
autenticada, CVSS 10.0)" **sí** lo es.

La contracara defensiva: publicar la versión en el banner **es** parte del
problema. Un ProFTPD que no cantara su versión obligaría al atacante a testear a
ciegas; cantándola, le regala el diagnóstico. La mitigación del bug en sí es
**deshabilitar `mod_copy`** o **actualizar a una release parcheada** (la 1.3.5a y
la serie 1.3.6 corrigieron el acceso sin autenticación); y, de fondo, **no exponer
el FTP** a la red si no hace falta.

---

## Fuentes

- NVD — CVE-2015-3306 (descripción, CVSSv2 10.0 y vector, CWE-284, fecha de
  publicación 18/05/2015). Consultado 11/09/2026 vía la API pública:
  <https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2015-3306>
  (ficha: <https://nvd.nist.gov/vuln/detail/CVE-2015-3306>).
- GitHub Advisory Database — GHSA-4mfj-5wr8-x32q (CWE-284, severidad High, EPSS
  96.75 % / percentil 100). Consultado 11/09/2026:
  <https://github.com/advisories/GHSA-4mfj-5wr8-x32q>
- Rapid7 — módulo Metasploit "ProFTPD 1.3.5 Mod_Copy Command Execution"
  (mecánica de `/proc/self/cmdline` → webshell, ejecución como `nobody`).
  Consultado 11/09/2026:
  <https://www.rapid7.com/db/modules/exploit/unix/ftp/proftpd_modcopy_exec/>
- Exploit-DB — "ProFTPd 1.3.5 - 'mod_copy' Remote Command Execution" (EDB-36803):
  <https://www.exploit-db.com/exploits/36803>

## Reflexión (3–5 líneas)

Lo que nos llevamos es que el recon no termina en el puerto abierto: el valor está
en el salto de "hay un FTP" a "hay una RCE no autenticada con exploit público".
Ese salto lo dio **una sola línea de banner**, y por eso entendimos en la práctica
por qué el `-sV` (y el banner grabbing) valen tanto: sin la versión exacta, el
hallazgo del 21 hubiera sido apenas "FTP abierto". También nos quedó clarísima la
ironía defensiva: el mismo banner que nos sirvió para clasificar es información que
PhantomCorp nunca debió filtrar.
