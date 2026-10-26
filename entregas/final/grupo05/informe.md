# Informe de Penetration Test — PhantomCorp "Clientes"

**Cliente:** PhantomCorp S.A.  ·  **Auditor (grupo):** 05
**Integrantes:** Gastón Magni (nosungam) — Ignacio Mosconi (ignamosconi) —
Matías Presuttari (matiaspresuttari) — Valentino Terreno (vterreno)
**Fecha:** 2026-10-26  ·  **Tipo:** Caja negra  ·  **Alcance:** host
`phantomcorp` (lab, red `labnet` aislada)

## 0. Declaración de uso de IA

Se usó Claude Code (Anthropic) como asistente durante el engagement: para
automatizar la ejecución y el formateo de los comandos de `curl` contra el
target, y para redactar un primer borrador de este informe a partir de la
evidencia recolectada. Cada hallazgo fue **validado por el grupo** contra la
salida real de los comandos (ver `loot/bitacora.md` y `loot/ctf-status-final.txt`):
ningún CVSS ni ninguna flag fue copiado de `solucion.md` ni inventado — las
cuatro flags se obtuvieron ejecutando el ataque de punta a punta sobre el
contenedor `cyberlab-phantomcorp` y se confirmaron con `./ctf submit`.

---

## 1. Resumen ejecutivo

- **Qué se hizo:** una auditoría de caja negra sobre el sistema "Clientes"
  de PhantomCorp, sin credenciales ni documentación previas, siguiendo la
  cadena recon → enumeración → explotación → post-explotación → impacto.
- **Resultado global:** compromiso total. Se encontró un portal interno no
  enlazado, se evadió su autenticación por inyección SQL, se robó un token
  de una API interna desde un backup de configuración expuesto, y con ese
  token se logró ejecución remota de comandos como **root** dentro del host,
  llegando a exfiltrar el archivo con los datos de clientes.
- **Riesgo de negocio:** exposición completa de la base de clientes
  (≈48.210 registros con nombre, DNI y número de tarjeta) y control total del
  servidor que la aloja. En producción esto es una violación de datos
  personales y financieros con exposición regulatoria y reputacional directa.
- **Recomendación prioritaria:** parametrizar la consulta de login (la causa
  raíz que habilita toda la cadena) y sacar inmediatamente el endpoint de
  ejecución de comandos (`/api/reporte`) de producción; ningún "token" alcanza
  para justificar una interfaz que ejecuta shell arbitrario.

| Severidad | Cantidad de hallazgos |
|---|---|
| Crítica | 2 |
| Alta | 2 |
| Media | 1 |
| Baja | 1 |

---

## 2. Alcance y metodología

**Alcance:** únicamente el host `phantomcorp` dentro de la red aislada del
lab (`labnet`), levantado vía `./ctf lab final`. Ningún otro host, servicio
ni red fue tocado. Ventana: la fijada por la cátedra para el práctico final.
**Permitido:** recon, enumeración, explotación y post-explotación sobre el
target. **Prohibido y no realizado:** cualquier acción destructiva (no se
borraron ni modificaron datos; `id`, `cat` y lectura de archivos fueron las
únicas acciones ejecutadas vía RCE, sin escritura ni destrucción).

Metodología seguida (la misma cadena de las Unidades 5 a 10):

1. **Reconocimiento y enumeración** (Lab 05/06) — descubrimiento de
   superficie HTTP sin asumir nada: `robots.txt`, rutas no enlazadas.
2. **Explotación** (Lab 07) — abuso de una inyección SQL en el formulario de
   login para lograr un foothold de autenticación.
3. **Post-explotación** (Lab 08) — desde el acceso ganado, búsqueda de
   credenciales/secretos adicionales que amplíen el alcance (pivoting lógico,
   no de red).
4. **Impacto** (Lab 09/10 aplicados a la práctica) — uso del secreto robado
   para alcanzar ejecución de comandos y demostrar el impacto final sobre el
   activo más sensible del sistema (los datos de clientes).

Herramientas: `curl` desde la consola atacante del lab (`cyberlab-attacker`).
No hizo falta `sqlmap`/`gobuster`/`nmap` para esta cadena puntual — la
inyección y las rutas se confirmaron manualmente porque el objetivo es
mostrar la explotación precisa, no un barrido genérico.

---

## 3. Narrativa del ataque

```
recon/enum  ->  foothold  ->  loot  ->  impacto
```

Arrancamos sin nada: ni credenciales ni mapa del sitio. Lo primero que pedimos
fue `robots.txt`, por costumbre más que por expectativa — y ahí estaba:
`Disallow: /portal-rrhh`. Un `robots.txt` no es un control de acceso, es un
cartel que dice "no indexen esto", y lo leímos igual. `/portal-rrhh` resultó
ser un portal de RRHH con un formulario de login, y el HTML traía, en un
comentario, la primera flag — una confirmación de que el equipo de desarrollo
sabe que esto "no debería" estar expuesto, pero lo dejó ahí.

El formulario pedía usuario y contraseña que no teníamos. Probamos la
inyección SQL clásica en el campo usuario: `admin' -- `. Si el backend arma
la consulta por concatenación de strings (y lo hace), ese payload cierra el
literal del usuario y convierte el resto de la cláusula `WHERE` en un
comentario SQL, anulando el chequeo de password. Funcionó: el dashboard nos
recibió como admin, entregó la segunda flag, y — generosamente — nos dijo
dónde mirar después: `/backup/rrhh.conf`.

Ese backup, servido sin ninguna autenticación adicional, tenía credenciales
de base de datos y, más interesante, un `API_TOKEN` para una API interna de
"reportes" (`/api/reporte`), junto con la tercera flag y una pista explícita
de cómo usarlo (`?token=...&cmd=...`). El nombre del parámetro ya adelantaba
el problema.

Con el token en mano, el endpoint resultó ser exactamente lo que el nombre
del parámetro sugería: ejecución de comandos del sistema operativo. `cmd=id`
confirmó que corríamos como `root` dentro del contenedor. De ahí al archivo
que el propio hito buscaba fue un solo comando: `cat
/app/priv/clientes.db.txt`, que contenía la cuarta flag junto con la
confirmación de que ahí viven los 48.210 registros de clientes (nombre, DNI,
tarjeta) — los crown jewels del alcance.

Cuatro pasos, cada uno habilitado por una falla distinta, pero todos
reducibles a una sola idea: **el sistema confía en que el atacante no llega
al paso siguiente**, en vez de defender cada paso por sí mismo.

---

## 4. Hallazgos (detalle técnico)

<!-- TODO: H-01 a H-06, ordenados por severidad -->

---

## 5. Conclusión

<!-- TODO -->

---

## 6. Anexo

<!-- TODO -->
