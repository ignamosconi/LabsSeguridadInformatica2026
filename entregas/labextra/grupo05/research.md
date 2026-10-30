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

