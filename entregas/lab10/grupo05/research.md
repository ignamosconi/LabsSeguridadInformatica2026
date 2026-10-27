# Mini-research — Laboratorio 10

**Tema elegido:** **B. Técnicas de evasión de WAF** (ofuscación, encoding, case,
comentarios) — por qué funcionan y cómo las contrarresta un defensor.

## Desarrollo

Un **WAF** (Web Application Firewall) por firmas inspecciona cada request contra un
conjunto de patrones de ataque conocidos. En el lab vimos la versión mínima de esto:
el IDS de PhantomCorp matchea `/union\s+select/` sobre el query crudo y bloquea con
`403`. La evasión de WAF es el arte de **cambiar la representación del payload sin
cambiar su efecto**, de modo que el patrón ya no coincida pero el motor de destino
(SQL, el intérprete de rutas, el navegador) lo siga interpretando igual. Las
familias de técnicas más usadas:

**1. Comentarios inline.** En SQL, `/**/` es un comentario vacío que el motor ignora
pero que rompe la subcadena literal que busca la firma. `UNION SELECT` →
`UNION/**/SELECT` evade cualquier regla que exija un espacio entre las palabras —es
exactamente lo que hicimos en R4—. Variantes más agresivas meten el comentario
*dentro* de la palabra clave: `UN/**/ION`.

**2. Encoding (y doble encoding).** El mismo carácter admite muchas
representaciones. `space` → `%20`, `+`, `%09` (tab). En rutas, `../` → `%2e%2e%2f` o,
contra WAF que decodifican una sola vez, **double-encoding**: `%252e%252e%252f` (el
WAF ve `%2e%2e%2f`, no lo matchea como `../`, y el servidor backend lo decodifica una
segunda vez a `../`). La clave del ataque es explotar la **diferencia de
canonicalización** entre el WAF y el backend.

**3. Mayúsculas/minúsculas (case).** Una firma que busque `union` literal se evade
con `UnIoN` si el matcheo no es case-insensitive. Es el error más básico y el más
común en reglas caseras.

**4. Espacios en blanco alternativos y sin espacio.** Tabs, saltos de línea,
comentarios como separador, o directamente eliminar el separador cuando la sintaxis
lo permite. Una firma con `\s+` (uno o más espacios) se cae si el ataque no usa
ninguno.

**5. Fragmentación y low-and-slow.** A nivel red/HTTP, partir el payload en varios
paquetes o requests, o espaciar las acciones en el tiempo, evita las firmas que
miran un request aislado y los umbrales de volumen.

El patrón común es el mismo que destilamos en la tabla de firmas del informe: la
detección por subcadena/regex es frágil porque **opera sobre la forma, no sobre la
semántica**. La contramedida del lado defensor es **canonicalizar antes de
inspeccionar** (decodificar recursivamente, eliminar comentarios, normalizar
case y whitespace, resolver la ruta a su forma absoluta) y recién ahí aplicar la
regla; complementarlo con detección por anomalía/score en vez de reglas binarias; y,
sobre todo, **no depender del WAF como única barrera**: un WAF es defensa en
profundidad sobre una app que ya debería ser segura (consultas parametrizadas,
allowlists de rutas), nunca el reemplazo de esa seguridad. Como resume OWASP, el WAF
reduce la superficie y da tiempo de respuesta, pero una regla siempre se puede
evadir; la vulnerabilidad corregida, no.

## Fuentes (mín. 3)

1. OWASP — *Web Application Firewall* y *SQL Injection Bypassing WAF*. Describe las
   familias de evasión (encoding, comentarios, case) y el rol del WAF como defensa en
   profundidad, no como fix.
   https://owasp.org/www-community/Web_Application_Firewall
2. MITRE ATT&CK — *Defense Evasion* (TA0005), en particular técnicas de ofuscación de
   comandos/payloads (T1027). El marco de referencia para clasificar la cara roja de
   este lab.
   https://attack.mitre.org/tactics/TA0005/
3. PortSwigger Web Security Academy — *SQL injection* / *Obfuscating attacks using
   encoding*. Ejemplos concretos de comentarios inline, doble encoding y bypass de
   filtros.
   https://portswigger.net/web-security/sql-injection
4. OWASP — *SQL Injection Prevention Cheat Sheet*. La contramedida de fondo:
   consultas parametrizadas, por qué el WAF es complemento y no sustituto.
   https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html

## Reflexión

Investigar la evasión de WAF nos dejó la misma lección que el lab, pero con nombre
propio: cada técnica de evasión es el espejo de una debilidad de la firma, y cada
mejora de la firma abre la puerta a una evasión más elaborada. Es una carrera que el
defensor no gana a nivel de reglas —siempre hay una representación más que no
previó—. Se gana cambiando de plano: canonicalizar para que muchas formas colapsen a
una, sumar detección por comportamiento, y eliminar la vulnerabilidad en la app para
que la firma sea una alarma y no el único muro. Entender cómo evade el atacante es,
literalmente, el trabajo del defensor: no se puede escribir una buena regla sin saber
cómo se la va a romper.
