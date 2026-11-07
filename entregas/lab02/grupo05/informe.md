# Informe - Laboratorio 02 · Criptografía

**Grupo:** 05 · **Integrantes:** *Gastón Magni, Ignacio Mosconi, Matías Presuttari, Valentino Terreno* · **Fecha:** 11/09/2026

## 0. Declaración de uso de IA

Se utilizó Claude (Anthropic) y Gemini Flash Extended (Google) como asistentes durante la resolución del presente laboratorio 02.

**Usos:**
- Gemini Flash (punto B.1): Se realizaron prompts que solicitaban no proporcionar directamente la respuesta, sino realizar preguntas orientadoras en función de las hipótesis de funcionamiento planteadas por el grupo de trabajo, con el objetivo de que la solución fuera encontrada y comprendida por los integrantes del grupo.
- Claude: Asistencia en la redacción y estructura de las explicaciones de Parte A y B.2.
- Claude: Revisión y verificación de la implementación de `mac_ingenuo()`, `mac_hmac()` y `verificar_mac()`.
- Claude: Consulta conceptual sobre el ataque de _length-extension_ y _timing attack_.

**Verificación:** cada explicación fue contrastada con las fuentes citadas (RFCs, papers, documentación de NIST). El código fue ejecutado localmente y los resultados verificados manualmente antes de incluirlos en el informe.


## 1. Parte A - Análisis de la falla

**Caso asignado:** WEP - Wired Equivalent Privacy (grupo 05 → 5 mod 5 = 0)

---

### A.1 - Qué prometía el sistema

WEP fue ratificado en 1999 como parte del estándar IEEE 802.11 para redes WiFi. Su promesa explícita era ofrecer una confidencialidad equivalente a la de una red cableada: el tráfico inalámbrico debía ser ilegible para cualquiera que no tuviera la clave compartida. Para lograrlo, usaba el algoritmo RC4 (un cifrado de flujo simétrico) combinado con un valor de inicialización (IV) de 24 bits, transmitido en texto claro junto a cada paquete.

