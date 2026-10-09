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

