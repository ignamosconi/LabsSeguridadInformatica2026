# Research - Lab Extra 2: El repo que delata

**Grupo:** 05.  
**Integrantes:** Ignacio Mosconi (ignamosconi) · Valentino Terreno (vterreno) · Gastón Magni (gastonmagni) · Matías Presuttari (matiaspresuttari).  
**Fecha:** 2026-10-30. 

**Método de selección de opción:** `número_de_grupo mod cantidad_de_opciones`
= `5 mod 2 = 1` → Opción B (incidente real).

**Declaración de uso de IA:** Utilizamos Claude (Anthropic) para asistir en la
búsqueda del caso, estructurar la redacción y formular la pregunta de cierre.
Las fuentes fueron verificadas individualmente por el grupo; los datos (fechas,
número de afectados, cronología) provienen de las fuentes citadas, no del modelo.


## Opción B - Un incidente real: Toyota T-Connect (2017–2022)

### Qué pasó

En diciembre de 2017, un subcontratista que desarrollaba código para **T-Connect**
(la app oficial de conectividad de Toyota, con acceso a arranque remoto, Wi-Fi
y datos del panel) subió por error parte del código fuente a un **repositorio
público de GitHub** desde su cuenta personal. Dentro del repositorio había una
clave de acceso hardcodeada al servidor de base de datos de clientes.

Con esa clave, cualquiera que encontrara el repositorio podía conectarse
directamente al backend y exportar los datos almacenados en bulk.

### Cuánto tiempo estuvo expuesto

Casi **cinco años**: desde diciembre de 2017 hasta el 15 de septiembre de 2022,
cuando un investigador externo que escanea repositorios públicos detectó la
exposición y lo reportó a Toyota. El repositorio fue hecho privado ese mismo
día; la clave fue invalidada el 17 de septiembre de 2022. Toyota anunció el
incidente públicamente el 7 de octubre de 2022.

### Qué datos quedaron expuestos

Las direcciones de email y los números de gestión de **296.019 clientes** que
usaron T-Connect entre julio de 2017 y septiembre de 2022. Nombres, tarjetas
de crédito y teléfonos no estaban en esa base de datos.

### Cómo lo encontraron

Como se mencionó anteriormente, no lo encontró Toyota:  fue un investigador 
externo que se dedicaba a escanear repositorios públicos en busca de secretos expuestos. 

### Lección: qué habría cambiado con rotación inmediata

El secreto entró al repositorio en diciembre de 2017. Si la rotación hubiera
ocurrido al día siguiente, la ventana de exposición habría sido de horas.
Al ocurrir casi cinco años después, cualquier actor que hubiera encontrado el
repositorio durante ese período tuvo acceso válido y continuo al servidor de
clientes.

La lección central es que **la clave siguió siendo válida durante cinco años**.
Hacer el repositorio privado en septiembre de 2022 no revocó retroactivamente
el acceso de quien hubiera descargado la clave antes. La única acción que cortó
el daño real fue invalidar la clave, pero esto ocurrió recién dos días después 
de descubrir la exposición.

Esto replica exactamente el escenario del lab: el "commit de limpieza" de
PhantomCorp (R1) no borró el secreto del commit anterior, igual que hacer el
repo privado no borró la clave del historial ni de los clones existentes.


## Pregunta de cierre

**GitHub escanea pushes públicos y avisa a los proveedores para revocar.
¿Por qué eso no alcanza?**

Hay al menos dos ventanas de exposición que quedan abiertas:

1. **La ventana entre el push y la detección/revocación.** El caso Toyota
   muestra el extremo: cinco años. Incluso en el mejor caso moderno, hay un
   delta de minutos u horas entre que la clave entra al historial público y
   que el proveedor la revoca. El escaneo de GitHub llega después del push,
   no antes; y actores maliciosos también monitorean el feed público de eventos
   de GitHub en tiempo real.

2. **Los clones, forks y cachés existentes.** GitHub puede hacer privado un
   repositorio y notificar al proveedor, pero no puede borrar las copias ya
   descargadas. En el caso Toyota, cualquier persona que hubiera clonado el
   repositorio durante esos cinco años tenía la clave en su copia local,
   permanentemente y sin que Toyota lo supiera. La revocación corta el acceso
   futuro al sistema destino, pero no borra el secreto de las copias
   distribuidas ni de los cachés de motores de búsqueda de código, que pueden
   retener commits por hash directo durante tiempo indeterminado.


## Fuentes

- GitGuardian - "Toyota Accidentally Exposed a Secret Key Publicly on GitHub
  for Five Years" (2022):
  https://blog.gitguardian.com/toyota-accidently-exposed-a-secret-key-publicly-on-github-for-five-years/
- Security Affairs - "Toyota Motor Corporation discloses data leak" (octubre 2022):
  https://securityaffairs.com/136915/data-breach/toyota-motor-corporation-data-leak.html
- Infosecurity Magazine - "Toyota Data Leak Could Impact 300K Customers" (octubre 2022):
  https://www.infosecurity-magazine.com/news/toyota-data-leak-customers/
- GitGuardian - "State of Secrets Sprawl 2024":
  https://www.cybersecuritydive.com/press-release/20240312-the-state-of-secrets-sprawl-2024/