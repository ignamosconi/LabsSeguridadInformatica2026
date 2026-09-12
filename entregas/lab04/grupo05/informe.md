# Informe — Laboratorio 04 · Marcos normativos y gestión

**Grupo:** 05
**Integrantes:** Magni, Gastón (@nosungam) · Mosconi, Ignacio (@ignamosconi) · Presuttari, Matías (@matiaspresuttari) · Terreno, Valentino (@vterreno)

**Alcance del perfil.** El escenario no da cantidad de clientes ni de empleados. Para que los dólares de la Parte B tengan denominador, asumimos una PyME argentina con personal remoto, una aplicación web pública, una oficina, y del orden de unos miles de registros de clientes (nombre, DNI y, hoy, PAN almacenado). Es un supuesto de alcance del Perfil organizacional, no un dato del enunciado. Moneda: dólares estadounidenses de septiembre de 2026, para que el ranking no dependa del tipo de cambio.

## 0. Declaración de uso de IA

**¿El grupo usó asistentes de IA?** Sí.

| Herramienta | Para qué | Qué partes afectó | Cómo se verificó |
|---|---|---|---|
| Cursor (asistente de código) | Redactar el informe y el mini-research, implementar `ale`, `roi_control` y `priorizar`, y contrastar identificadores del marco contra las fuentes. | Toda la entrega: `src/riesgo.py`, `riesgos.json`, `informe.md` y `research.md`. | Las fórmulas se corrieron contra los ejemplos del enunciado (`20000.00` y `0.875`). Las subcategorías se leyeron en el PDF de NIST CSWP 29, no de memoria. Las cinco funciones concurrentes y las cuatro respuestas al riesgo se leyeron en NIST CSWP 04162018. Los artículos 2 y 9 de la Ley 25.326 se leyeron en el texto actualizado de Infoleg. Los ALE y los ROI del informe son la salida del script, no un número pegado a mano. |

Una declaración honesta no reemplaza entender la entrega. El grupo responde por las decisiones: CSF 2.0 y no ISO 27001, evitar el PAN en vez de cifrarlo y seguir guardándolo, no poner el ALE posterior del backup en cero, y no tratar el seguro del disco como si reemplazara la única copia.

## 1. Parte A — Marco aplicado

### A.1 — Qué marco, y por qué este

Elegimos el **NIST Cybersecurity Framework 2.0** (Pascoe, Quinn y Scarfone, 2024), no ISO/IEC 27001.

ISO/IEC 27001 certifica un sistema de gestión. PhantomCorp, tal como está descrita, no tiene política, roles, alcance ni ciclo de mejora: tiene un servidor público, un disco en la oficina y tres ausencias (MFA, política de contraseñas, plan de respuesta). Armar el teatro de una certificación sobre eso no decide qué proteger ni cuánto gastar. El CSF no pide certificado y no prescribe cómo lograr cada resultado. Es una taxonomía de resultados —funciones, categorías, subcategorías— pensada para que cualquier organización, sin importar tamaño ni madurez, entienda, evalúe, priorice y comunique su esfuerzo (Pascoe et al., 2024). Se usa escribiendo un Perfil actual y un Perfil objetivo, y cerrando la brecha en orden de riesgo (Pascoe et al., 2024, sec. 3). Eso es exactamente la pregunta del laboratorio.

Usamos la **versión 2.0** (26 de febrero de 2024), no la 1.1. La 1.1 sigue siendo la fuente que nombró las cinco funciones como concurrentes y continuas —Identify, Protect, Detect, Respond, Recover— y que ya listaba las cuatro respuestas al riesgo: mitigar, transferir, evitar y aceptar (National Institute of Standards and Technology [NIST], 2018, sec. 1.1 y 1.2). Pero el Core de 2018 no es el vigente. Mapear a `PR.AC-7` o `RS.RP-1` sería citar controles que el marco actual no tiene. Los identificadores de abajo son del apéndice A de NIST CSWP 29.

