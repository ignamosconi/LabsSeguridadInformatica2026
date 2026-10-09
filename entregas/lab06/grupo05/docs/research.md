# Mini-research • Laboratorio 06

**Tema elegido:** *(uno)*

Elegimos el tema A:

- [x] **A.** Cómo un `.git` expuesto permite reconstruir el código (git-dumper) y
  casos reales de credenciales filtradas por esta vía.
- [ ] **B.** Wordlists de enumeración: qué son SecLists, cómo se eligen, por qué
  una wordlist mala hace fallar la enumeración.
- [ ] **C.** El método HTTP `PUT` y el WebDAV: cómo se pasa de "método habilitado"
  a subir un webshell.
- [ ] **D.** Fingerprinting pasivo vs. activo: cómo `whatweb` deduce el stack.



## Desarrollo

### ¿Qué es un repositorio `.git` y por qué es sensible?

Cuando un proyecto usa Git, el directorio `.git/` almacena toda la información del
repositorio: el historial completo de commits, los objetos (blobs, trees, commits),
las referencias a ramas y tags, y el archivo de configuración que puede incluir URLs
internas, nombres de usuarios y a veces credenciales de repositorios remotos.

En un servidor web típico, el código se despliega copiando los archivos al webroot
(por ejemplo, `/var/www/html/`). Si el deploy se hace con `git clone` o `git pull`
directamente en ese directorio, la carpeta `.git/` queda expuesta bajo la raíz del
sitio. Si el servidor web no está configurado para bloquear el acceso a directorios
que empiezan con punto, cualquier visitante puede pedir
`http://objetivo.com/.git/config` y obtener la respuesta.

### Cómo se reconstruye el código con git-dumper

El ataque se realiza en dos etapas:

**Etapa 1: Confirmar la exposición:**
```bash
curl -s http://objetivo.com/.git/config
```
Si responde 200 con contenido de configuración git (empieza con `[core]`), el
repositorio está expuesto.

**Etapa 2: Reconstruir el repositorio con GitTools:**
La herramienta `git-dumper` (parte de la suite GitTools de Internetwache) descarga
recursivamente los objetos del repositorio haciendo peticiones HTTP a rutas conocidas
de la estructura interna de git: `.git/HEAD`, `.git/index`, `.git/objects/pack/`,
entre otras. Con esos objetos descargados localmente, reconstruye el working tree
completo.

```bash
git-dumper http://objetivo.com/.git/ repositorio-local/
cd repositorio-local/
git log --oneline --all    # ver todo el historial
git log --all -p           # ver los diffs, incluyendo credenciales eliminadas
```

El resultado es una copia funcional del repositorio con todo su historial. Si en
algún commit pasado existió una contraseña o un token de API que luego fue eliminado
con otro commit, `git log --all -p` lo muestra igualmente: eliminar un secreto de
la rama principal no lo borra del historial de objetos git.

### Por qué es más grave que "un archivo de más"

Un archivo de configuración expuesto filtra esa configuración. Un `.git` expuesto
filtra:

- El **código fuente actual** de toda la aplicación: lógica de negocio, rutas
  internas no documentadas, validaciones de autenticación y autorización.
- El **historial completo**: credenciales de base de datos, tokens de API y claves
  privadas que pasaron por el repositorio en algún momento, aunque hayan sido
  "eliminadas" después.
- Las **URLs de repositorios remotos** (en `.git/config`), que pueden ser servidores
  git internos accesibles desde la red.
- Los **mensajes de commit**, que a veces contienen información operacional
  ("fix: hardcoded password in prod config").

### Casos documentados y herramientas utilizadas en la industria

**GitTools - la herramienta estándar del sector:** El repositorio GitTools de
Internetwache es la suite de referencia para explotar `.git` expuestos. Contiene
`git-dumper` (descarga el repositorio vía HTTP), `git-extractor` (reconstruye el
working tree desde los objetos descargados) y `git-finder` (escanea listas de URLs
buscando instancias vulnerables). El hecho de que esta herramienta exista, sea de
código abierto y esté activamente mantenida ilustra cuán extendido es el problema
en producción. Código y documentación en:
https://github.com/internetwache/GitTools

**Escenario tipo documentado por PortSwigger:** PortSwigger Web Security Academy
describe el vector de directorio `.git` expuesto como una forma clásica de
information disclosure involuntaria. El servidor no tiene la intención de revelar
su estructura interna, pero la mala configuración lo hace de todos modos. La
academia documenta el caso, sus variantes y los pasos de verificación en:
https://portswigger.net/web-security/information-disclosure/exploiting

**HackTricks: referencia técnica de la comunidad de seguridad ofensiva:**
HackTricks documenta el procedimiento completo de explotación de `.git` expuestos,
incluyendo qué archivos pedir en qué orden, cómo reconstruir el árbol de objetos
manualmente cuando `git-dumper` no puede descargarlo todo, y casos donde la
exposición parcial (solo algunos objetos accesibles) igual permite recuperar
fragmentos de código sensibles:
https://book.hacktricks.xyz/network-services-pentesting/pentesting-web/git

**OWASP Web Security Testing Guide (WSTG): sección de archivos sensibles:**
La guía oficial de OWASP clasifica los directorios de control de versiones
expuestos (`.git`, `.svn`, `.hg`) dentro de la categoría de archivos con extensiones
o nombres sensibles que no deberían ser accesibles desde el exterior. La sección
incluye procedimiento de detección y criterios de impacto:
https://github.com/OWASP/wstg/blob/master/document/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management/03-File_Extensions_Handling_for_Sensitive_Information.md


## Fuentes

1. **GitTools - Internetwache** (GitHub). Suite de herramientas para explotar
   repositorios `.git` expuestos; incluye `git-dumper`, `git-extractor` y
   `git-finder`. Código abierto y activamente mantenido.
   https://github.com/internetwache/GitTools

2. **PortSwigger Web Security Academy** - *"Exploiting information disclosure
   vulnerabilities"*. Referencia técnica con ejemplos prácticos del vector `.git`
   expuesto como caso de information disclosure involuntaria.
   https://portswigger.net/web-security/information-disclosure/exploiting

3. **OWASP Web Security Testing Guide v4.2** - *Test File Extensions Handling for
   Sensitive Information*. Guía oficial con procedimiento de detección de directorios
   de control de versiones expuestos y criterios de impacto. Versión en GitHub
   (acceso directo al texto):
   https://github.com/OWASP/wstg/blob/master/document/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management/03-File_Extensions_Handling_for_Sensitive_Information.md

4. **HackTricks** - *"Pentesting Web - Git"*. Documentación técnica de la comunidad
   de seguridad ofensiva: procedimiento de explotación completo, incluyendo
   reconstrucción manual de objetos y casos de exposición parcial.
   https://book.hacktricks.xyz/network-services-pentesting/pentesting-web/git


## Reflexión

Antes de este lab, la idea de "desplegar con git" parecía una práctica razonable.
El laboratorio muestra que la diferencia entre un deploy seguro y un `.git` expuesto
es simplemente no haber configurado una regla en el servidor web, o haber usado
`git pull` en el webroot por comodidad. El impacto no es proporcional al error: un
descuido de configuración de dos líneas puede exponer años de historial de código,
incluyendo secretos que ya no existen en la rama principal pero sí en el historial.
La herramienta `git-dumper` demuestra que el ataque es completamente automatizable
y no requiere ninguna habilidad especial más allá de saber que el vector existe.
Eso refuerza por qué la enumeración es tan importante: el inventario detallado de
lo que expone un servidor web no es obvio leyendo la página de inicio.