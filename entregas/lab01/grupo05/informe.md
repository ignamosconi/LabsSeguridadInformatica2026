# Laboratorio 01 — Informe

## Identificación

| | |
|---|---|
| **Grupo** | 05 |
| **Caso asignado (Parte A)** | SolarWinds / SUNBURST (2020) — asignado por `5 mod 6 = 5` sobre la tabla del enunciado |
| **Tema del mini-research** | Tema 2 — La cadena de suministro de software como superficie de ataque |
| **Fecha de entrega** | [COMPLETAR] |

### Integrantes

*Esta tabla también va en `INTEGRANTES.md`. Solo nombre, legajo y usuario de
GitHub. Nada de DNI, teléfono ni dirección: el repositorio es público.*

| Nombre y apellido | Legajo | Usuario de GitHub |
|---|---|---|
| Magni, Gastón | 14991 | @nosungam |
| Mosconi, Ignacio | 15288 | @ignamosconi |
| Presuttari, Matías | 14959 | @matiaspresuttari |
| Terreno, Valentino | 15079 | @vterreno |

---

# PARTE A — Análisis del incidente bajo la lente CIA

## A.1 — Cronología

| Fecha | Hecho | Fuente |
|---|---|---|
| Desde marzo de 2020 | SolarWinds distribuye versiones troyanizadas de Orion Platform (2019.4 HF5 a 2020.2 HF1): el backdoor SUNBURST fue insertado en el binario `SolarWinds.Orion.Core.BusinessLayer.dll` y firmado con el certificado legítimo de code-signing de la empresa. | CISA (2020/2021), Advisory AA20-352A |
| 13 de diciembre de 2020 | FireEye (hoy Mandiant) publica el hallazgo de la intrusión —detectada primero en su propia red— y bautiza el backdoor como SUNBURST. | FireEye/Mandiant (2020) |
| 13 de diciembre de 2020 | CISA emite la Directiva de Emergencia 21-01, ordenando a las agencias federales desconectar de inmediato las versiones comprometidas de Orion. | CISA, ED 21-01 (2020) |
| 16 de diciembre de 2020 | Se confirma que intrusos monitorearon cuentas de correo interno de los Departamentos del Tesoro y de Comercio (NTIA) de EE. UU., además de otros organismos (Estado, Energía/NNSA, Seguridad Nacional, Salud). | Mak, Slate (2020) |
| 15 de abril de 2021 | El gobierno de EE. UU. atribuye formalmente la campaña al Servicio de Inteligencia Exterior de Rusia (SVR). | CISA, AA20-352A (act. 2021) |

---

## A.2 — Activo afectado

**Activo principal:** la integridad del *pipeline* de compilación y firma de
código de SolarWinds Orion Platform — concretamente, la garantía de que el
binario `SolarWinds.Orion.Core.BusinessLayer.dll`, firmado con el certificado
de code-signing legítimo de la empresa, era exactamente el código que
SolarWinds había compilado y no contenía nada agregado sin autorización.

**Por qué es el principal:** es el activo cuyo compromiso funcionó como
vector único hacia todos los demás. Los atacantes no vulneraron a cada
víctima una por una: comprometieron la fábrica de software que ~18.000
organizaciones actualizaban de forma rutinaria y confiada, y esas
organizaciones instalaron el backdoor voluntariamente, creyendo que era una
actualización legítima firmada por su proveedor.

**Otros activos afectados** (secundarios, alcanzados *a través* del backdoor
una vez desplegado): las redes internas y cuentas de correo de organismos del
gobierno de EE. UU. —entre ellos los Departamentos del Tesoro y de Comercio
(NTIA), Estado, Energía/NNSA, Seguridad Nacional y Salud— y, en el caso de
FireEye, su propio conjunto interno de herramientas de Red Team.

---

## A.3 — Matriz CIA