La versión 2.0 agregó una sexta función, **Govern**, en el centro de la rueda: no reemplaza a las otras cinco, las prioriza (Pascoe et al., 2024). El enunciado pide las cinco. Las usamos como pide el enunciado, y no fingimos que Govern no existe: sin una política mínima (GV.PO-01) un MFA “recomendado” no es un resultado, es un deseo. La respuesta al riesgo, en el Core 2.0, queda en ID.RA-06: las respuestas se eligen, se priorizan, se planifican, se siguen y se comunican. No se mitiga todo.

El mini-research es del mismo marco. No es la razón de la elección. Es la consecuencia de no mezclar dos vocabularios en la misma entrega. La razón es el escenario.

### A.2 y A.3 — Cinco debilidades, resultado del marco, respuesta

El escenario nombra más de cinco huecos. Estas son las cinco que cambian la decisión. El servidor web público no tiene fila propia: es el camino por el que se realizan la fila 2 y la fila 3. Parchar la plataforma (PR.PS-02, “Software is maintained, replaced, and removed commensurate with risk”) entra en el plan de acción; no es una sexta debilidad.

| # | Debilidad del escenario | Función y subcategoría (CSF 2.0, texto del Core) | Respuesta |
|---|---|---|---|
| 1 | Guardan nombres, DNI y tarjetas, y no hay inventario ni clasificación | **Identify.** ID.AM-07: inventarios de datos y de sus metadatos. ID.AM-05: los activos se priorizan por clasificación, criticidad e impacto | **Mitigar** |
| 2 | Custodian el número de tarjeta (PAN) en sistemas propios | **Protect.** PR.DS-01: se protege la confidencialidad, integridad y disponibilidad de los datos en reposo | **Evitar** |
| 3 | Empleados con acceso remoto, sin MFA y sin política de contraseñas | **Protect.** PR.AA-03: usuarios, servicios y hardware se autentican. PR.AA-01: las identidades y credenciales se gestionan | **Mitigar** |
| 4 | El único backup es un disco en la oficina | **Recover**, con el resultado de copia en Protect. PR.DS-11: los backups se crean, protegen, mantienen y prueban. RC.RP-03: la integridad de los backups se verifica antes de usarlos | **Mitigar** |
| 5 | No hay plan de respuesta a incidentes. Sobre el servidor público no hay detección descrita | **Respond** (y Detect como condición). ID.IM-04: los planes de respuesta se establecen, comunican, mantienen y mejoran. RS.MA-01: el plan se ejecuta con terceros una vez declarado el incidente. RS.CO-02: se notifica a los interesados. DE.CM-01: se monitorean redes y servicios | **Transferir** |

Los textos de subcategoría están tomados de Pascoe et al. (2024), apéndice A. No renombramos categorías de la versión 1.1 para que “caigan” en la función que nos convenía. ID.IM-04 está bajo Identify, no bajo Respond. Lo decimos igual: la ausencia de plan se *establece* ahí, y se *nota* cuando Respond no puede ejecutar RS.MA-01.

**1. Inventario — mitigar.** No se puede transferir “saber qué se tiene”. Un proveedor puede armar la planilla; el deber del artículo 9 de la Ley 25.326 sigue en el responsable del archivo: adoptar medidas técnicas y organizativas para evitar adulteración, pérdida, consulta o tratamiento no autorizado, y no registrar datos personales en archivos que no reúnan condiciones de integridad y seguridad (Ley 25.326, 2000, art. 9). Aceptar la ceguera no es una aceptación documentada: sin ID.AM-05 no hay criterio para las otras cuatro filas. Evitar “tener clientes” apaga la empresa. La mitigación es chica: un inventario de dónde viven nombre, DNI y PAN, y una clasificación por impacto. Es la condición del resto, no el control estrella.

