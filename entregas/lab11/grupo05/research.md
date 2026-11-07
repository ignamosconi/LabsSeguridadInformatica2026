# Mini-research — Laboratorio 11

**Tema elegido:** **A.** Volatility 3: cómo se captura un volcado de RAM (LiME,
avml) y qué plugins se usan para procesos, red y credenciales.

## Desarrollo

### 1. Por qué se captura la memoria primero

La memoria RAM es el soporte más volátil de un sistema: al apagar o reiniciar la
máquina se pierde por completo. Todo lo que vive solo en RAM —procesos en
ejecución, conexiones de red abiertas, variables de entorno, claves y sesiones—
desaparece con ella. Por eso el orden de volatilidad que describe la RFC 3227
ubica a la memoria antes que el disco y los logs: primero se captura lo que antes
se destruye. En el caso del Lab 11 esto se ve con claridad: el atacante ejecutó
`history -c`, pero la captura de memoria conservó el historial de la sesión viva
y la conexión `ESTABLISHED` del proceso `nc` hacia el C2. Esos dos artefactos ya
no existían en el disco.

### 2. Cómo se adquiere un volcado en Linux

A diferencia de Windows, Linux no trae una herramienta estándar para volcar toda
la RAM. Las dos opciones más usadas en DFIR son:

- **LiME (Linux Memory Extractor).** Es un módulo de kernel que se carga con
  `insmod` y escribe la memoria a un archivo o por la red. Su ventaja es que
  captura desde dentro del kernel, con acceso a todos los rangos de memoria; su
  costo es que hay que compilarlo para la versión exacta del kernel del equipo
  analizado y que su carga modifica el estado del sistema (por eso se documenta
  en la cadena de custodia). Ejemplo de uso:

  ```bash
  insmod lime.ko "path=/mnt/evidencia/ram.lime format=lime"
  ```

- **AVML (Acquire Volatile Memory for Linux).** Herramienta de Microsoft escrita
  en Rust, de código abierto. No requiere compilar un módulo: se ejecuta como
  binario y vuelca la memoria a un archivo comprimido. Es más simple de desplegar
  en respuesta a incidentes, aunque en algunos kernels necesita privilegios y
  acceso a `/dev/crash` o a `/dev/mem`.

  ```bash
  avml /mnt/evidencia/ram.avml
  ```

Otras alternativas históricas son `fmem` y la lectura de `/proc/kcore`, pero
LiME y AVML son las que se recomiendan hoy en la práctica. En todos los casos, el
volcado se escribe en un medio externo, se hashea al terminarlo y se documenta
quién lo hizo, cuándo y con qué versión de la herramienta: el volcado es
evidencia y también necesita cadena de custodia.

### 3. Qué se analiza con Volatility 3

**Volatility 3** es el framework de análisis de memoria de referencia. Trabaja
sobre el volcado (no sobre el equipo vivo), detecta el sistema operativo y ofrece
plugins agrupados por familia (`linux.*`, `windows.*`, `mac.*`). Los que usamos
en este laboratorio —y sus equivalentes reales sobre un dump— son:

| Necesidad forense | Plugin de Volatility 3 | Qué devuelve |
|---|---|---|
| Procesos en ejecución | `linux.pslist` / `linux.pstree` | Lista y árbol de procesos con PID, PPID y usuario; permite detectar procesos huérfanos o con padre inesperado (en el lab, `system-check` como hijo de `bash` y `nc` como hijo del SUID). |
| Conexiones de red | `linux.sockstat` | Sockets con IP/puerto local y remoto, estado y PID; sirve para encontrar un C2 `ESTABLISHED` que el firewall no vio. |
| Archivos abiertos | `linux.lsof` | Descriptores abiertos por proceso; en el caso, el `nc` con su socket y el `bash` con el `.tar.gz` de exfiltración. |
| Historial de comandos | `linux.bash` | Comandos recuperados de la memoria de los procesos `bash`, incluso si el `.bash_history` del disco fue borrado. |
| Código malicioso en memoria | `linux.malfind` | Regiones de memoria ejecutables y anónimas, típicas de payloads inyectados. |
| Credenciales | `linux.hashdump` (según versión) | Hashes de contraseñas extraídos de la memoria del kernel/sistema; permiten evaluar qué credenciales quedaron expuestas. |

El flujo típico es: `vol -f ram.lime linux.pslist`, después `linux.pstree` para
ver la jerarquía, `linux.sockstat` para la red y `linux.bash` para la actividad
del atacante. La clave no es un plugin aislado sino la **correlación**: el mismo
PID que aparece en `pslist` debe aparecer en `sockstat` y en `lsof`. En el Lab 11
el PID 1490 (`nc 45.13.37.7 4444`) aparece en los tres, y su padre 1477
(`system-check`) es el binario SUID: la memoria cuenta la escalada y el C2 en una
sola historia.

### 4. Límites y buenas prácticas

Un volcado de RAM es enorme (gigas) y contiene datos sensibles: credenciales,
claves, contenido de documentos y datos personales. Debe almacenarse cifrado,
con acceso restringido y bajo la misma cadena de custodia que el disco. Además,
la captura debe hacerse con el menor impacto posible: cada comando que se ejecuta
en el equipo vivo altera la memoria. Por eso se documenta la herramienta, la
versión, el orden de captura y el hash del resultado. En producción, un análisis
de memoria sin volcado previo y sin hashes no es defendible.

## Fuentes (mín. 3)

1. **RFC 3227 — Guidelines for Evidence Collection and Archiving** (IETF, 2004).
   Define el orden de volatilidad y las buenas prácticas de recolección.
   <https://www.rfc-editor.org/rfc/rfc3227>
2. **Volatility 3 — documentación oficial.** Plugins, uso de la CLI y soporte de
   sistemas operativos. <https://volatility3.readthedocs.io/>
3. **LiME (Linux Memory Extractor)** — repositorio oficial.
   <https://github.com/504ensicsLabs/LiME>
4. **Microsoft AVML (Acquire Volatile Memory for Linux)** — repositorio oficial.
   <https://github.com/microsoft/avml>
5. **NIST SP 800-86 — Guide to Integrating Forensic Techniques into Incident
   Response.** Marco general de adquisición y preservación de evidencia.
   <https://csrc.nist.gov/pubs/sp/800/86/final>

## Reflexión

Este lab cierra el círculo del curso: en las clases anteriores atacamos y en la
10 aprendimos a evadir; acá nos tocó reconstruir el ataque desde los rastros. La
parte técnica más valiosa no fue "encontrar la flag", sino entender que la
memoria y el disco se complementan. El `history -c` del atacante parecía un
borrado exitoso en el disco, pero la sesión seguía viva en RAM y Volatility (o,
en este caso, los artefactos ya extraídos) la recuperó. Lo mismo con el C2: un
`nc` que no deja archivo en disco, pero sí un socket y un proceso.

También me quedó claro que la cadena de custodia no es burocracia. Un solo
archivo alterado (`auth.log`) alcanza para que esa pieza deje de ser confiable,
aunque el resto esté intacto. Si no se documenta el hash y la manipulación, no
hay forma de defender el análisis. La forense es, en el fondo, contar una
historia con evidencia verificable: si no se puede verificar, no es evidencia.
