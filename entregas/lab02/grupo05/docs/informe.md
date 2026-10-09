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