**2. PAN — evitar, no “cifrar y seguir guardando”.** El DNI y el nombre son datos personales. No son datos sensibles: el artículo 2 reserva esa categoría a origen racial o étnico, opiniones políticas, convicciones religiosas, filosóficas o morales, afiliación sindical, salud y vida sexual (Ley 25.326, 2000, art. 2). El error sería tratar la tarjeta como si la ley la llamara “sensible” y, con eso, dramatizar. El error inverso es creer que, porque no es sensible, se puede dejar en un disco. El artículo 9 cubre todo dato personal.

La respuesta al **PAN** no es mitigar con cifrado en reposo y seguir siendo un vault. Cifrar baja el SLE y deja a PhantomCorp dentro del alcance contractual de las marcas de tarjeta y de un incidente de PAN. El escenario no dice que el negocio sea custodiar números de tarjeta. Dice que los guarda. Evitar esa actividad —cobrar por un procesador y conservar un token— achica el alcance más que volverse un custodio competente. El seguro no borra el PAN del disco, así que transferir no responde esta fila. El DNI no se evita: hay que seguir tratándolo. Para el DNI, bajo el mismo PR.DS-01, la respuesta es mitigar (acceso mínimo y cifrado en reposo). Una fila, dos datos, dos respuestas. Mezclarlas en “mitigar los datos” sería la salida fácil que la rúbrica pide no tomar.

**3. Acceso remoto — mitigar.** Evitar el acceso remoto contradice el escenario: el personal trabaja a distancia. Aceptarlo sin segundo factor, con DNI y tarjetas del otro lado, no está justificado: en la Parte B esta fila es el segundo ALE (28.000 USD/año), no un residual. Transferir tampoco autentica a nadie; el seguro cubre una cola, no reemplaza PR.AA-03. La mitigación es MFA en el acceso remoto, resistente a phishing para quien administra el servidor y los backups, y una política de credenciales que priorice longitud y una lista de denegación. No un cartel de “una mayúscula, un número y un símbolo”, que la gente elude y que no es lo que PR.AA-01 pide.

**4. Disco de oficina — mitigar.** Acá es fácil citar mal el marco. PR.DS-11 está en Protect. El resultado de negocio que falla es Recover: si la única copia está en la oficina, RC.RP-03 no se puede cumplir cuando el ransomware cifra el disco o el incendio lo quema. Decir solo “Recover” sin el identificador de Protect sería inventar un control. Decir solo “Protect” ocultaría que el daño es no poder restaurar.

Transferir no alcanza: el seguro de incendio paga el disco, no reconstruye el padrón si esa copia era la única. Aceptar tampoco: el ALE del ransomware asociado a esa copia única es el más alto del ranking (34.000 USD/año). Evitar los backups es peor que el disco. La mitigación es una copia fuera de la oficina, inmutable, y una prueba de restauración. El ROI está en B.2. No es “comprar un disco más grande para la misma oficina”.

**5. Sin plan — transferir la capacidad, no la existencia del plan.** Una PyME no arma un CSIRT. Mitigar Respond hasta tener analistas de guardia es el SOC de 80.000 USD/año que en B.2 tiene ROI negativo. Aceptar “no tenemos plan” no es aceptar un residual medido: es no haber elegido respuesta. Evitar los incidentes no es una estrategia.

La respuesta es **transferir** la capacidad especializada: un retainer que haga forense, contención fuera de horario y apoyo para notificar (RS.MA-01 y RS.CO-02 hablan, justamente, de terceros y de interesados). Esa transferencia tiene una precondición que no se compra: una página interna que diga quién declara el incidente, a qué número llama y a quién hay que avisar. Eso es ID.IM-04, y sin esa página el retainer no se activa. Transferir sin la página no es transferir; es abandonar. La detección en cero sobre el servidor público se mitiga en lo mínimo (logs que alguien mire, DE.CM-01). El residual de no pagar un SOC 24/7 se acepta, y B.2 muestra por qué.

Ninguna de las cinco filas es “mitigar porque sí”. Dos se mitigan porque la alternativa destruye el negocio o no restituye el único ejemplar (filas 3 y 4). Una se mitiga porque sin ella no hay decisión (fila 1). Una se evita porque la actividad no debería existir (fila 2). Una se transfiere porque el control propio no se paga (fila 5).

