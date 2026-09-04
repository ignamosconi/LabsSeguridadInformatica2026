# Informe — Laboratorio 03 · Autenticación

**Grupo:** 05 · **Caso asignado:** 05 mod 4 = **1 → RockYou 2009**

**Integrantes:**

| Nombre y apellido | Legajo | Usuario de GitHub |
|---|---|---|
| Magni, Gastón | 14991 | @nosungam |
| Mosconi, Ignacio | 15288 | @ignamosconi |
| Presuttari, Matías | 14959 | @matiaspresuttari |
| Terreno, Valentino | 15079 | @vterreno |

**Entorno de las mediciones:** Intel Core i7-1165G7 (8 hilos), Python 3.12.3,
OpenSSL 3.0.13, Linux. Todas las cifras marcadas *medido* se reprodujeron en esta
máquina; las marcadas *publicado* salen de las fuentes citadas en § 1.6.

---

## 0. Declaración de uso de IA

Se usó **Claude Opus 5** (Claude Code) como asistente, y se declara el alcance:

| Qué | Cómo se usó | Verificación |
|---|---|---|
| `hash_password`, `verify_password`, `totp` | Implementadas con asistencia de la IA a partir de las pistas del esqueleto | Contrastadas contra los vectores oficiales de RFC 6238 / RFC 4226 con `src/pruebas.py` (40 chequeos, todos en verde) |
| Búsqueda de fuentes de la Parte A | La IA buscó y trajo las fuentes; se leyeron y se citan con URL y fecha | Las cifras de § 1 salen del white paper original de Imperva y del comunicado de la FTC, no de resúmenes de terceros |
| Redacción del informe y del mini-research | Borrador asistido, revisado y corregido por el grupo | — |
| Mediciones (§ 2.2, § 2.3) y benchmarks | **Ejecutadas localmente**, no generadas por la IA | Reproducibles con los comandos de § 4 |

Lo que **no** se delegó: la elección de parámetros, la lectura de los RFC y la
interpretación de los resultados. Ningún número de este informe fue tomado de la
memoria del modelo: o está medido, o está citado.

---

## 1. Parte A — RockYou 2009

### 1.1 Qué pasó

RockYou vendía widgets y aplicaciones sociales para MySpace y Facebook: álbumes,
tarjetas, juegos. Nada crítico — y ese es justamente el punto.

| Fecha | Hecho |
|---|---|
| ~4 dic 2009 | Un atacante con el alias **"igigi"** explota una **inyección SQL** en `rockyou.com` y se baja la base completa |
| 14 dic 2009 | TechCrunch publica el caso: **32 millones de cuentas** con las contraseñas **en texto plano**. RockYou sabía de la brecha desde días antes y no había notificado a nadie |
| 16 dic 2009 | El atacante publica la lista completa (32.603.388 registros). Se filtran las contraseñas repetidas: quedan **14.341.564 únicas** → nace **`rockyou.txt`** |
| ene 2010 | Imperva (ADC) publica *Consumer Password Worst Practices*: el primer análisis estadístico de 32 M de contraseñas **reales** de usuarios |
| 27 mar 2012 | La **FTC** cierra un acuerdo con RockYou: **US$ 250.000** de multa por violar COPPA (datos de ~179.000 chicos), prohibición de seguir haciendo afirmaciones engañosas sobre seguridad y **20 años de auditorías** externas de su programa de seguridad |
| 2010–hoy | `rockyou.txt` viene **preinstalado en Kali Linux** y es el diccionario por defecto de casi toda demostración de cracking |

### 1.2 Qué se guardó mal

No hubo criptografía **de ningún tipo**. Las contraseñas estaban en la base tal
como el usuario las tecleaba. Es el piso absoluto: no es "hash débil", es
**cero hash**.

Tres agravantes que hacen el caso peor que una simple omisión técnica:

