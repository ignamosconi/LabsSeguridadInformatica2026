# Research — Lab Extra SSRF

**Grupo:** 05 · **Integrantes:** Magni, Gastón (@nosungam) · Mosconi, Ignacio
(@ignamosconi) · Presuttari, Matías (@matiaspresuttari) · Terreno, Valentino
(@vterreno)

**Declaración de uso de IA:** usamos IA (Claude) para ordenar la redacción y
chequear que no mezcláramos detalles técnicos del caso. Los datos los tomamos de
las fuentes citadas al pie (acusación del DOJ, análisis técnicos y la
documentación de AWS) y los contrastamos entre sí; la IA no fue fuente.

## Opción A — Capital One (2019): un SSRF que terminó en 100 millones de registros

**1. Qué funcionalidad era vulnerable.** Capital One corría parte de su
infraestructura en AWS, detrás de un Web Application Firewall (ModSecurity
usado como proxy reverso) sobre una instancia EC2. El WAF estaba mal
configurado y podía ser inducido a hacer pedidos salientes en nombre del
servidor: el clásico patrón SSRF, un componente que fetchea una URL que el
atacante controla, desde la posición de red del servidor.

**2. Qué pidió el atacante a través del servidor.** En lugar de un sitio
externo, dirigió la petición al **Instance Metadata Service** de AWS, en la
dirección link-local `http://169.254.169.254/`. Concretamente consultó la ruta
de credenciales IAM de la instancia:
`.../latest/meta-data/iam/security-credentials/<rol-de-la-instancia>`. El
metadata service no pide autenticación —confía en que quien le habla es la
propia instancia—, así que respondió con las **credenciales temporales** (access
key, secret key y token de sesión) del rol asociado a esa EC2.

**3. Qué obtuvo y cuál fue el impacto.** Con esas credenciales el atacante
actuó como el rol de la instancia, que tenía permisos de lectura amplios sobre
S3. Ejecutó un `ListBuckets` y luego un `sync` que exfiltró el contenido de los
buckets. El resultado: datos de aproximadamente **100 millones de personas en
EE.UU. y 6 millones en Canadá** —solicitudes de tarjetas de crédito, con
nombres, direcciones, scores crediticios y, en un subconjunto, números de
seguridad social y de cuentas bancarias. Capital One terminó pagando una multa
de 80 millones de USD (OCC, 2020) y 190 millones en un acuerdo civil. La app
"no estaba rota": hizo exactamente lo que se le pidió.

**4. Qué mitigación lo habría impedido.** Varias capas, de fondo a superficie:

- **IMDSv2** (ver abajo): obliga a un flujo con token (PUT previo + header), lo
  que rompe el SSRF simple de un solo `GET` reflejado. Es la respuesta directa
  de AWS a esta clase de ataque.
- **Permisos IAM mínimos** en el rol de la instancia: si el rol no hubiera
  tenido lectura amplia sobre S3, el robo de credenciales valía mucho menos.
- **Control de egreso y arreglo del WAF**: impedir que el componente de borde
  alcance `169.254.169.254`, y corregir la configuración que permitía el SSRF.

## El metadata service e IMDSv2 (complemento a la Opción B)

El metadata service expone, sin autenticación, configuración de la instancia y
—lo crítico— las credenciales temporales del rol IAM. En **IMDSv1** alcanza un
`GET` a `169.254.169.254`, y por eso un SSRF que solo refleja un GET basta para
robarlas. **IMDSv2** vuelve el acceso *orientado a sesión*: primero hay que
hacer un `PUT /latest/api/token` (con un header `X-aws-ec2-metadata-token-ttl-
seconds`) para obtener un token, y recién después usar ese token en un header en
cada `GET`. Eso bloquea el SSRF típico, que casi siempre puede forzar un `GET`
simple pero no un `PUT` con headers propios; además IMDSv2 limita el hop TTL=1
para que la respuesta no salga de la instancia. Es la misma idea que vimos en
R1: "solo yo me hablo a mí mismo" deja de ser defensa cuando otro puede hablar
por vos.

## Pregunta de cierre — SSRF ("el server fetchea por vos") vs. inyección de comandos ("el server ejecuta por vos")

**Similitud.** En ambas el atacante abusa de la *identidad y la posición* del
servidor: no actúa él, actúa el servidor por él, con sus privilegios y su
ubicación de red. En los dos casos la raíz es la misma —entrada del usuario que
llega sin validar a una operación poderosa (una request de red, o la shell)— y
los dos anulan el perímetro: da igual dónde esté el atacante si el servidor hace
el trabajo sucio desde adentro.

**Diferencia.** El SSRF te da el poder de *pedir* del servidor: leés lo que el
servidor puede leer (R1–R3: panel interno, intranet, backup; en cloud,
credenciales). La inyección de comandos (Lab 07) te da el poder de *ejecutar*:
una shell, código arbitrario sobre el host. El SSRF está acotado a lo que el
destino acepte responder por HTTP/otros esquemas; la RCE no tiene ese techo.

**Cuál es más peligrosa.** En el caso general, **la inyección de comandos**:
ejecución arbitraria es control total del host (lectura *y* escritura,
persistencia, pivot), mientras que el SSRF es, en esencia, lectura/petición a
través de un proxy. Dicho eso, el matiz importa: un SSRF contra el metadata
service de la nube puede escalar a *comprometer toda la cuenta* —y por alcance
(Capital One) eso iguala o supera a una RCE en un solo host. Nuestra conclusión:
la RCE es peor por capacidad; el SSRF en cloud es peor por alcance. Lo que las
une es la lección del lab: **confiar en la ubicación de red es una defensa
ilusoria cuando la entrada del usuario llega a una operación poderosa.**

---

### Fuentes

- U.S. DOJ — *United States v. Paige Thompson*, denuncia (W.D. Wash., 2019):
  descripción del acceso al metadata service y a los buckets S3.
  https://www.justice.gov/usao-wdwa/press-release/file/1188626/download
- Krebs on Security — "What We Can Learn from the Capital One Hack" (2019):
  https://krebsonsecurity.com/2019/08/what-we-can-learn-from-the-capital-one-hack/
- AWS — *Use IMDSv2* (documentación EC2, flujo con token y mitigación de SSRF):
  https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html
- OWASP — *A10:2021 Server-Side Request Forgery (SSRF)* y *SSRF Prevention Cheat
  Sheet*: https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_%28SSRF%29/
  · https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- MITRE — *CWE-918: Server-Side Request Forgery (SSRF)*:
  https://cwe.mitre.org/data/definitions/918.html