## 2. Parte B — Riesgo cuantitativo

SLE es la pérdida si el evento ocurre. ARO es cuántas veces por año creemos que ocurre. ALE = SLE × ARO. El ROI de un control es (ALE antes − ALE después − costo anual) / costo anual. Mayor que cero: el control se paga. Los tres números de abajo salen de `src/riesgo.py`, no de una planilla paralela.

Los ARO son supuestos de planificación, no frecuencias medidas. Un ALE no es una predicción del año que viene. Es una forma de no gastar el presupuesto en el miedo más ruidoso. Si el supuesto de ARO está mal, el ranking puede voltearse: lo decimos en B.1, no lo escondemos.

### B.1 — Ranking por ALE, y dónde no coincide con la intuición

```text
$ python3 src/riesgo.py priorizar --archivo riesgos.json
      34000.00  Ransomware que cifra el unico backup (disco de oficina)
      28000.00  Toma de cuenta de empleado remoto (sin MFA ni politica de contrasenas)
      24000.00  Filtracion de PAN y DNI por el servidor web publico
       7700.00  Dano extra por ausencia de plan de respuesta (sin doble conteo)
       1350.00  Perdida fisica del disco de oficina (incendio o robo, sin ciberataque)
```

| Orden | Riesgo | SLE (USD) | ARO | ALE (USD) |
|---|---|---:|---:|---:|
| 1 | Ransomware que cifra el único backup | 85.000 | 0,40 | 34.000 |
| 2 | Toma de cuenta remota, sin MFA ni política | 28.000 | 1,00 | 28.000 |
| 3 | Filtración de PAN y DNI por la web pública | 160.000 | 0,15 | 24.000 |
| 4 | Daño extra por no tener plan (sin doble conteo) | 22.000 | 0,35 | 7.700 |
| 5 | Pérdida física del disco, sin ciberataque | 45.000 | 0,03 | 1.350 |

**No coincide con la intuición en el primer puesto.** La intuición pone la filtración de tarjetas arriba: es el SLE más alto (160.000) y es el dato que da más vergüenza explicar. El ALE la deja tercera. El ransomware gana porque el factor de exposición de la única copia es casi 1 y el ARO (0,40) es más alto que el de una filtración completa (0,15). “El evento más caro” y “el riesgo que más cuesta por año” no son la misma frase. El laboratorio existe para esa diferencia.

**Tampoco coincide en el segundo.** La toma de cuentas se siente menor porque cada evento no es un desastre: 28.000, no 160.000. A razón de una por año, el ALE queda encima de la filtración. La frecuencia es lo que la intuición descuenta.

**El plan de respuesta queda cuarto, y está bien que quede cuarto.** Sin plan se siente como el problema más grande. Cuantitativamente el SLE de esta fila es solo el adicional por demora (22.000), no el incidente entero. Si hubiéramos vuelto a sumar el SLE del ransomware, el ranking habría premiado el doble conteo. La ausencia de plan importa, y no es el riesgo número uno.

**El disco que se quema queda último, y eso no autoriza a ignorarlo.** ALE 1.350 contra un SLE de 45.000: el evento es grave y raro. Es otra amenaza que el ransomware. No se suman. La decisión de no comprar una caja fuerte está en B.3. La decisión de no dejar esa copia como única está en B.2.

El ranking es sensible al ARO de la filtración. 34.000 / 160.000 = 0,2125. Si creyéramos que un servidor público con PAN almacenado se compromete más de una vez cada 4,7 años (ARO > 0,2125), la filtración pasaría al primer puesto y la intuición ganaría. Dejamos 0,15 a propósito y lo marcamos: el orden 1 no es un hecho, es el supuesto. Por eso B.2 no propone “un firewall para la vergüenza de las tarjetas”. Propone el control del riesgo que el ALE pone primero, y la fila 2 de la Parte A (evitar el PAN) achica el SLE de la tercera fila por otro camino.

### B.2 — Control del riesgo número uno, y si conviene