1. **Guardaba credenciales de terceros, también en claro.** Para que la app
   "invitara a tus amigos", RockYou pedía las credenciales del **webmail** y de
   MySpace/Facebook del usuario, y las almacenaba en la misma base sin cifrar. La
   brecha no filtró sólo contraseñas de RockYou: filtró llaves de casillas de
   correo ajenas. Imperva lo pone como consejo #3 para usuarios: *"nunca confíes
   tus contraseñas importantes a un tercero"*.
2. **La comparación era `contraseña == guardada`.** Con texto plano no hay hash
   que comparar, así que el login comparaba cadenas directamente: no sólo es
   reversible, además es la forma más burda de la falla de tiempo que atacamos en
   § 2.3.
3. **La política de contraseñas empujaba a lo peor.** El mínimo de RockYou era de
   **cinco caracteres**. Con ese piso, el 26,04% de los usuarios eligió justo
   seis y el 4,07% eligió cinco *(Imperva, distribución de longitudes)*.

Y el agravante no técnico, que la FTC terminó sancionando: RockYou **le decía a
sus usuarios que protegía sus datos** mientras los guardaba en claro. La multa no
fue por ser insegura, fue por mentir sobre serlo.

### 1.3 Cómo se explotó

**El ataque en sí fue trivial.** Una inyección SQL sobre una técnica que, como
señaló TechCrunch en su momento, *"está documentada desde hace más de una
década"*. Y una vez adentro, **el costo de explotación fue cero**: no hubo
cracking, no hubo GPU, no hubo diccionario. Las contraseñas ya eran contraseñas.
Ésa es la diferencia esencial con LinkedIn 2012 (SHA-1 sin salt) o con cualquier
brecha posterior: **no había nada que romper**.

**El daño real vino después, y es lo que hace a este caso único.** Al publicarse,
la lista dejó de ser un incidente de 32 M de personas y se convirtió en una
**pieza de infraestructura para el atacante**: la primera muestra masiva de cómo
elige contraseñas un ser humano de verdad. Lo que Imperva midió sobre esa lista
*(publicado)*:

| Hallazgo | Cifra |
|---|---|
| Contraseña más usada: `123456` | **290.731 cuentas** (0,9% del total) |
| Le siguen | `12345` (79.078), `123456789` (76.790), `password` (61.958), `iloveyou` (51.622), `princess` (35.231), `rockyou` (22.588) |
| Usuarios con contraseña de ≤ 6 caracteres | **30%** |
| Usuarios con contraseña de ≤ 7 caracteres | ~50% |
| Usuarios con un juego de caracteres limitado | ~60% (41,7% sólo minúsculas; 15,9% sólo dígitos) |
| Usuarios que usan caracteres especiales | < 4% |
| Contraseñas "fuertes" según el criterio de NASA (≥ 8 caracteres + 4 clases) | **0,2%** |
| Cobertura de las 5.000 contraseñas más populares | **20% de los usuarios** |

Y la conclusión operativa que saca el propio informe: con **1** intento por
cuenta se acierta el 0,9%; con **116** intentos, el 5%; con **683**, el 10%; con
**5.000**, el 20%. Imperva lo traduce a un ataque *online* de la época: con un
DSL de 55 KB/s de subida, 110 intentos por segundo, *"el atacante gana acceso a
una cuenta nueva por segundo, o menos de 17 minutos para comprometer 1.000
cuentas"*.

**Por qué esto cambió el juego para siempre.** El cracking de contraseñas dejó de
ser un problema de **espacio de búsqueda** y pasó a ser un problema de
**ordenamiento**. La comparación *(calculada sobre las velocidades publicadas de
hashcat en una RTX 4090)*:

| Estrategia | Candidatos | Tiempo contra SHA-1 sin salt | Cobertura esperada |
|---|---:|---:|---:|
| Fuerza bruta exhaustiva, 8 caracteres `[A-Za-z0-9]` | 218.340.105.584.896 ≈ 2⁴⁷·⁶ | 1,2 h | 100% de ese espacio |
| **`rockyou.txt`** | 14.341.564 ≈ 2²³·⁸ | **0,3 ms** | ~20–30% de usuarios reales |