| Propiedad | ¿Se violó? | Evidencia concreta |
|---|---|---|
| **Confidencialidad** | Sí | Se confirmó el monitoreo de cuentas de correo interno de los Departamentos del Tesoro y de Comercio (NTIA), y FireEye reportó la sustracción de sus herramientas de Red Team (Mak, Slate, 2020; FireEye/Mandiant, 2020). |
| **Integridad** | Sí | El dato alterado es identificable con precisión: el binario `SolarWinds.Orion.Core.BusinessLayer.dll` fue modificado para incluir el backdoor SUNBURST antes de ser firmado con el certificado legítimo de SolarWinds (CISA, AA20-352A, 2020/2021). Esta es, de hecho, la violación fundacional del incidente: sin ella no hay acceso a ningún otro activo. |
| **Disponibilidad** | No | El objetivo de la campaña fue la persistencia sigilosa a largo plazo (el backdoor operó sin ser detectado durante meses), no la interrupción de servicio. El propio mecanismo de comando y control —dominios por víctima que imitaban tráfico legítimo del protocolo de Orion, con esteganografía para ocultar los comandos— fue diseñado explícitamente para *no* generar señales de indisponibilidad que delataran la intrusión (CISA, AA20-352A, 2020/2021). |

**Justificación ampliada de la propiedad más discutible:**

La disponibilidad es la más discutible porque, superficialmente, un
incidente de esta magnitud "se siente" como si tuviera que afectar las tres
propiedades. Pero no hay evidencia de caídas de servicio, denegación de
acceso ni destrucción de datos asociadas a SUNBURST: es, por diseño, lo
opuesto a un ataque de disponibilidad. El error típico —marcar las tres
propiedades como violadas por la gravedad del hecho— es precisamente el que
el enunciado advierte que hay que evitar. Acá la respuesta correcta y
defendible es «No», y es lo que distingue a este incidente de, por ejemplo,
WannaCry, donde la disponibilidad sí fue el objetivo directo.

---

## A.4 — Encadenamiento amenaza → vulnerabilidad → impacto

| Elemento | En este caso |
|---|---|
| **Amenaza** *(quién / qué, con qué motivación)* | Un actor estatal avanzado (APT29/Nobelium), atribuido por el gobierno de EE. UU. al Servicio de Inteligencia Exterior de Rusia (SVR), con motivación de espionaje de largo plazo, no de lucro económico ni de disrupción. |
| **Vulnerabilidad** *(la debilidad concreta que se explotó)* | Controles insuficientes de integridad y aislamiento en el entorno de build/CI-CD de SolarWinds, que permitieron insertar código malicioso en el binario antes de la etapa de firma, sin que el proceso de firma detectara la discrepancia entre el código fuente auditado y el binario efectivamente firmado. |
| **Activo** *(sobre qué recayó)* | El pipeline de compilación y firma de Orion Platform, y transitivamente las redes de ~18.000 organizaciones que instalaron la actualización troyanizada. |
| **Impacto** *(consecuencia sobre el negocio o las personas)* | Acceso de espionaje no detectado durante meses a redes sensibles de múltiples agencias federales de EE. UU. y empresas privadas; sustracción de herramientas internas de FireEye; una respuesta de emergencia a escala nacional (Directiva 21-01 de CISA); y sanciones diplomáticas de EE. UU. contra Rusia en abril de 2021. |

**Redacción:**

Un actor estatal con motivación de espionaje (la amenaza) explotó controles
de integridad insuficientes en el entorno de compilación y firma de código
de SolarWinds (la vulnerabilidad) para insertar el backdoor SUNBURST en el
binario `SolarWinds.Orion.Core.BusinessLayer.dll` antes de que fuera firmado
con el certificado legítimo de la empresa. Ese binario comprometido —el
activo sobre el que recayó el ataque— se distribuyó como una actualización
de rutina a miles de clientes de Orion, entre ellos agencias del gobierno de
EE. UU., que lo instalaron confiando en la firma digital. El resultado fue
un impacto de espionaje sostenido y no detectado durante meses sobre redes
gubernamentales y privadas, seguido de una respuesta de emergencia federal y
consecuencias diplomáticas para el atacante identificado.

---

## A.5 — Dos controles mitigantes

### Control 1

