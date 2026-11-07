# Research — Lab Extra 5: JWT inseguro

**Grupo:** 05 · **Integrantes:** Magni, Mosconi, Presuttari, Terreno

**Declaración de uso de IA:** Se utilizó un asistente de IA (DeepSeek) para
organizar el catálogo de ataques y revisar la redacción. Las definiciones y
recomendaciones se contrastaron contra RFC 8725 y la documentación de
PortSwigger citadas al final; la aplicación al caso del lab y la pregunta de
cierre son propias del grupo.

**Opción elegida:** A — El catálogo de ataques a JWT.

---

## 1. `alg:none` y confusión de algoritmo

### 1.1 `alg:none`

Un JWT puede declarar en su header `"alg": "none"`, que significa "sin firma".
La condición que habilita el ataque es que el servidor **confíe en el valor de
`alg` que viene en el token** y, al ver `none`, saltee la verificación de la
firma. En ese caso el atacante borra la firma (dejando el punto final), pone
los claims que quiera —`role:admin`, `sub:otro_usuario`— y el servidor los
acepta como válidos.

No es un ataque criptográfico: es un error de lógica. El servidor le pregunta
al atacante cómo quiere que lo autentiquen. Algunas librerías viejas aceptaban
`none` por compatibilidad, y también aparecen variantes con mayúsculas o
codificaciones inesperadas para evadir filtros ingenuos.

**Defensa:** fijar en la configuración del servidor la lista de algoritmos
permitidos (por ejemplo, solo `RS256` o solo `HS256`) y rechazar explícitamente
`none`. El algoritmo con el que se verifica no debe salir del token, sino de la
política del servidor. RFC 8725 §3.1 lo exige: la librería debe poder recibir
un conjunto soportado de algoritmos y no usar ninguno fuera de él.

### 1.2 Confusión de algoritmo (RS256 → HS256)

En RS256 el emisor firma con una clave **privada** RSA y el verificador usa la
**pública**. En HS256 hay una sola clave simétrica que sirve para firmar y
verificar. La confusión ocurre cuando el servidor está configurado para RS256
pero acepta el `alg` que trae el token: el atacante cambia el header a
`"alg":"HS256"` y firma con la **clave pública RSA** como si fuera el secreto
HMAC. Si la librería no separa los tipos de clave, la verificación "funciona":
la misma clave pública que el servidor usa para verificar RS256 se usa como
secreto HMAC, y el atacante conoce ese valor.

La clave pública no es secreta: suele estar publicada en un JWKS, en la
documentación o se puede derivar de tokens existentes. Por eso este ataque no
requiere crackear nada.

**Defensa:** además del pinning de algoritmo, cada clave debe usarse con un
solo algoritmo y debe validarse que el tipo de clave corresponda. Nunca se debe
permitir que una clave pública RSA se interprete como secreto HMAC. RFC 8725
§3.1–§3.2 y la documentación de PortSwigger describen el caso y la mitigación.

## 2. Inyección por `kid`, `jku` y `x5u`

### 2.1 `kid` (Key ID)

`kid` es un identificador libre que el servidor usa para elegir la clave de
verificación cuando tiene varias. El problema aparece cuando ese valor se usa
sin validar para construir una ruta de archivo, una consulta SQL o una
búsqueda en un directorio de claves.

- **Path traversal:** si el servidor hace algo como
  `leer("claves/" + kid)`, el atacante puede poner
  `"kid": "../../../../dev/null"` y forzar el uso de un archivo conocido. En
  Linux, `/dev/null` es vacío; si además el servidor acepta HS256, se firma el
  token con la cadena vacía y la verificación pasa. También se pueden apuntar
  a archivos cuyo contenido el atacante conozca.
- **Inyección SQL:** si el `kid` se concatena en una consulta que busca la
  clave en una base, el atacante puede alterar la consulta o hacer que
  devuelva una clave que él controla.

**Defensa:** tratar `kid` como un identificador opaco y validarlo contra una
allowlist de claves conocidas; nunca usarlo para construir rutas, SQL ni
comandos. Las claves deben resolverse por una tabla interna, no por un valor
arbitrario del token.

### 2.2 `jku` y `x5u`

`jku` (JWK Set URL) y `x5u` (X.509 URL) le dicen al servidor de dónde bajar la
clave para verificar. Si el servidor acepta cualquier URL, el atacante publica
su propio JWKS o certificado en un host que controla, firma el token con su
clave privada y hace que el servidor descargue la clave pública correspondiente.
El servidor verifica correctamente… contra la clave del atacante. Es una
variante de "confiar en una URL controlada por el usuario", con el agregado de
que puede derivar en SSRF: el servidor hace la petición desde su red interna.