`rockyou.txt` es **15 millones de veces más chico** que el espacio exhaustivo de
8 caracteres y, aun así, tumba a uno de cada cuatro usuarios. Eso es lo que
RockYou le regaló al mundo: no 32 M de contraseñas, sino la **distribución de
probabilidad** de la elección humana. Las contraseñas de 2009 caducaron; la
distribución no.

### 1.4 El efecto dominó

- **Inmediato:** como la mitad de los usuarios reusa contraseñas entre sitios
  (Imperva cita varios estudios de la época), los 32 M de pares
  email + contraseña en claro eran munición directa para **credential stuffing**
  contra webmail, MySpace y Facebook. Y las credenciales de terceros que RockYou
  guardaba en claro no requerían ni eso.
- **Permanente:** `rockyou.txt` es hoy el diccionario por defecto de John the
  Ripper, hashcat y Kali. Cada brecha posterior mal protegida se crackea, en
  primera instancia, **con la lista de RockYou**. Los 6,5 M de hashes SHA-1 sin
  salt de LinkedIn en 2012 cayeron en horas y `rockyou.txt` fue parte del
  instrumental. El daño de RockYou no fue lineal: fue un **multiplicador** para
  todas las brechas de la década siguiente.
- **Irónicamente, defensivo:** la misma lista es hoy un control. NIST SP 800-63B
  exige comparar cada contraseña nueva contra listas de contraseñas
  comprometidas, y `rockyou.txt` es la lista fundacional de ese control. La peor
  brecha de higiene de contraseñas de la historia se convirtió en la herramienta
  que la previene.

### 1.5 La forma correcta

Lo que RockYou debió hacer — y lo que implementamos en la Parte B:

1. **Nunca almacenar la contraseña en forma recuperable.** No en claro, no
   cifrada con una clave que está en el mismo servidor. Sólo la **derivada de una
   KDF de una vía**. Imperva ya lo decía en 2010 a los administradores: *"asegurate
   de que las contraseñas no se guarden en texto claro; siempre digerí la
   contraseña antes de guardarla en la base"*. NIST SP 800-63B lo pone como
   requisito normativo: los verificadores **SHALL** guardar el secreto "en una
   forma resistente a ataques offline", salteado y con una KDF, con **salt de al
   menos 32 bits** y un conteo de iteraciones "tan grande como permita el
   rendimiento del servidor".
2. **KDF lenta con salt por usuario.** Hoy OWASP recomienda **Argon2id**
   (m=19 MiB, t=2, p=1 mínimo); bajo FIPS-140, **PBKDF2-HMAC-SHA256 con 600.000
   iteraciones**. Es lo del § 2.
3. **Guardar los parámetros junto al hash** para poder subir el costo sin
   invalidar a nadie (rehash en el próximo login exitoso).
4. **Comparar en tiempo constante** (§ 2.3).
5. **Rechazar la contraseña débil en el alta, no después de la brecha.** Éste es
   *el* control que le faltaba a RockYou: con un mínimo de 5 caracteres y sin
   lista de bloqueo, el 20% de sus cuentas era abrible con 5.000 intentos. Hoy:
   mínimo de 8, sin tope bajo de longitud, y contraste contra listas de
   contraseñas filtradas (NIST SP 800-63B § 5.1.1.2).
6. **Anti-fuerza bruta en el login**: rate limiting, CAPTCHA, bloqueo progresivo.
   Los "17 minutos para 1.000 cuentas" de Imperva son un ataque **online**, y
   ningún hash del mundo lo frena: se frena en la capa de la aplicación. (Dato
   lateral interesante del § 2.2: una KDF costosa **también** limita el ataque
   online, porque el servidor no puede validar más de ~23 intentos por segundo
   por core.)