| | |
|---|---|
| **Qué es** | Atestación de procedencia de build firmada criptográficamente (por ejemplo, bajo el marco SLSA — Supply-chain Levels for Software Artifacts), que ata cada binario publicado a su commit de origen y a un registro verificable del entorno de build que lo produjo, en infraestructura de build efímera y aislada de Internet. |
| **Propiedad de la tríada que protege** | Integridad. |
| **Por qué habría funcionado en este caso concreto** | El ataque dependió exactamente de que el binario firmado no coincidiera con el código fuente auditado, sin que nadie pudiera detectarlo. Con atestación de procedencia (SLSA nivel 2 o superior), el binario `SolarWinds.Orion.Core.BusinessLayer.dll` habría llevado un registro verificable de qué código fuente y qué build efectivamente lo generaron; una discrepancia entre ese registro y el commit auditado habría sido detectable antes de la firma, y no después de nueve meses de explotación. |

### Control 2

| | |
|---|---|
| **Qué es** | Filtrado de salida (egress filtering) y monitoreo de anomalías en tráfico DNS/HTTP saliente, con una lista de permitidos estricta para los destinos con los que el software de monitoreo de red (Orion) necesita comunicarse legítimamente. |
| **Propiedad de la tríada que protege** | Confidencialidad. |
| **Por qué habría funcionado en este caso concreto** | El backdoor SUNBURST se comunicaba con dominios por víctima bajo `avsvmcloud[.]com`, imitando el protocolo legítimo de Orion y usando esteganografía para ocultar los comandos (CISA, AA20-352A, 2020/2021). Un control de egreso que solo permitiera tráfico saliente hacia los endpoints oficiales y documentados de SolarWinds habría bloqueado o, como mínimo, expuesto en los logs esas conexiones no autorizadas, acortando de forma significativa los meses de acceso no detectado que permitieron el monitoreo de correo del Tesoro y de NTIA. |

---

## A.6 — Fuentes consultadas (Parte A)

1. [PRIMARIA] Cybersecurity and Infrastructure Security Agency. (2020, 17 de diciembre; actualizado 2021, 15 de abril). *Advanced persistent threat compromise of government agencies, critical infrastructure, and private sector organizations* (Cybersecurity Advisory AA20-352A). U.S. Department of Homeland Security. https://www.cisa.gov/news-events/cybersecurity-advisories/aa20-352a
2. [PRIMARIA] Cybersecurity and Infrastructure Security Agency. (2020, 13 de diciembre). *Emergency Directive 21-01: Mitigate SolarWinds Orion code compromise*. U.S. Department of Homeland Security. https://www.cisa.gov/news-events/directives/ed-21-01-mitigate-solarwinds-orion-code-compromise-closed
3. [PRIMARIA] FireEye/Mandiant. (2020, 13 de diciembre). *Highly evasive attacker leverages SolarWinds supply chain to compromise multiple global victims with SUNBURST backdoor*. https://www.fireeye.com/blog/threat-research/2020/12/evasive-attacker-leverages-solarwinds-supply-chain-compromises-with-sunburst-backdoor.html
4. [SECUNDARIA] Mak, A. (2020, 16 de diciembre). *What we know about the hack of Commerce, Treasury, and other departments*. Slate. https://slate.com/technology/2020/12/solarwinds-hack-commerce-treasury-breach.html

---

# PARTE B — Integridad con funciones de hash

## B.1 — Evidencia de ejecución

*Pegá la salida real de cada comando. No la transcribas a mano: copiala tal
cual sale de la terminal.*

### Generación del manifiesto

```
$ python3 src/integridad.py generar --dir data/muestra --salida manifest.sha256

(pegar salida)
```

### Verificación sobre un directorio íntegro

```
$ python3 src/integridad.py verificar --dir data/muestra --manifiesto manifest.sha256
$ echo "código de salida: $?"

(pegar salida)
```

### Detección de la modificación de un byte

*Esta prueba es obligatoria y tiene una penalización específica en la rúbrica
si falla.*

```
$ printf 'X' >> data/muestra/transferencia.txt
$ python3 src/integridad.py verificar --dir data/muestra --manifiesto manifest.sha256
$ echo "código de salida: $?"

(pegar salida — debe reportar MODIFICADO y salir con 1)
```

### Detección de archivo faltante y de archivo nuevo

```
(pegar los comandos que usaron y la salida)
```

### Efecto avalancha

```
$ python3 src/integridad.py avalancha --a "transferencia: $1000" --b "transferencia: $1001"

(pegar salida)
```

**Distancia obtenida:** ____ bits de 256 (____ %)

