# Informe - Lab Extra 2: El repo que delata

**Grupo:** 05.  
**Integrantes:** Ignacio Mosconi (ignamosconi) · Valentino Terreno (vterreno) · Gastón Magni (gastonmagni) · Matías Presuttari (matiaspresuttari).  
**Fecha:** 2026-10-30.  

**Declaración de uso de IA:** Para la resolución de este lab utilizamos Claude
(Anthropic) para guiarnos en los pasos de investigación y para redactar y
estructurar el informe. Los comandos fueron ejecutados y verificados por nosotros;
las flags fueron encontradas corriendo los comandos reales sobre el repo generado.
Las respuestas a las preguntas de análisis fueron desarrolladas por el grupo con
asistencia de IA para claridad de redacción.

## 1. Línea de tiempo de la filtración

| Fecha | Autor | Commit (hash corto) | Qué pasó | ¿Expone algo? |
|---|---|---|---|---|
| 2026-08-05 16:30 | dev-jperez | 0abdf95 | Creación de rama `feature/pasarela-pagos`; se commitea `.env.pasarela` con `PAGOS_SECRET` | **Sí**: clave de pasarela de pagos |
| 2026-08-10 09:12 | dev-jperez | de33a75 | Commit inicial del proyecto (`app.py`, `README.md`). Token por variable de entorno, correctamente | No |
| 2026-08-10 18:47 | dev-jperez | 9333f2b | Hotfix: se hardcodea `PHANTOM_API_TOKEN` en `config.py` para resolver deploy urgente | **Sí**: API token de PhantomCorp |
| 2026-08-11 10:05 | dev-jperez | eafb81c | "Limpieza": se sobreescribe `config.py` sin el token. El commit anterior conserva el secreto intacto | No (el daño ya está hecho) |
| 2026-08-12 14:22 | dev-jperez | bc9d0db | Commit con `notas_investigacion.txt` que contiene `staging_key`. Inmediatamente reseteado con `git reset --hard HEAD~1`. El objeto queda colgado en el object store | **Sí**: clave del cluster de staging |
| 2026-08-20 11:00 | dev-jperez | fa714bd | Commit de documentación: "Historia limpia. Sin secretos. ✅" | No (falsa sensación de seguridad) |

**Tiempo de exposición del API token (R1):** desde 2026-08-10 18:47 hasta hoy: el commit nunca fue eliminado de la historia. El commit de "limpieza" del
2026-08-11 no borra nada del historial.



## 2. Hallazgos

### R1 - Secreto en commit viejo

**Comandos exactos:**
```bash
git log -p -- config.py
```

**Salida relevante (diff del commit hotfix):**
```diff
commit 9333f2b.
Author: dev-jperez <jperez@phantomcorp.example>
Date:   Sun Aug 10 18:47:00 2026 -0300

    hotfix: deploy roto en produccion (config temporal)

diff --git a/config.py b/config.py
new file mode 100644
--- /dev/null
+++ b/config.py
@@ -0,0 +1,4 @@
+# Config de emergencia — arreglar el deploy roto YA (después lo pasamos a env)
+PHANTOM_API_TOKEN = "FLAG{git_log_no_olvida}"
+REGION = "us-east-1"
+DEBUG = True
```

**Qué se expuso:** la API token de producción de PhantomCorp. Habilita
autenticarse contra `https://api.phantomcorp.example/v2` con permisos de deploy.

---

### R2 - Commit "perdido"

**Comandos exactos:**
```bash
git reflog
git show bc9d0db
```

**Cómo llegamos del reflog al contenido:**
El reflog lista todos los movimientos de HEAD. Al ver la entrada
`reset: moving to HEAD~1`, el hash de la línea inmediatamente anterior
es el commit que fue descartado. `git show <hash>` muestra su contenido
completo aunque ninguna rama lo apunte. El objeto sigue en el object store
de git hasta que corra `git gc`.

**Qué se expuso:** la clave del cluster de staging
(`staging_key: FLAG{git_reflog_rescata}`). Habilita acceso al cluster de
staging de la infraestructura de PhantomCorp.

---

### R3 - Rama abandonada

**Comandos exactos:**
```bash
git log --oneline --all
git show feature/pasarela-pagos:.env.pasarela
```

**Qué se expuso:** el secreto de la pasarela de pagos
(`PAGOS_SECRET=FLAG{git_rama_abandonada}`) y el endpoint interno
`https://pagos.phantomcorp.example`. Habilita operar contra el sistema
de pagos de PhantomCorp.


## 3. Evaluación de exposición

Si el repo hubiera estado **público en GitHub** desde el commit inicial,
el primero encontrado por un bot habría sido **R1** (el API token en
`config.py`): está en la historia lineal de `main` y herramientas como
TruffleHog o GitGuardian la escanean con `git log -p` en tiempo real vía
webhook. Tiempo estimado hasta detección: **menos de 5 minutos** desde
el push (estos servicios reciben eventos de push inmediatamente).