7. **No pedir ni almacenar credenciales de terceros.** Para eso existe la
   delegación por **OAuth**: la app recibe un token revocable y de alcance
   limitado, y nunca ve la contraseña del usuario. En 2009 era una práctica
   común; hoy es indefendible.
8. **Consultas parametrizadas** para cerrar la SQLi que abrió la puerta, y un
   proceso de notificación que no dependa de que el atacante publique los datos.

### 1.6 Fuentes

1. Imperva Application Defense Center — *Consumer Password Worst Practices* (white paper), enero 2010. https://www.imperva.com/docs/gated/WP_Consumer_Password_Worst_Practices.pdf — **fuente primaria** de todas las estadísticas de § 1.3: top-20 con conteos absolutos, distribución de longitudes, 0,2% de contraseñas fuertes, cobertura del top-5000, y las recomendaciones citadas.
2. Cluley, G. / TechCrunch — *RockYou Hack: From Bad To Worse*, 14/12/2009. https://techcrunch.com/2009/12/14/rockyou-hack-security-myspace-facebook-passwords/ — (32 M de cuentas en texto plano; credenciales de MySpace y webmail de terceros también en claro; SQLi "documentada desde hace más de una década"; RockYou no notificó).
3. Federal Trade Commission — *FTC Charges That Security Flaws in RockYou Game Site Exposed 32 Million Email Addresses and Passwords*, 27/03/2012. https://www.ftc.gov/news-events/news/press-releases/2012/03/ftc-charges-security-flaws-rockyou-game-site-exposed-32-million-email-addresses-passwords — (multa de US$ 250.000 por COPPA, ~179.000 menores, 20 años de auditorías, cargo por afirmaciones engañosas sobre seguridad). Expediente completo: https://www.ftc.gov/legal-library/browse/cases-proceedings/1023120-rockyou-inc
4. The Register — *RockYou hack reveals appalling password practices*, 17/12/2009. https://www.theregister.com/2009/12/17/rockyou_security_snafu/ — (publicación de la lista completa y reacción de la industria).
5. NIST — *SP 800-63B, Digital Identity Guidelines: Authentication and Lifecycle Management*, § 5.1.1.2. https://pages.nist.gov/800-63-3/sp800-63b.html — (KDF obligatoria, salt ≥ 32 bits, iteraciones, y contraste contra listas de contraseñas comprometidas).
6. OWASP — *Password Storage Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html — (Argon2id m=19456/t=2/p=1; PBKDF2-HMAC-SHA256 600.000; bcrypt wf ≥ 10; pepper).
7. Chick3nman — *Hashcat v6.2.6 benchmark on the NVIDIA RTX 4090*. https://gist.github.com/Chick3nman/32e662a5bb63bc4f51b847bb422222fd — (SHA-1: 50.638,7 MH/s; PBKDF2-HMAC-SHA256: 8.865,7 kH/s; bcrypt: 184,0 kH/s) — base de los cálculos de § 1.3 y § 2.2.
8. Krebs, B. — *As Scope of 2012 Breach Expands, LinkedIn to Again Reset Passwords for Some Users*, KrebsOnSecurity, 18/05/2016. https://krebsonsecurity.com/2016/05/as-scope-of-2012-breach-expands-linkedin-to-again-reset-passwords-for-some-users/ — usada sólo para el contraste del § 1.4 (LinkedIn: 117 M de hashes SHA-1 sin salt).

---

## 2. Parte B.1 — Contraseñas

Implementado en [`src/auth.py`](src/auth.py). Formato del registro:

```
pbkdf2_sha256$200000$4f9a...b1$0dae...24
   algoritmo  iters   salt (16 B)  derivada (32 B)
```

```
$ python3 src/auth.py hash --password 'Phantom-2026!'
pbkdf2_sha256$200000$c06781c52210fe790f40ce502ced9e49$9230aa23b451171b3d8a359c16c08550802a0161744320bbc17e73ae8e2676a1
$ python3 src/auth.py verify --password 'Phantom-2026!' --registro 'pbkdf2_sha256$200000$c06781c52210fe790f40ce502ced9e49$9230aa23b451171b3d8a359c16c08550802a0161744320bbc17e73ae8e2676a1'
OK
$ python3 src/auth.py verify --password 'Phantom-2027!' --registro 'pbkdf2_sha256$200000$c06781...'
FALLO     # exit code 1
```