El riesgo número 1 es el ransomware con un solo disco en la oficina. El control no es “otro disco al lado”. Es una copia **fuera de la oficina, inmutable**, y una prueba de restauración por trimestre. Eso es lo que piden PR.DS-11 y RC.RP-03, no un vendor.

**Costo anual: 7.200 USD.** Almacenamiento inmutable, 2.400. Equipo o servicio amortizado, 1.800. Horas de las pruebas de restore, 3.000. Es un orden de magnitud de PyME, no una cotización.

**ALE antes: 34.000** (85.000 × 0,40).

**ALE después: 15.200. No cero.** El backup no frena la exfiltración. Del SLE de 85.000, unos 55.000 son destrucción, caída larga y palanca de rescate: bajan a 8.000, que es la ventana de restaurar. Los otros 30.000 (respuesta, aviso, datos que ya se fueron) siguen ahí. SLE posterior = 38.000. El ataque sigue ocurriendo, así que el ARO se queda en 0,40. ALE posterior = 38.000 × 0,40 = 15.200. Poner el ALE posterior en cero habría inflado el ROI.

```text
$ python3 src/riesgo.py roi --antes 34000 --despues 15200 --costo 7200
1.611
```

Pérdida evitada = 34.000 − 15.200 = 18.800. Neta de costo = 11.600. ROI = 11.600 / 7.200 = 1,611. **Conviene.** Cada dólar de costo evita 2,61 dólares de pérdida (18.800 / 7.200) y deja 1,61 dólares netos. El 1,611 que imprime el script es ese neto sobre el costo, la misma convención del enunciado (0,875).

El control que no conviene, para no mitigar por reflejo: un SOC 24/7 a 80.000 USD/año que solo baje el ARO del ransomware de 0,40 a 0,25. ALE posterior = 85.000 × 0,25 = 21.250.

```text
$ python3 src/riesgo.py roi --antes 34000 --despues 21250 --costo 80000
-0.841
```

No se paga. Por eso la fila 5 de la Parte A transfiere la guardia y acepta no tener SOC. El backup inmutable se compra. El SOC, no.

### B.3 — Un riesgo que no se mitiga

La pérdida física del disco (incendio o robo, sin ciberataque) tiene ALE 1.350. Una caja fuerte certificada y una ronda dedicada salen más que eso por año. El ROI de un búnker sobre este ALE es negativo. **No se mitiga así.**

La respuesta es **transferir** el valor del hardware y la interrupción corta con un seguro de contenido, y **aceptar** la molestia residual de perder esa copia. Hay una condición, y sin ella la frase es falsa: esto vale **después** del control de B.2. Si el disco de la oficina sigue siendo la única copia, el seguro no reconstruye el padrón, y transferir sería esconder el riesgo número 1 detrás de una póliza. Con la copia inmutable ya existente, perder el disco de la oficina es perder un ejemplar, no el registro. Ese residual sí se transfiere y, en la parte que la póliza no cubre (unas horas de ir a buscar la otra copia), se acepta.

No es el mismo verbo que la fila 5. Allá se transfiere una capacidad que la PyME no va a staffear. Acá se transfiere un perjuicio económico chico y se rechaza un control cuyo costo supera el ALE.

## Bitácora

Corrido desde `entregas/lab04/grupo05/` con Python 3. Los dos primeros comandos son los del enunciado. El tercero es el ranking de esta entrega.

```text
$ python3 src/riesgo.py ale --sle 50000 --aro 0.4
20000.00

$ python3 src/riesgo.py roi --antes 20000 --despues 5000 --costo 8000
0.875

$ python3 src/riesgo.py priorizar --archivo riesgos.json
      34000.00  Ransomware que cifra el unico backup (disco de oficina)
      28000.00  Toma de cuenta de empleado remoto (sin MFA ni politica de contrasenas)
      24000.00  Filtracion de PAN y DNI por el servidor web publico
       7700.00  Dano extra por ausencia de plan de respuesta (sin doble conteo)
       1350.00  Perdida fisica del disco de oficina (incendio o robo, sin ciberataque)

$ python3 src/riesgo.py roi --antes 34000 --despues 15200 --costo 7200
1.611

$ python3 src/riesgo.py roi --antes 34000 --despues 21250 --costo 80000
-0.841
```