*¿Coincide con lo esperado? ¿Qué esperaban antes de correrlo?*

### HMAC

```
$ python3 src/integridad.py mac --clave "secreto" --mensaje "transferir 1000"

(pegar salida)
```

```
$ python3 src/integridad.py mac --clave "secreto" --mensaje "transferir 1000" --verificar <tag válido>
$ python3 src/integridad.py mac --clave "secreto" --mensaje "transferir 1000" --verificar <tag alterado>

(pegar ambas salidas)
```

---

## B.2 — Decisiones de implementación

*Qué decisiones tuvieron que tomar que el enunciado no resolvía por ustedes.
Ejemplos: cómo trataron los enlaces simbólicos, qué hicieron con los archivos
vacíos, cómo excluyeron el manifiesto del recorrido, qué pasa si el directorio
está vacío. Una o dos oraciones por decisión.*

| Decisión | Qué hicimos | Por qué |
|---|---|---|
| | | |
| | | |

---

## B.3 — Preguntas de análisis

> **Se responden con fundamento técnico, no con opinión.** Dos o tres párrafos
> cada una. Las respuestas de una línea no suman puntos.

### 1. El manifiesto por sí solo no alcanza

*Un atacante con acceso de escritura al directorio también puede escribir
`manifest.sha256`. ¿Qué le impide modificar un archivo y regenerar el
manifiesto para que todo dé `OK`? ¿Qué habría que cambiar en el esquema para
que ese ataque no funcione?*

**Respuesta:**

---

### 2. Qué agrega HMAC y qué no

*¿Qué propiedad de seguridad aporta HMAC que un hash simple no aporta? Y la
parte importante: ¿qué **no** resuelve HMAC? Pensá en el no repudio y en
quién conoce la clave.*

**Respuesta:**

---

### 3. MD5 y SHA-1

*Ambos siguen apareciendo en software en producción. ¿Qué propiedad
criptográfica se les rompió, exactamente? ¿Hay algún uso en el que todavía
sean aceptables, o ninguno? Fundamentá con al menos una fuente.*

**Respuesta:**

**Fuente:**

---

### 4. Comparación en tiempo constante

*¿Por qué comparar un tag de autenticación con `==` puede filtrar información
al atacante, y cómo lo evita `hmac.compare_digest()`? Describí el ataque
concreto que esto previene.*

**Respuesta:**

---

### 5. SHA-256 para contraseñas: mala idea

*SHA-256 es una función de hash criptográfica sólida. ¿Por qué, entonces, es
una mala elección para almacenar contraseñas? ¿Qué se usa en su lugar y qué
propiedad tienen esas funciones que SHA-256 no tiene?*

**Respuesta:**

---

# Cierre

## Dificultades encontradas

*Qué les costó, dónde se trabaron, qué decidieron y por qué. Esta sección se
lee y suma. No es relleno: es donde se ve si entendieron el problema.*

---

## Distribución del trabajo

*Quién hizo qué. Tiene que ser consistente con el historial de commits.*

| Integrante | Aportes |
|---|---|
| Magni, Gastón | |
| Mosconi, Ignacio | |
| Presuttari, Matías | |
| Terreno, Valentino | |

---

## Declaración de uso de asistentes de IA

> **Obligatoria.** No está prohibido usar asistentes de IA. Lo que se evalúa es
> que entiendan lo que entregan. La omisión de esta declaración es **causal de
> rechazo automático** de la entrega. Una declaración honesta no baja la nota.

**¿El grupo usó asistentes de IA en este trabajo?**  Sí / No

*Si la respuesta es No, firmen igual la sección y pasen al final.*

| Herramienta | Para qué se usó | Qué partes del entregable afectó | Cómo se verificó que lo devuelto era correcto |
|---|---|---|---|
| | | | |
| | | | |

**Declaración:**

*El grupo declara que comprende el contenido íntegro de lo entregado y que
puede explicar y defender oralmente cualquier parte del código y del análisis,
independientemente de la asistencia recibida.*

---

## Fuentes consultadas (general)

*Todas las fuentes del trabajo, en formato APA. Las de la Parte A pueden
repetirse acá o referenciarse a la sección A.6.*

1.
2.
3.