Decisiones de diseño:

- **Salt de 16 bytes** de `secrets.token_bytes` (CSPRNG del sistema, no `random`).
  128 bits, muy por encima de los 32 bits que exige NIST.
- **Los parámetros viajan en el registro.** `verify_password` relee iteraciones y
  salt desde ahí en vez de asumir los suyos: cuando haya que subir el costo, los
  registros viejos siguen validando y se pueden rehashear al vuelo.
- **Registro corrupto o ajeno → `False`**, nunca una excepción: un `500` en el
  login también es información para el atacante.

Frente a la Parte A conviene decir lo obvio: **RockYou no falló en esto, falló
antes**. No eligió mal el algoritmo, no eligió ninguno. Lo que sigue es el
escalón que nunca subió — y la razón por la que subirlo a medias (hashear sin
salt, o con un hash rápido) sigue siendo insuficiente **precisamente por culpa de
`rockyou.txt`**.

### 2.1 ¿Por qué salt **por usuario**?

Porque sin salt, `hash(contraseña)` es una **función global**, y eso rompe tres
cosas a la vez. Con dos usuarios que eligieron la misma contraseña se ve al toque
*(medido)*:

```
sin salt (sha256 pelado):  8d969eef6ecad3c29a3a6292  ==  8d969eef6ecad3c29a3a6292   → True
con salt por usuario:      97e57a0ef7ae155571e0af4d  vs  dc812e6f28297850a319d2d5   → False
```

1. **Filtra información sin crackear nada.** Con la columna sin salt, el atacante
   agrupa hashes iguales y ya sabe qué cuentas comparten contraseña — y cuál es la
   más popular, que es la primera que conviene atacar. Sobre una base tipo
   RockYou eso significa ubicar de una las **290.731 cuentas con `123456`** sin
   invertir un solo ciclo de CPU: el histograma se ve directo en la tabla.
2. **Habilita la precomputación.** Una rainbow table se calcula una vez y sirve
   contra todas las víctimas de todos los sitios. Con 128 bits de salt, el
   atacante tendría que almacenar o computar 2¹²⁸ valores más **por contraseña**:
   deja de existir como ataque.
3. **Habilita el ataque por lotes**, que es el que multiplica el daño: un
   candidato hasheado se prueba contra **todos** los hashes de la base de una sola
   vez (una búsqueda en un set ordenado, costo despreciable). Con salt único, el
   atacante tiene que **repetir todo el trabajo por cada usuario**. Con las
   velocidades del § 1.3: pasar `rockyou.txt` contra las 32,6 M de cuentas sin
   salt son **0,3 ms**; con salt y PBKDF2 a 200.000 iteraciones son **334 años**
   de esa misma GPU.

El salt **no es secreto** y no necesita serlo: no protege la contraseña, destruye
la economía de escala del atacante.

### 2.2 ¿Por qué **muchas** iteraciones?

Porque el defensor paga el costo **una vez por login** y el atacante lo paga
**una vez por candidato**. Las iteraciones son la única palanca que mueve esa
asimetría a nuestro favor. *Medido en esta máquina:*

| | Costo por operación | Intentos/s por core |
|---|---:|---:|
| `sha256` pelado (1 pasada) | 0,6 µs | 1.760.676 |
| PBKDF2-SHA256, 1 iteración | 2,2 µs | ~455.000 |
| **PBKDF2-SHA256, 200.000 iteraciones** | **43,1 ms** | **23,2** |
| PBKDF2-SHA256, 600.000 iteraciones (OWASP) | 129,3 ms | 7,7 |

200.000 iteraciones encarecen cada intento **~78.000 veces** respecto de un
`sha256` pelado, y al defensor le cuestan 43 ms: imperceptible en un login,
letal en un diccionario.

