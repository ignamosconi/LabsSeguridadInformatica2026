# Informe — Laboratorio 08 · Post-explotación y automatización

**Grupo:** 05 · **Integrantes:** Magni, Gastón (@nosungam) · Mosconi, Ignacio
(@ignamosconi) · Presuttari, Matías (@matiaspresuttari) · Terreno, Valentino
(@vterreno) · **Fecha:** 2026-10-09

## 0. Declaración de uso de IA

Usamos Claude Code (Opus 4.8) como asistente para: completar la función
`buscar_flag()` del esqueleto `recolector.py`, levantar el entorno Docker del
lab, ejecutar la post-explotación dentro del host víctima y ordenar la evidencia
y este informe. Todas las flags se obtuvieron corriendo el entorno real
(`./ctf lab 08` + `make shell-victima`), no se copiaron de ningún `solucion.md`.
Revisamos y entendemos cada comando, técnica y respuesta de análisis.

## 1. Flags capturadas

Salida de `./ctf status 08` (evidencia: `evidencia/ctf-status.txt`):

```
   ✓  R1     Reconocimiento del host comprometido
   ✓  R2     Loot de credenciales
   ✓  R3     Escalada de privilegios (SUID)
   ✓  R4     Pivoting al host interno
   ✓  R5     Automatizacion (fuerza bruta de legajos)
   ██████████████████████████████  5/5 (100%)
```

| Reto | Flag |
|---|---|
| R1 | `FLAG{post_situational_awareness}` |
| R2 | `FLAG{loot_credentials_found}` |
| R3 | `FLAG{privesc_suid_root}` |
| R4 | `FLAG{pivot_internal_host}` |
| R5 | `FLAG{automation_pays_off}` |

Caímos como `operador` (uid=1000, sin privilegios, sin `sudo`) en el host
`phantomcorp`. Ese es el punto de partida: un shell sin privilegios no es el
final, es el principio.

## 2. Informe de post-explotación

| Fase | Qué hiciste | Comando/técnica | Evidencia | Defensa |
|---|---|---|---|---|
| **Recon del host** | Nos preguntamos *quién/dónde/qué*: identidad (`operador`, sin grupos extra), sistema (`phantomcorp`, Debian), redes (dos interfaces: `eth0 172.23.0.0/16` y `eth1 172.22.0.0/16` → el host está en dos redes) y filesystem. En `/opt/phantom-deploy/DEPLOY_NOTES.txt` había una nota de deploy con un `deploy_token` que es el flag. | `id; whoami; hostname; uname -a; env; ip -o addr; cat /etc/hosts; ls -la /opt; cat /opt/phantom-deploy/DEPLOY_NOTES.txt` | `evidencia/r1-recon.txt` | No dejar notas/tokens de deploy en el filesystem del server. Deploys sin secretos embebidos; permisos mínimos y limpieza de artefactos de despliegue. |
| **Loot** | Las apps guardan sus secretos en config. Leímos `/var/www/.env` (world-readable, 644): `DB_PASS=Ph@ntom-DB-2024` y `APP_SECRET=<flag>`. El `.bash_history` del usuario mostró que ya había tocado `phantomcorp-db` (pista de pivoting). Un `grep -rai` confirmó los secretos. | `cat /var/www/.env; cat ~/.bash_history; grep -rai "pass\|secret\|token" /var/www` | `evidencia/r2-loot.txt` | Secretos fuera del disco de la app: gestor de secretos / variables de entorno efímeras inyectadas al runtime; `.env` con permisos `600` y dueño ≠ usuario de la app; no versionar secretos; rotación. Deshabilitar/limpiar historiales en cuentas de servicio. |
| **Privesc (SUID)** | `/root/flag.txt` (modo 600, dueño root) no era legible como `operador`. `find / -perm -4000` listó un binario no estándar: `/usr/local/bin/system-check`, que es una **copia SUID de bash**. GTFOBins indica ejecutarlo con `-p`: el bit SUID hace que corra con el euid del dueño (root) y `-p` **preserva** ese euid privilegiado. Con `system-check -p -c 'cat /root/flag.txt'` leímos el archivo (euid=0). | `sudo -l; find / -perm -4000 -type f 2>/dev/null; system-check -p -c "id; cat /root/flag.txt"` | `evidencia/r3-privesc.txt` | No dejar binarios SUID innecesarios, y nunca shells (`bash`/`sh`) con SUID. Auditar SUID periódicamente (`find / -perm -4000`), montar con `nosuid` donde se pueda, principio de mínimo privilegio. |
| **Pivoting** | El host interno `phantomcorp-db` vive solo en `internalnet` (red `internal`). Desde la **consola atacante** `curl http://phantomcorp-db/` falla (sin ruta). Desde la **víctima** sí responde, porque `phantomcorp` está conectado a las dos redes y hace de trampolín. La raíz `/` devolvió el flag de pivot. | Atacante: `curl --max-time 4 http://phantomcorp-db/` → unreachable. Víctima: `curl -s http://phantomcorp-db/` → JSON con `pivot`. | `evidencia/r4-pivot.txt` | Segmentación efectiva + host dual-homed es el riesgo: minimizar hosts con patas en dos redes, firewall este-oeste, no exponer servicios internos sin autenticación, listas de control de acceso entre segmentos. |

## 3. Automatización