Un costo anual de cero no entra en la fórmula. El programa sale con código 1 y un mensaje, no con un traceback: `error: costo_anual no puede ser 0: el ROI divide por el costo del control`.

## 3. Anexo — riesgos.json

El archivo de la entrega es `riesgos.json`. Los nombres van sin tilde para que coincidan con la salida del script. El campo `supuesto` no lo lee el programa; `priorizar` lo conserva y ordena por el ALE que recalcula.

```json
[
  {
    "nombre": "Ransomware que cifra el unico backup (disco de oficina)",
    "sle": 85000,
    "aro": 0.4
  },
  {
    "nombre": "Toma de cuenta de empleado remoto (sin MFA ni politica de contrasenas)",
    "sle": 28000,
    "aro": 1.0
  },
  {
    "nombre": "Filtracion de PAN y DNI por el servidor web publico",
    "sle": 160000,
    "aro": 0.15
  },
  {
    "nombre": "Dano extra por ausencia de plan de respuesta (sin doble conteo)",
    "sle": 22000,
    "aro": 0.35
  },
  {
    "nombre": "Perdida fisica del disco de oficina (incendio o robo, sin ciberataque)",
    "sle": 45000,
    "aro": 0.03
  }
]
```

El SLE de cada fila, partido en componentes, está en el campo `supuesto` del archivo. No se repite acá para no mantener dos copias que puedan divergir.

## Fuentes de la Parte A y de la Parte B

Ley 25.326. (2000). *Protección de los datos personales*. Honorable Congreso de la Nación Argentina. Artículos 2 y 9. http://servicios.infoleg.gob.ar/infolegInternet/anexos/60000-64999/64790/texact.htm

National Institute of Standards and Technology. (2018, 16 de abril). *Framework for improving critical infrastructure cybersecurity, version 1.1* (NIST CSWP 04162018). https://doi.org/10.6028/NIST.CSWP.04162018

Pascoe, C., Quinn, S. y Scarfone, K. (2024, 26 de febrero). *The NIST Cybersecurity Framework (CSF) 2.0* (NIST CSWP 29). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.CSWP.29

## Dificultades

Lo que más costó no fue la multiplicación. Fue no citar un Core viejo para que la fila “caiga” en la función que el enunciado nombra. ID.IM-04 —el plan se establece— está en Identify. RS.MA-01 supone que el plan ya existe y se ejecuta. Inventar `RS.RP-1` de la versión 1.1 habría sido prolijo y falso. Lo dejamos escrito así.

La otra trampa fue el ALE posterior del backup. Si lo poníamos en cero, el ROI mentía: la copia inmutable no frena la exfiltración. Bajar solo la parte de destrucción (55.000 a 8.000) y dejar los 30.000 de respuesta y aviso es menos lucido y es lo que el control realmente hace.

El ARO sigue siendo un supuesto. Si la filtración de PAN supera 0,2125 eventos por año, el ranking se da vuelta. Preferimos mostrarlo a defender el orden 1 como si fuera un hecho.

## Distribución del trabajo

Cada integrante es autor de al menos un commit. El resto figura como coautor en todos, porque las decisiones (qué marco, qué respuesta, qué ARO) se discutieron sobre el mismo borrador.

| Integrante | Autor de |
|---|---|
| Magni, Gastón (@nosungam) | Copia del esqueleto, `priorizar`, mini-research |
| Mosconi, Ignacio (@ignamosconi) | `INTEGRANTES.md`, `riesgos.json`, esta declaración y el cierre |
| Presuttari, Matías (@matiaspresuttari) | `ale`, Parte A del informe |
| Terreno, Valentino (@vterreno) | `roi_control`, el error de costo cero, Parte B del informe |