Puesto sobre las cifras de Imperva, que son de usuarios reales y no de
contraseñas hipotéticas — costo en GPU (44.328 h/s) de atacar **una** cuenta con
las contraseñas más populares:

| Objetivo del atacante | Intentos por cuenta | Con SHA-1 sin salt | Con PBKDF2-200k y salt |
|---|---:|---:|---:|
| 0,9% de las cuentas | 1 | instantáneo | 0,02 ms |
| 5% de las cuentas | 116 | instantáneo | 2,6 ms |
| 10% de las cuentas | 683 | instantáneo | 15 ms |
| 20% de las cuentas | 5.000 | instantáneo | 113 ms |
| `rockyou.txt` completo | 14.341.564 | 0,3 ms | **5,4 min** |

Y acá está la lección incómoda, que preferimos decir explícitamente antes de que
la rúbrica nos la marque: **contra `123456`, PBKDF2 no sirve para nada**. 113 ms
para el 20% de las cuentas es gratis para cualquier atacante. Las iteraciones
multiplican el costo de recorrer un espacio; si la contraseña está en el primer
puñado de candidatos, no hay espacio que recorrer. **Las iteraciones compran
tiempo, no impunidad**: son necesarias, y son inútiles sin política de
contraseñas, lista de bloqueo y segundo factor. El caso RockYou es la
demostración empírica de que el eslabón débil está del lado del usuario, y por
eso el § 1.5 pone el punto 5 al mismo nivel que el 2.

Un efecto secundario que sí ayuda contra el ataque **online** de Imperva: con
43 ms por verificación, el servidor no puede procesar más de **23,2 intentos de
login por segundo por core**. Los 110 intentos/s que asumía Imperva con un DSL de
2009 ya no entran: la KDF actúa de freno natural. No reemplaza al rate limiting
— es CPU nuestra la que se consume — pero cambia la aritmética del atacante.

Dos advertencias más que salen de medir y no de suponer:

- **El esqueleto usa 200.000 y OWASP hoy pide 600.000** para PBKDF2-HMAC-SHA256.
  Dejamos el default del enunciado para no cambiar la firma, pero en producción
  iríamos a 600.000 (129 ms medidos, todavía aceptable) o directamente a
  **Argon2id**, que es memory-hard y le saca a la GPU su ventaja (ver
  [`research.md`](research.md)).
- Las iteraciones son también un vector de **DoS**: 129 ms de CPU por intento de
  login es algo que hay que combinar con rate limiting, no algo que se sube sin
  medir.

### 2.3 Verificación en tiempo constante

`verify_password` compara con `hmac.compare_digest`, que recorre **todos** los
bytes siempre. La comparación ingenua (`==` byte a byte, cortando en la primera
diferencia) tarda distinto según **cuánto del prefijo acertó el atacante**, y eso
es un oráculo: se adivina el token byte por byte, y en lugar de 256³² intentos
son 32×256. *Medido* sobre 32 bytes, mínimo de 7 bloques de 20.000 repeticiones:

| Dónde está la primera diferencia | Comparación ingenua | `hmac.compare_digest` |
|---|---:|---:|
| byte 0 | 188 ns | 46 ns |
| byte 16 | 439 ns | 47 ns |
| byte 31 | 656 ns | 47 ns |
| idénticos | 669 ns | 48 ns |

La ingenua **filtra 3,5×**; `compare_digest` es plana (dispersión ~1–13%, dentro
del ruido). En este lab el valor comparado es una derivada de PBKDF2, así que la
fuga es de bajo impacto — pero el mismo error en un MAC, un token de sesión o un
código TOTP es explotable, y escribirlo bien no cuesta nada. Nótese que el login
de RockYou, al comparar texto plano contra texto plano, tenía **esta misma falla
además** de la principal: la fuga de tiempo revelaba el prefijo de la contraseña
real, no de un hash.

