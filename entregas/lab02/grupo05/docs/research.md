# Mini-research — Laboratorio 02

**Tema elegido:** *(uno)*

Si consideramos al tema "A" como el tema 0, el B 1, etc; y sabiendo que somos el  
grupo N° 5,  elegimos el tema B tras hacer la operación 5 mod 4. El resultado fue  
1, por lo que elegimos la opción B.

- [ ] **A.** Modos de operación de cifrado por bloques (ECB vs CBC vs GCM) y por
  qué ECB filtra estructura (el "pingüino" de Adobe).
- [x] **B.** HMAC y el ataque de length-extension: cómo funciona el ataque y por
  qué HMAC lo previene.
- [ ] **C.** Derivación de claves desde contraseñas (PBKDF2, bcrypt, scrypt,
  Argon2): por qué un `sha256(password)` no alcanza.
- [ ] **D.** Cifrado asimétrico y firmas digitales: qué problema resuelven que el
  simétrico no.


## Desarrollo

### El problema de fondo: Merkle-Damgård y el estado expuesto

SHA-256 (como MD5 y SHA-1) está construido sobre la construcción de
Merkle-Damgård. El algoritmo parte de un estado interno inicial (IV fijo),
divide el mensaje en bloques de 512 bits y aplica iterativamente una función de
compresión:

```
estado₀ = IV (constante)
estadoᵢ = compress(estadoᵢ₋₁, bloqueᵢ)
hash(m) = estadoₙ
```

La operación termina agregando un bloque de padding que codifica la longitud
del mensaje original (esto es el _length padding_ de Merkle-Damgård, necesario
para la seguridad de la construcción básica). El valor final publicado como
digest **es exactamente el estado interno** `estadoₙ`.

Esta propiedad hace que SHA-256 sea eficiente y componible, pero tiene una
consecuencia directa: quien conozca `hash(m)` conoce el estado interno tras
procesar `m`. Puede continuar el cómputo como si fuera el propio algoritmo,
sin necesidad de haber visto `m` en absoluto.

### El ataque de length-extension paso a paso

Supongamos que un servidor genera un "MAC" como:

```
tag = sha256(clave_secreta || mensaje)
```

y lo envía al cliente junto con `mensaje`. Un atacante pasivo intercepta ambos.
No conoce `clave_secreta`.

El atacante quiere forjar un tag válido para el mensaje extendido:

```
mensaje_forjado = mensaje || padding_de_merkle_damgård || datos_extra
```

donde `padding_de_merkle_damgård` es el padding que SHA-256 habría insertado
al terminar de procesar `clave_secreta || mensaje` (calculable conociendo la
longitud estimada de la clave, que suele ser pública o deducible).

El atacante:

1. Inicializa el estado interno de SHA-256 con el valor de `tag` interceptado
   (en lugar del IV estándar).
2. Continúa el cómputo de SHA-256 alimentando `datos_extra` como si fueran
   bloques adicionales del mismo mensaje.
3. Obtiene `tag_forjado = sha256(clave_secreta || mensaje_forjado)` — un tag
   completamente válido — sin haber tocado la clave en ningún momento.

El servidor recibe `(mensaje_forjado, tag_forjado)`, computa
`sha256(clave_secreta || mensaje_forjado)` y obtiene exactamente `tag_forjado`.
La verificación pasa. La falsificación tuvo éxito.

Herramientas como **hashpump** automatizan este proceso: dados el tag original,
la longitud estimada de la clave y el string a agregar, producen el mensaje
extendido y el tag forjado en milisegundos.

### Por qué HMAC lo previene

HMAC (RFC 2104) rompe la linealidad de Merkle-Damgård con una doble envoltura
keyed:

```
HMAC(K, m) = H( (K ⊕ opad) || H( (K ⊕ ipad) || m ) )
```

- `ipad = 0x36 repetido` / `opad = 0x5c repetido` (constantes estándar)
- `K` se rellena o comprime al tamaño de bloque de H

El hash **interno** `H((K ⊕ ipad) || m)` procesa el mensaje con una clave
derivada. El resultado es un valor opaco de 32 bytes. Ese valor se convierte en
la entrada del hash **externo** junto con `K ⊕ opad`.

Un atacante que intentara aplicar length-extension al hash interno obtendría un
valor que no es la salida de HMAC: para convertirlo en un HMAC válido tendría
que invertir o falsificar el hash externo — lo que equivale a romper SHA-256,
computacionalmente inviable. La doble envoltura hace que el estado interno
después del hash externo nunca sea observable directamente.

Formalmente, se puede probar que si H es una función de hash segura en el
modelo PRF, entonces HMAC es un PRF seguro. Esta prueba no depende de la
ausencia del ataque de length-extension: HMAC es seguro incluso si H lo
padece.

### HMAC en Python (biblioteca estándar)

```python
import hmac, hashlib

def mac_hmac(clave: bytes, msg: bytes) -> str:
    return hmac.new(clave, msg, hashlib.sha256).hexdigest()

def verificar_mac(esperado: str, recibido: str) -> bool:
    # compare_digest: tiempo constante → evita timing attacks
    return hmac.compare_digest(esperado, recibido)
```

La comparación con `compare_digest` es crítica: una comparación byte a byte
normal (`==`) termina al primer byte diferente, filtrando información de cuántos
bytes ya son correctos. Un atacante que pueda medir tiempos de respuesta con
precisión puede reconstruir el MAC válido sin conocer la clave (timing attack).
`compare_digest` recorre siempre los dos strings completos en tiempo constante,
cerrando ese canal lateral.


## Fuentes

1. Krawczyk, Bellare & Canetti. **"HMAC: Keyed-Hashing for Message
   Authentication"**. RFC 2104, IETF, 1997.
   <https://www.rfc-editor.org/rfc/rfc2104>

2. Bellare, Canetti & Krawczyk. **"Keying Hash Functions for Message
   Authentication"**. CRYPTO 1996. LNCS 1109, pp. 1–15.
   <https://cseweb.ucsd.edu/~mihir/papers/kmd5.pdf>

3. Crosby, Wallach & RIEDI. **"Opportunities and Limits of Remote Timing
   Attacks"**. Rice University 2009.
   <https://www.cs.rice.edu/~dwallach/pub/crosby-timing2009.pdf>

4. NIST. **"Recommendation for Applications Using Approved Hash Algorithms"**.
   FIPS 198-1 / SP 800-107 Rev.1.
   <https://csrc.nist.gov/pubs/fips/198-1/final>


## Reflexión

Lo que más llama la atención de este tema es que el problema no está en SHA-256
sino en suponerle propiedades que no tiene. `sha256(clave || mensaje)` se
comporta exactamente como se diseñó SHA-256: procesa bytes y expone su estado.
El error está en asumir que eso equivale a autenticación. HMAC no es un parche:
es un diseño que piensa desde el principio en qué información debe ser opaca y
quién puede continuarla. La lección se generaliza a toda la criptografía
aplicada: antes de usar una primitiva hay que leer su modelo de seguridad, no
solo su firma de función.