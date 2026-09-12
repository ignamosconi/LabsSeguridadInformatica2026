# Mini-research — Laboratorio 04

**Grupo:** 05
**Tema elegido:** B — NIST Cybersecurity Framework: las cinco funciones y cómo se usan
**Cantidad de palabras:** 994 (planteo, desarrollo, tensión y cierre; sin bibliografía, reflexión ni declaración)

## Planteo

Cualquiera que haya visto una lámina de ciberseguridad puede recitar Identify, Protect, Detect, Respond, Recover. Casi nadie, recitándolas, puede decir qué decisión cambia. La tesis de este trabajo es que las cinco funciones no son un plan de implementación, ni una escala de madurez, ni una checklist. Son un idioma compartido de resultados. Se usan escribiendo un Perfil actual y un Perfil objetivo, y cerrando la brecha en orden de riesgo. Recorrer la rueda “en orden” es no haberlas usado.

## Desarrollo

La versión 1.1, la que todavía nombra cinco funciones y no seis, las define como concurrentes y continuas: Identify, Protect, Detect, Respond, Recover (National Institute of Standards and Technology [NIST], 2018, sec. 1.1). Concurrentes: no se termina Identify para empezar Protect. Continuas: Detect no es la fase tres de un proyecto. Juntas sirven para expresar la gestión del riesgo, ordenar información, decidir, tratar amenazas y mejorar con lo ya ocurrido. El mismo documento nombra las cuatro respuestas: mitigar, transferir, evitar o aceptar (NIST, 2018, sec. 1.2). Las funciones no reemplazan esa elección. La organizan.

El Core de la versión 2.0 conserva esas cinco y les agrega Govern, en el centro de la rueda, porque sin contexto, estrategia y política las otras cinco se vuelven una lista técnica (Pascoe, Quinn y Scarfone, 2024). El documento pone dos límites que la lámina suele borrar. El orden y el tamaño de las funciones en el Core no implican secuencia ni importancia. Y los resultados no son una checklist de acciones: la acción que logra un resultado cambia con la organización (Pascoe et al., 2024). El marco no prescribe cómo se logra cada resultado. Quien cita una función y pega debajo una herramienta está usando el CSF al revés.

Cada función vigente es un verbo sobre un resultado, no un producto. Identify entiende el riesgo actual y qué priorizar. Protect aplica salvaguardas —identidad, datos, plataforma, resiliencia— sobre eso. Detect encuentra eventos a tiempo para que Respond pueda contener, analizar, notificar y frenar la expansión. Recover restaura operaciones (Pascoe et al., 2024). Se nombran juntas porque se necesitan juntas: una copia que nadie probó es Protect de mentira y Recover imposible.

El uso concreto no es “implementar las cinco”. Es un Perfil. En 1.1 se compara un Perfil actual con uno objetivo, y esa brecha prioriza la mejora teniendo en cuenta el costo (NIST, 2018, sec. 1.1). La versión 2.0 formaliza el gesto: acotar el alcance y los supuestos; juntar políticas y prácticas; armar el Perfil; analizar la brecha; seguir un plan de acción, que puede ser un registro de riesgos (Pascoe et al., 2024, sec. 3). El alcance puede ser la organización o un sistema, y un Perfil de comunidad puede servir de base al objetivo. No es un certificado. Es decir qué resultados se logran y cuáles se eligieron como siguiente paso.

Los Tiers —Partial, Risk Informed, Repeatable, Adaptive— no son la nota del Perfil. Caracterizan el rigor de la gestión, y la versión 2.0 dice que subir de Tier se justifica cuando el riesgo o un mandato lo exigen, o cuando un análisis costo-beneficio muestra una reducción factible (Pascoe et al., 2024, sec. 3.2). Subir a Adaptive para la lámina es usar el marco como puntuación. Un control cuyo costo supera la pérdida anual evitada no justifica un Tier más alto. El marco de 2018 ya pedía factorizar el costo al priorizar el camino del Perfil actual al objetivo (NIST, 2018).

## Tensión

