# Informe — Laboratorio 04 · Marcos normativos y gestión

**Grupo:** 05
**Integrantes:** Magni, Gastón (@nosungam) · Mosconi, Ignacio (@ignamosconi) · Presuttari, Matías (@matiaspresuttari) · Terreno, Valentino (@vterreno)

**Alcance del perfil.** El escenario no da cantidad de clientes ni de empleados. Para que los dólares de la Parte B tengan denominador, asumimos una PyME argentina con personal remoto, una aplicación web pública, una oficina, y del orden de unos miles de registros de clientes (nombre, DNI y, hoy, PAN almacenado). Es un supuesto de alcance del Perfil organizacional, no un dato del enunciado. Moneda: dólares estadounidenses de septiembre de 2026, para que el ranking no dependa del tipo de cambio.

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
