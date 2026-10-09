# Informe · Laboratorio 06 · Enumeración de servicios

**Grupo:** 05  
**Integrantes:** *Gastón Magni, Ignacio Mosconi, Matías Presuttari, Valentino Terreno*  
**Fecha:** 11/09/2026


## 0. Declaración de uso de IA

Se utilizó Claude (Anthropic) como asistente durante la resolución del laboratorio.
Usos concretos:
- Estructuración del informe y redacción de las secciones de análisis.
- Revisión de los comandos de enumeración y explicación de qué campo/header
  contiene cada hallazgo.
- Redacción del mini-research (sección en research.md).

El grupo ejecutó todos los comandos contra el entorno Docker de la cátedra,
verificó las salidas obtenidas y validó que el análisis sea consistente con
lo observado. Las flags se obtuvieron ejecutando las herramientas de enumeración,
no leyendo solucion.md ni el código del target.


## 1. Flags capturadas
```bash
Ignacio@DESKTOP-I81FL9D MINGW64 /.../LabsSeguridadInformatica2026 (lab06-grupo05)
$ bash ctf status 06

  ╭────────────────────────────────────────────────────────────╮  
  │                     PROGRESO · LAB 06                      │  
  ╰────────────────────────────────────────────────────────────╯  

   ✓  R1     Enumeracion de directorios  
   ✓  R2     Repositorio Git expuesto  
   ✓  R3     Metodos HTTP peligrosos habilitados  
   ✓  R4     Enumeracion de usuarios via API  
   ✓  R5     Fingerprinting de tecnologia  

  ██████████████████████████████  5/5 (100%)  

[ OK ] ¡Lab 06 COMPLETO! Ponete las pilas con la próxima unidad.  
```



## 2. Inventario de enumeración

| Hallazgo | Ruta / Método | Técnica | Evidencia | Riesgo | ¿Qué habilita para Lab 07? |
|---|---|---|---|---|---|
| Directorio `/backup` accesible públicamente | `GET /backup/` | Enumeración de directorios con `dirb` | Ver 2.1 | **Alto**: expone archivos de configuración y backups con credenciales potenciales en texto plano | Acceso a volcados de base de datos y archivos `.old`; insumo directo para ataques de credenciales o path traversal en Lab 07 |
| Repositorio `.git` expuesto | `GET /.git/config` | Petición HTTP directa (`curl`) | Ver 2.2 | **Crítico**: permite reconstruir el código fuente completo del servidor con `git-dumper`, incluyendo el historial donde pueden existir credenciales eliminadas | Lectura del código fuente revela rutas internas, lógica de autenticación y posibles secretos; facilita explotación dirigida en Lab 07 |
| Métodos HTTP peligrosos habilitados (`PUT`, `DELETE`) | `OPTIONS /` | Enumeración de métodos HTTP (`curl -X OPTIONS`) | Ver 2.3 | **Alto**: `PUT` habilitado permite subir archivos arbitrarios al servidor, incluyendo webshells | Subida de webshell PHP/Python via `PUT` → ejecución remota de comandos (RCE); vector directo de explotación en Lab 07 |
| Endpoint de API interna expuesto que lista usuarios | `GET /api/users` | Enumeración de endpoints API (`curl`) | Ver 2.4 | **Medio**: filtra nombres de usuario válidos y sus roles sin requerir autenticación | Usuarios enumerados (`admin`, `jperez`, `mgomez`) son insumo para ataques de fuerza bruta dirigida, credential stuffing y SQLi en Lab 07 |
| CMS identificado con versión exacta y archivo de versión accesible | `GET /phantomcms/VERSION` | Fingerprinting web (`whatweb` + `curl`) | Ver 2.5 | **Medio**: PhantomCMS 3.7 con build 2024-11 puede tener CVEs conocidos; el archivo de versión no debería ser público | Búsqueda de exploits públicos para PhantomCMS 3.7; identifica el stack exacto para seleccionar payloads en Lab 07 |

### 2.1 - Evidencia: enumeración de directorios
```text
root@attacker:/loot# dirb http://phantomcorp/

-----------------
DIRB v2.22    
By The Dark Raver
-----------------

START_TIME: Fri Sep 11 23:28:02 2026
URL_BASE: http://phantomcorp/
WORDLIST_FILES: /usr/share/dirb/wordlists/common.txt

-----------------

GENERATED WORDS: 4612                                                          

---- Scanning URL: http://phantomcorp/ ----
+ http://phantomcorp/admin (CODE:403|SIZE:65)                                                                                                        
+ http://phantomcorp/backup (CODE:200|SIZE:249)                                                                                                      
                                                                                                                                                     
-----------------
END_TIME: Fri Sep 11 23:28:15 2026
DOWNLOADED: 4612 - FOUND: 2
```


**Acceso al directorio descubierto:**  
```text
root@attacker:/loot# curl -s http://phantomcorp/backup/
<!doctype html><html><body><h1>Index of /backup</h1>
<pre>
respaldo-db-2024.sql.gz
config.old
notas-infra.txt   ->  FLAG{dir_enumeration_backup}
</pre>
<p>Este directorio no deberia estar accesible. Enumeracion de directorios 101.</p>
```