Hay dos formas de fracasar que se parecen a usar el marco.
La primera es tratar las cinco funciones como una secuencia de compra: inventario, firewall, SIEM, retainer, backup. El documento dice que se trabajan al mismo tiempo: gobernar, identificar, proteger y detectar ocurren de continuo, y responder y recuperar tienen que estar listas antes del incidente (Pascoe et al., 2024). Una organización que “está en Detect” no usa el CSF. Narra un proyecto.

La segunda es el Perfil objetivo que marca todas las subcategorías como prioridad. Eso es la checklist que el propio Core advierte que no es. Elegir resultados, y dejar otros fuera porque el riesgo no los paga, es el uso. Marcar todo es no haber priorizado, que es lo único para lo que el idioma sirve.

El límite que más importa fuera de Estados Unidos es legal. El CSF es voluntario y neutro de país: no sustituye una obligación. En Argentina, el artículo 9 de la Ley 25.326 impone al responsable del archivo medidas técnicas y organizativas, y prohíbe registrar datos personales en archivos sin condiciones de integridad y seguridad (Ley 25.326, 2000). Un Perfil no cumple ese artículo. Puede ordenar la conversación. No reemplaza la ley ni las medidas de la autoridad de aplicación. Usarlo como si “estar en el CSF” fuera cumplimiento es marketing.

El otro límite es de método. Las cinco funciones no dicen cuál brecha cerrar primero: dicen en qué idioma describirla. Sin una estimación de impacto y de frecuencia —aunque el ARO sea un supuesto y no una medición— el Perfil objetivo se llena con lo que asusta, no con lo que cuesta. El marco de 2018 ya pedía probabilidad e impacto para fijar la tolerancia y priorizar el gasto (NIST, 2018, sec. 1.2). Quien se queda en los cinco verbos recitó el marco y no lo usó.

## Cierre

Las cinco funciones sirven como idioma, no como plan. Se usan cuando una organización puede decir qué resultados logra, cuáles eligió como objetivo, y en qué orden cierra la diferencia, porque el riesgo y el costo lo justifican —no porque la rueda se lea de izquierda a derecha. La versión 2.0 no tiró esas cinco: les puso Govern en el centro para que dejen de usarse como lista de herramientas. El uso correcto cabe en una frase sin nombre de producto: este es el Perfil actual, este es el objetivo, esta brecha se cierra primero porque la pérdida anual evitada supera el costo, y estas otras se aceptan o se transfieren porque un control propio no se paga.

## Reflexión

En el escenario del laboratorio, recitar las cinco funciones no decide nada. Decirle a PhantomCorp que “tiene que proteger y recuperarse” es la lámina. El uso es el otro: el Perfil actual falla en la copia de respaldo y en la autenticación del acceso remoto; el objetivo no es “subir de Tier”; el plan de acción pone primero el control cuyo ROI es positivo y no compra el que es negativo. Las funciones nombran el hueco. El ALE dice cuál hueco se paga. Sin las dos cosas, o se mitiga todo o se mitiga lo que da miedo.

## Bibliografía

1. [PRIMARIA] Ley 25.326. (2000). *Protección de los datos personales*. Honorable Congreso de la Nación Argentina. Artículo 9. http://servicios.infoleg.gob.ar/infolegInternet/anexos/60000-64999/64790/texact.htm
2. [PRIMARIA] National Institute of Standards and Technology. (2018, 16 de abril). *Framework for improving critical infrastructure cybersecurity, version 1.1* (NIST CSWP 04162018). https://doi.org/10.6028/NIST.CSWP.04162018
3. [PRIMARIA] Pascoe, C., Quinn, S. y Scarfone, K. (2024, 26 de febrero). *The NIST Cybersecurity Framework (CSF) 2.0* (NIST CSWP 29). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.CSWP.29

Las tres fuentes se abrieron en el documento original (el texto actualizado de la ley en Infoleg, y los PDF de NIST CSWP 04162018 y NIST CSWP 29) antes de citarlas. No se usó un resumen de terceros como fuente.