**Fuente:** [Wikipedia - Wired Equivalent Privacy](https://en.wikipedia.org/wiki/Wired_Equivalent_Privacy)

---

### A.2 - El mal uso concreto

El problema no fue RC4 en sí mismo: el problema fue **cómo WEP usó RC4**.

RC4 es un cifrado de flujo que genera una secuencia pseudoaleatoria de bytes (keystream) a partir de una clave. Esa secuencia se combina con el mensaje mediante XOR para producir el cifrado. La propiedad crítica es que **la misma clave nunca debe generar el mismo keystream dos veces**: si dos mensajes se cifran con el mismo keystream, el XOR de ambos cifrados produce el XOR de los textos en claro, destruyendo la confidencialidad.

Para evitar esto, WEP combinaba la clave compartida (fija) con un IV de 24 bits que cambiaba por paquete. Sin embargo, 24 bits solo permiten 2²⁴ = 16.777.216 combinaciones distintas. En una red con tráfico moderado, ese espacio se agota en pocas horas, forzando la **reutilización de pares (IV, clave)** y, con ellos, del keystream. Adicionalmente, el IV viajaba en texto claro en la cabecera de cada trama, permitiendo a un atacante identificar exactamente qué paquetes comparten keystream.

El agravante fue que Fluhrer, Mantin y Shamir demostraron en 2001 que el algoritmo de scheduling de claves (KSA) de RC4 produce salidas estadísticamente sesgadas cuando se usan ciertos IVs "débiles" - y WEP los usaba sin filtrarlo. Eso permitió un ataque estadístico que deduce la clave compartida byte a byte acumulando paquetes pasivamente.

**Fuentes:**
- Fluhrer, Mantin & Shamir, *Weaknesses in the Key Scheduling Algorithm of RC4* - [IACR ePrint 2001/019](https://eprint.iacr.org/2001/019)
- Tews, Weinmann & Pyshkin, *Breaking 104 Bit WEP in Less Than 60 Seconds* - [IACR ePrint 2007/120](https://eprint.iacr.org/2007/120)

---

### A.3 - Propiedad rota y cómo se explotó

La propiedad rota fue la **confidencialidad**.

El ataque práctico, publicado por Tews, Weinmann y Pyshkin (2007) e implementado en **aircrack-ng**, combina dos técnicas:

1. **Captura pasiva de IVs:** el atacante escucha el tráfico WiFi y acumula tramas cifradas. Como los IVs viajan en claro, puede identificar cuántas veces se repite cada uno.
2. **Análisis estadístico del KSA:** usando los IVs débiles identificados por Fluhrer-Mantin-Shamir, se correlaciona el primer byte del keystream (observable mediante el CRC conocido de ciertas tramas) con los posibles bytes de la clave. Con suficientes muestras, la correlación estadística revela la clave completa.

Con ~40.000 paquetes capturados (acelerables mediante inyección de tráfico ARP), aircrack-ng recupera una clave WEP de 104 bits en menos de 60 segundos. El atacante solo necesita estar dentro del alcance de la señal WiFi; no requiere autenticarse ni establecer ninguna conexión.

**Fuente:** Tews, Weinmann & Pyshkin - [IACR ePrint 2007/120](https://eprint.iacr.org/2007/120)

---

### A.4 - La forma correcta

Reemplazar WEP por **WPA2 con AES-CCMP** (o WPA3 con SAE). En lugar de derivar una clave de sesión concatenando la clave maestra con un IV corto y estático, 802.11i utiliza un *4-way handshake* que genera claves de sesión frescas, únicas e independientes para cada conexión. AES en modo CCM provee tanto cifrado (confidencialidad) como autenticación de integridad (MIC de 64 bits), eliminando simultáneamente la reutilización de keystream y la falta de integridad auténtica que padecía WEP.

**Fuentes:** 
- [Wikipedia - IEEE 802.11i-2004 / WPA2](https://en.wikipedia.org/wiki/IEEE_802.11i-2004)
- [FIPS 197 - Advanced Encryption Standard](https://csrc.nist.gov/pubs/fips/197/final)


## 2. Parte B.1 - Romper el XOR

### Resultado

```
→ Clave (hex): 0x37
→ Clave (int): 55
→ Clave (char): '7'
→ Texto en claro: Memo interno PhantomCorp: la clave del wifi de invitados es
  Phantom-Guest-2026. No compartir fuera de la empresa.
```

Comando ejecutado:

```bash
python3 src/cripto.py romper --hex 7a525a58175e59435245595817675f565943585a745845470d175b5617545b5641521753525b17405e515e175352175e59415e435653584417524417675f565943585a1a70425244431a05070501191779581754585a475645435e45175142524556175352175b5617525a474552445619
```

### Por qué el cifrado clásico de clave corta no protege nada

Con una clave de 1 solo byte, el espacio de claves es exactamente 256. La función `romper_xor_1byte()` itera los 256 candidatos, descifra el texto con cada uno y puntúa el resultado por cuántos bytes pertenecen al conjunto de caracteres frecuentes en español/inglés (letras comunes + espacio). El candidato con mayor puntaje es el texto real. El ataque es de **fuerza bruta pura**, no requiere ningún conocimiento previo del contenido y termina en microsegundos.

La lección es doble:

1. **La longitud de la clave importa.** Una clave de 1 byte ofrece 8 bits de seguridad: trivialmente rompible.
2. **La aleatoriedad y unicidad de la clave importan.** Incluso con más bytes, una clave reutilizada vuelve el XOR transparente - exactamente la falla de WEP descripta en Parte A.



## 3. Parte B.2 - Autenticación de mensajes

### B.2.1 - ¿Por qué `sha256(clave || mensaje)` permite un ataque de _length-extension_?

SHA-256 usa la construcción de Merkle-Damgård: divide el mensaje en bloques, procesa cada bloque encadenando el estado interno, y publica ese estado final como el digest. El estado interno al terminar de procesar `clave || mensaje` **es** el valor del digest, y es observable para cualquiera que reciba el hash.

Eso significa que un atacante puede continuar el cómputo de SHA-256 desde ese estado, sin conocer la clave, agregando bytes arbitrarios. Antes de agregar los suyos, debe insertar el *padding* de Merkle-Damgård que SHA-256 habría aplicado al terminar el bloque original (calculable conociendo la longitud estimada de `clave || mensaje`). El resultado es un digest válido para el mensaje extendido `clave || mensaje || padding || datos_extra`.

**Ejemplo concreto:** el servidor verifica `sha256("secreta" || "monto=100")`. El atacante intercepta ese hash, calcula el padding correspondiente y produce `sha256("secreta" || "monto=100" || <padding> || "&monto=9999")` sin conocer la clave. El servidor computa exactamente la misma cadena al verificar y acepta la falsificación.

**Fuentes:**
- [Wikipedia - Length extension attack](https://en.wikipedia.org/wiki/Length_extension_attack)
- [Wikipedia - Merkle-Damgård construction](https://en.wikipedia.org/wiki/Merkle%E2%80%93Damg%C3%A5rd_construction)

---

### B.2.2 - ¿Cómo lo resuelve HMAC estructuralmente?

HMAC (RFC 2104) aplica la función de hash dos veces con dos claves derivadas distintas:

```
HMAC(K, m) = H( (K ⊕ opad) || H( (K ⊕ ipad) || m ) )
```

El hash **interno** `H((K ⊕ ipad) || m)` procesa el mensaje. Su resultado es un valor opaco de 32 bytes que se convierte en la entrada del hash **externo** junto con `K ⊕ opad`. Un atacante que intentara aplicar length-extension al hash interno obtendría un valor que no es la salida de HMAC: para usarlo necesitaría revertir o falsificar el hash externo, lo cual es computacionalmente inviable. La doble envoltura con clave rompe la linealidad de Merkle-Damgård que hace posible el ataque.

Formalmente, si H es una función de hash segura como PRF, HMAC hereda esa seguridad: existe una prueba que garantiza que HMAC-SHA256 es un PRF seguro independientemente de si SHA-256 padece length-extension. Esto lo distingue de cualquier construcción ad-hoc como la concatenación directa.

**Fuente:** Krawczyk, Bellare & Canetti, *HMAC: Keyed-Hashing for Message Authentication - Sección 2* - [RFC 2104, IETF](https://www.rfc-editor.org/rfc/rfc2104#section-2)

---

### B.2.3 - ¿Qué ataque evita la comparación en tiempo constante?

Evita el **timing attack** (ataque de canal lateral por tiempo).

Una comparación de strings convencional (`==` en Python, `strcmp` en C) termina en cuanto encuentra el primer byte diferente. Un MAC completamente incorrecto termina en el primer byte; uno que acierta los primeros 10 bytes tarda proporcionalmente más. Un atacante que puede medir estadísticamente esos tiempos puede deducir byte a byte qué prefijos del MAC esperado ya acertó, reduciendo una búsqueda de 2²⁵⁶ posibilidades a un máximo de 256 × 32 intentos.

**Ejemplo concreto:** el atacante envía MACs de la forma `00…00`, `01…00`, `02…00`, midiendo el tiempo de respuesta. Cuando el primer byte correcto produce un tiempo levemente mayor, lo fija y pasa al segundo. Con suficientes muestras por posición, reconstruye el MAC válido sin conocer la clave.

`hmac.compare_digest()` recorre siempre los dos strings completos, byte a byte, sin cortocircuitar, manteniendo el tiempo de ejecución constante independientemente de cuántos bytes coincidan.

**Fuentes:**
- [Python docs - `hmac.compare_digest`](https://docs.python.org/3/library/hmac.html#hmac.compare_digest)
- [Wikipedia - Timing attack](https://en.wikipedia.org/wiki/Timing_attack)



## 4. Bitácora

```bash
# Generar el reto
python3 data/generar_datos.py

# Verificar que el esqueleto corre
python3 src/cripto.py xor --texto hola --clave K
# salida: 2324272a

# Romper el XOR
python3 src/cripto.py romper --hex 7a525a58175e59435245595817675f565943585a745845470d175b5617545b5641521753525b17405e515e175352175e59415e435653584417524417675f565943585a1a70425244431a05070501191779581754585a475645435e45175142524556175352175b5617525a474552445619
# → Clave (hex): 0x37  |  Texto: Memo interno PhantomCorp...

# Probar MAC ingenuo
python3 src/cripto.py mac --clave secreta --msg "pago 100" --modo ingenuo
# → a8cc54c07b3acb7470c25ab9eea5234bfa2562e37298eee275e39a457004b725

# Probar MAC HMAC
python3 src/cripto.py mac --clave secreta --msg "pago 100" --modo hmac
# → 5ec4a52407221836a66e8d654d914aaa4b18bd31cf31907348bcd292677b902e
```