R3 (la rama) sería el segundo: las ramas también se indexan. R2 (el commit
dangling) es el más difícil para un bot porque no está referenciado por
ninguna rama, aunque `git fsck` lo encuentra en cualquier clon.


## 4. Plan de remediación (P4)

En orden de prioridad:

1. **Rotar todos los secretos YA**: `PHANTOM_API_TOKEN`, `staging_key`,
   `PAGOS_SECRET`. Esto es lo primero porque es lo único que corta el daño
   real. Mientras las claves sigan vigentes, todo lo demás es cosmético.
2. **Revocar accesos activos**: revisar logs de los sistemas que usan esas
   claves para detectar uso no autorizado durante el período de exposición.
3. **Notificar a quienes forkearon o clonaron**: esas copias tienen la
   historia completa. La reescritura del repo original no las afecta.
4. **Reescribir la historia** con `git filter-repo` para eliminar los secretos
   de los commits y hacer force-push. Evita futuras exposiciones para quien
   clone después, pero no remedia las copias existentes.
5. **Eliminar la rama** `feature/pasarela-pagos`.
6. **Implementar prevención** para que no vuelva a ocurrir (ver P5).

La reescritura de historia es la parte **menos urgente**: si alguien ya clonó,
las claves ya están en su poder. Y si las claves ya fueron rotadas, lo que
queda en la historia vieja es inútil de todas formas.



## 5. Preguntas P1 a P5

**P1) Línea de tiempo del token de la API:**

El token fue introducido en el commit `9333f2b` (2026-08-10 18:47) por
dev-jperez, en `config.py`, con el mensaje "hotfix: deploy roto en produccion
(config temporal)". El commit de "limpieza" es `eafb81c` (2026-08-11 10:05),
que sobreescribe `config.py` sin el token. Sin embargo, el commit `9333f2b`
permanece en la historia para siempre: el nuevo commit no borra el anterior,
solo agrega uno encima. El tiempo de exposición en la historia es indefinido
(desde 2026-08-10). No alcanza con el commit de limpieza: cualquiera que corra
`git log -p` puede ver la clave en el diff del commit anterior.

**P2) Por qué el `reset --hard` no borró nada:**

Git almacena su contenido como un grafo de objetos inmutables (blobs, trees,
commits) en `.git/objects/`. Crear un commit crea un objeto; hacer
`git reset --hard HEAD~1` solo mueve el puntero de la rama (una referencia)
al commit anterior, no elimina el objeto del commit descartado. El objeto
queda "colgado" (dangling): sin ninguna rama que lo apunte, pero físicamente
presente en el object store.

Dos comandos que lo demuestran:
- `git reflog`: lista todos los movimientos de HEAD, incluyendo el commit
  que fue reseteado.
- `git fsck --lost-found`: encuentra objetos sin referencia y los lista
  como "dangling commit".

**P3) Riesgo de la rama abandonada:**

- **Repo público:** cualquier persona que clone el repo tiene la rama completa
  con `.env.pasarela`. Los bots de escaneo también la ven con `--all`. El
  riesgo es total e inmediato.
- **Repo privado con 30 colaboradores:** los 30 tienen acceso a la rama. Si
  alguno tiene su clon en una máquina comprometida, el secreto está expuesto.
  Además, GitHub preserva commits por hash directo incluso si se borra la
  rama, hasta que se ejecute un GC.

**P4)**  
Respondida en la sección 4 (Plan de remediación).

**P5) Mecanismos preventivos:**

1. **Pre-commit hook (en la máquina del desarrollador):** un hook que corre
   antes de cada commit y escanea el diff en busca de patrones de secretos.
   Herramientas: `detect-secrets` (Yelp) o `gitleaks` en modo pre-commit.
   Si detecta un secreto, bloquea el commit antes de que entre a la historia.
2. **Escaneo server-side en CI/CD (al hacer push):** un step en el pipeline
   (GitHub Actions, GitLab CI) que corre `gitleaks` o `trufflehog` sobre el
   diff del push. Si detecta secretos, falla el build y notifica. Actúa como
   segunda barrera si el hook local fue salteado.


## 6. Evidencia de progreso

- Captura de `./ctf status extra2` con los 3 ✓: 
```bash
  ╭────────────────────────────────────────────────────────────╮
  │                   PROGRESO · LAB extra2                    │
  ╰────────────────────────────────────────────────────────────╯

   ✓  R1     Secreto "borrado" en un commit viejo (git log -p)
   ✓  R2     Commit "perdido" por un reset (git reflog / fsck)
   ✓  R3     Secreto en una rama abandonada

  ██████████████████████████████  3/3 (100%)

[ OK ] ¡Lab extra2 COMPLETO! Ponete las pilas con la próxima unidad.
```

- Archivos adjuntos confirmados:
  - `evidencia/comandos.txt` ✓
  - `evidencia/salidas/r1.txt` ✓
  - `evidencia/salidas/r2_reflog.txt` ✓
  - `evidencia/salidas/r2_commit.txt` ✓
  - `evidencia/salidas/r3_branches.txt` ✓
  - `evidencia/salidas/r3_env.txt` ✓