Script completado: [`src/recolector.py`](src/recolector.py). Completamos
`buscar_flag()` (recorrido + corte al hallar) y agregamos un helper
`extraer_flag()` que detecta el legajo distinto **sin hardcodear** el nombre de
la clave (los normales traen `id/nombre/area`; el del flag trae una clave extra).
Reusa `consultar_legajo()` del esqueleto, que ya maneja 404 (`HTTPError → None`) y
errores de red.

Corrida real **dentro del host víctima** contra `phantomcorp-db`
(`evidencia/r5-recolector-en-victima.txt`):

```
[*] Enumerando legajos 1..250 en http://phantomcorp-db
[+] Flag en el legajo id=187: FLAG{automation_pays_off}
```

El flag estaba en el legajo **187** de 250: a mano era inviable, el script lo
resuelve en segundos y **corta apenas lo encuentra** (no sigue enumerando de
gusto). Manejo de errores verificado apuntando a un puerto muerto
(`evidencia/r5-recolector-manejo-errores.txt`): registra el error por `stderr`,
no aborta y sigue con el siguiente id.

## 4. Preguntas de análisis

**P1 — SUID y el flag `-p`.**
El bit **SUID** hace que un ejecutable corra con los permisos de su **dueño**, no
de quien lo lanza. Si el dueño es root, cualquier usuario que lo ejecute obtiene
`euid=0` durante esa ejecución. Es peligroso porque convierte un binario en una
puerta a root: si además es un intérprete/shell o una herramienta que permite
ejecutar comandos o leer archivos arbitrarios (ver GTFOBins), la escalada es
directa. El flag **`-p`** de bash es clave: por defecto bash, al arrancar,
**baja** sus privilegios efectivos para igualarlos al uid real (medida de
seguridad); con `-p` **no** los baja y **preserva el euid=0** heredado del SUID.
Por eso `system-check -p` nos deja operar como root; sin `-p` volveríamos a ser
`operador`. Lo comprobamos: `id` dentro del binario mostró `euid=0(root)`.

**P2 — el pivoting (por qué el atacante no llegaba y vos sí).**
Las redes están **segmentadas**. `phantomcorp-db` está conectado **solo** a
`internalnet`, que está declarada `internal: true` (sin ruta hacia afuera). La
consola atacante vive en `labnet`: no comparte segmento con la DB, entonces no
tiene ruta hasta ella (`curl` da unreachable/timeout). La víctima `phantomcorp`,
en cambio, es **dual-homed**: tiene una pata en `labnet` (`eth1`) y otra en
`internalnet` (`eth0`), así que alcanza la DB. Una vez con shell en la víctima la
usamos de **trampolín**: el tráfico sale desde un host que sí está en la red
interna. Eso es movimiento lateral / pivoting.

**P3 — cómo evitar secretos en `.env`/`.bash_history`.**
No almacenar secretos en disco junto a la app. Lo correcto:
- **Gestor de secretos** (Vault, AWS/GCP Secrets Manager, Docker/K8s secrets) que
  entrega las credenciales en runtime y rota periódicamente.
- **Variables de entorno efímeras** inyectadas por el orquestador, no un `.env`
  world-readable (644) en el filesystem; si hay `.env`, permisos `600` y dueño
  distinto del usuario de la app.
- **No versionar** secretos (`.gitignore`), escaneo de secretos en CI, y rotación
  de lo filtrado (la `DB_PASS` ya está quemada).
- En cuentas de servicio, deshabilitar o no persistir el historial
  (`HISTFILE=/dev/null`, `unset HISTFILE`), y no tipear secretos en la línea de
  comandos (quedan en el history y en la lista de procesos).

**P4 — qué decidiste vos que el script no decide solo.**
El script solo **ejecuta la repetición** que nosotros definimos. Decidimos los
humanos: *qué* endpoint atacar y *cómo* se ve un hallazgo (la heurística de "una
clave distinta a `id/nombre/area`" = flag); el **rango** 1..250 y la estrategia de
enumeración; **cuándo cortar** (al primer hallazgo); qué es un error recuperable
(404/timeout → seguir) y qué no; y el encadenamiento con las fases previas (que el
host interno sale del loot del `.env` y del pivoting). El script no "entiende" el
objetivo: no reformula la estrategia si el patrón cambia, no decide pivotear ni
elige el próximo blanco. **Esa capa de decisión y orquestación es exactamente lo
que en el Lab 09 va a tomar un agente**: nosotros fijamos objetivo y límites, el
agente encadena las tools.

**P5 — defensa para SUID y para pivoting.**
- **SUID:** eliminar el binario SUID innecesario (`chmod -s` / borrar
  `system-check`) y **nunca** dar SUID a shells o intérpretes; auditar
  regularmente con `find / -perm -4000 -type f`, montar particiones de datos con
  `nosuid`, y aplicar mínimo privilegio (lo que necesite root que lo haga un
  servicio acotado, no un binario de uso general).
- **Pivoting:** reducir los hosts **dual-homed** (que un server público no tenga
  pata directa en la red interna), firewall **este-oeste** entre segmentos con
  reglas explícitas, autenticación en los servicios internos (la DB respondía sin
  credenciales a cualquiera de la LAN), y monitoreo de tráfico lateral anómalo
  (un web server que de golpe habla con la DB interna por HTTP crudo).

## 5. Mini-research

Ver [`research.md`](research.md) — tema **D: de scripts a agentes**.