`jwk` (clave embebida en el header) es el mismo problema sin URL: si el
servidor acepta la clave que viene dentro del token, el atacante firma con su
propia clave y la adjunta.

**Defensa:** no aceptar `jku`, `x5u` ni `jwk` arbitrarios. Si el caso de uso
los requiere, permitir solo URLs de una allowlist estricta, exigir HTTPS,
validar el origen y no seguir redirecciones; o directamente ignorar esos
headers y usar claves configuradas localmente. RFC 8725 §3.10 recomienda
sanitizar `kid` y proteger `jku`/`x5u` contra SSRF con allowlists.

## 3. Qué tienen en común

Los tres ataques explotan la misma idea: **el token no debe decidir cómo se
verifica el token**. El `alg`, el `kid`, el `jku` y el `jwk` son datos que llegan
del cliente antes de que exista una firma confiable. El servidor tiene que
partir de una configuración propia (algoritmo permitido, claves conocidas,
origen permitido) y usar los headers solo como índices dentro de ese conjunto
cerrado. La regla práctica es: validar primero, confiar después; y nunca al
revés.

## 4. Pregunta de cierre

**¿Un secreto de 32 bytes aleatorios resuelve el problema si PhantomCorp sigue
metiendo datos sensibles en el payload?**

No. Resuelve una parte, no el problema completo.

- **R2 (forja) queda mitigado:** con 256 bits de entropía, el ataque de
  diccionario de este lab deja de ser factible. Sin el secreto no se puede
  recalcular la firma ni cambiar `role` o `sub`. El ataque offline sigue
  existiendo en teoría —cualquiera puede verificar candidatos localmente— pero
  el espacio de búsqueda es inabordable.
- **R1 (confidencialidad) sigue igual de roto:** el payload sigue siendo
  base64url, no cifrado. Si el token lleva `nota_interna`, datos personales,
  un connection string o cualquier secreto de negocio, cualquiera que lo vea
  lo lee. Un secreto fuerte protege la integridad, no la lectura.
- **El riesgo de filtración del secreto sigue existiendo:** si la clave se
  filtra por un log, una variable de entorno mal protegida, un backup o un
  repositorio, el atacante vuelve a poder firmar. La entropía no reemplaza la
  rotación, el almacenamiento seguro ni la separación de funciones.
- **La autorización sigue siendo responsabilidad del servidor:** aunque el
  token esté bien firmado, un `sub=maria` legítimo o un `role` mal usado por la
  aplicación siguen siendo un problema de control de acceso. La firma dice
  "este token lo emitió quien tiene la clave", no "este usuario puede ver este
  recurso".

La solución completa combina: secreto de alta entropía (o mejor, firma
asimétrica con la privada solo en el emisor), algoritmo fijado, rotación y
revocación, claims mínimos y sin datos sensibles, expiración corta, y
autorización server-side por recurso. Si hace falta confidencialidad real en el
contenido, hay que cifrar (JWE) o no poner ese contenido en el token. Cambiar
`mate123` por 32 bytes aleatorios es necesario, pero no suficiente: tapa el
camino de R2 y deja abierta la puerta de R1.

## Fuentes

- Sheffer, Y., Hardt, D. y Jones, M. (2020). *JSON Web Token Best Current
  Practices* (RFC 8725, BCP 225). IETF.
  https://www.rfc-editor.org/rfc/rfc8725.html — §2.1 (algoritmos y `none`),
  §2.2 (claves simétricas débiles), §3.1–§3.2 (verificación y elección de
  algoritmo), §3.5 (entropía de claves), §3.10 (`kid`, `jku`, `x5u`).
- PortSwigger Web Security Academy. *JWT attacks*.
  https://portswigger.net/web-security/jwt — aceptación de firmas arbitrarias
  y `alg:none`, fuerza bruta de secretos, inyección por `jwk`/`jku`/`kid` y
  medidas de prevención.
- Jones, M., Bradley, J. y Sakimura, N. (2015). *JSON Web Token (JWT)*
  (RFC 7519). IETF. https://www.rfc-editor.org/rfc/rfc7519 — formato de claims
  y definición de los claims registrados `sub`, `exp` e `iat`.
- NIST NVD. *CVE-2015-9235* (confusión RS256→HS256 en la librería `jsonwebtoken`).
  https://nvd.nist.gov/vuln/detail/CVE-2015-9235