### 2.2 - Evidencia: repositorio `.git` expuesto
```console
root@attacker:/loot# curl -s http://phantomcorp/.git/config
[core]
        repositoryformatversion = 0
        bare = false
[remote "origin"]
        url = https://git.internal.phantomcorp/intranet.git
# Un .git expuesto filtra codigo, historia y a veces secretos.
# FLAG{git_repo_exposed}
```



### 2.3 - Evidencia: métodos HTTP peligrosos
```console
root@attacker:/loot# curl -X OPTIONS -i http://phantomcorp/
HTTP/1.0 200 OK
Server: PhantomServer/3.7 
Date: Fri, 11 Sep 2026 23:30:01 GMT
Allow: GET, POST, PUT, DELETE, OPTIONS
X-Dangerous-Methods: FLAG{http_methods_put_enabled}
```


### 2.4 - Evidencia: API de usuarios expuesta
```text
root@attacker:/loot# curl -s http://phantomcorp/api/users | python3 -m json.tool
```
```json
{
    "users": [
        {
            "id": 1,
            "user": "admin",
            "role": "superuser"
        },
        {
            "id": 2,
            "user": "jperez",
            "role": "editor"
        },
        {
            "id": 3,
            "user": "mgomez",
            "role": "viewer"
        }
    ],
    "note": "endpoint interno de RRHH - no exponer",
    "flag": "FLAG{user_enumeration_api}"
}
```



### 2.5 - Evidencia: fingerprinting de tecnología
```console
root@attacker:/loot# whatweb http://phantomcorp  
http://phantomcorp [200 OK] Country[RESERVED][ZZ], HTML5, HTTPServer[PhantomServer/3.7], IP[172.19.0.2], MetaGenerator[PhantomCMS 3.7], Title[Intranet PhantomCorp], X-Powered-By[PhantomCMS/3.7]
```

```console
root@attacker:/loot# curl -s http://phantomcorp/phantomcms/VERSION  
PhantomCMS 3.7 (build 2024-11)  
Archivo default del CMS. Si llegaste aca por fingerprinting, bien.  
FLAG{tech_fingerprint_phantomcms}  
```



## 3. Preguntas de análisis

### P1 - Enumeración vs. reconocimiento

El reconocimiento (Lab 05) responde a la pregunta *¿qué existe?*: se identificaron
los hosts activos, los puertos abiertos y los servicios que escuchan en ellos
mediante `nmap -sV`. El resultado fue un mapa: "puerto 80 abierto, servidor web
PhantomCMS 3.7". En ese momento no sabíamos nada sobre el *interior* del servicio.

La enumeración (este lab) responde a *¿qué esconde cada cosa?*: tomamos ese servicio
ya identificado y lo interrogamos en profundidad. Con `dirb` probamos miles de rutas
para encontrar `/backup`; con `curl /.git/config` confirmamos un repositorio expuesto;
con `curl -X OPTIONS` preguntamos qué métodos acepta. El resultado es un inventario
detallado de superficie de ataque dentro de ese único servicio.

Dos diferencias concretas: 
- a) En el Lab 05 usamos nmap sobre rangos de IP y puertos (alcance amplio, profundidad mínima). En este lab usamos dirb sobre un único host (alcance mínimo, profundidad máxima).
- b) El Lab 05 no tocó ninguna ruta HTTP interna; el Lab 06 las enumeró todas.

### P2 - El `.git` expuesto

Un archivo suelto filtrado expone ese archivo. Un `.git` expuesto es cualitativamente
distinto: expone el repositorio completo, con toda su historia.

Con `git-dumper` (o `GitTools`) un atacante baja el objeto pack del repositorio,
reconstruye el working tree y obtiene:
- a) El código fuente actual y toda su lógica interna, incluyendo rutas privadas, validaciones y lógica de autenticación.  
- b) El historial de commits, donde pueden existir credenciales, tokens de API o claves
privadas que fueron commiteadas y luego eliminadas. Eliminar un secreto de la rama
principal no lo borra del historial: `git log --all -p` los recupera.

En este lab, el `/.git/config` expuesto reveló la URL interna del repositorio
(`git.internal.phantomcorp/intranet.git`) y la flag. Un atacante real podría usar
esa URL para intentar clonar el repo directamente si el servidor git interno está
accesible, o usar `git-dumper` para reconstruirlo desde los objetos HTTP.

### P3 - El método `PUT` habilitado

El método HTTP `PUT` permite al cliente enviar un archivo al servidor y que este lo
almacene en la ruta indicada. Con `PUT` habilitado, el ataque concreto es:

1. Subir un webshell: `curl -X PUT http://phantomcorp/shell.py --data-binary @shell.py`
2. Acceder al webshell por GET: `curl http://phantomcorp/shell.py?cmd=id`
3. El servidor ejecuta el comando y devuelve la salida → RCE (Remote Code Execution).

El header `Allow: GET, POST, PUT, DELETE, OPTIONS` encontrado en la respuesta
OPTIONS confirma que el servidor acepta `PUT`. Combinado con la ausencia de
autenticación, este hallazgo es un vector directo de ejecución de código remoto
sin necesidad de explotar vulnerabilidades en el código de la aplicación.

