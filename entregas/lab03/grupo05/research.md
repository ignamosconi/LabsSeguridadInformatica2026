# Mini-research — Laboratorio 03 · Grupo 05

**Tema elegido:**
- [x] **A.** PBKDF2 vs bcrypt vs scrypt vs Argon2: por qué existen "hashes lentos".
- [ ] **B.** TOTP vs FIDO2/WebAuthn.
- [ ] **C.** Autenticación vs autorización; RBAC y ABAC.
- [ ] **D.** Ataques de timing reales y cómo se mitigan.

---

## Desarrollo

### 1. El problema: el hash rápido es un requisito invertido

Toda función de hash criptográfica se diseña para ser **rápida**: hay que
digerir gigabytes y verificar firmas al vuelo. Para contraseñas, ese objetivo
está **exactamente al revés**.

La razón es una asimetría de conteo. El servidor evalúa la función **una vez por
login**; el atacante que se robó la base la evalúa **una vez por candidato**, y
tiene miles de millones de candidatos. Cualquier ahorro por evaluación se
multiplica del lado equivocado. Ese es todo el argumento de los "hashes lentos"
(mejor: **funciones de derivación de clave**, KDF): elegir un costo por
evaluación tan alto como el defensor pueda tolerar, para que el atacante lo pague
multiplicado por su espacio de búsqueda.

Hay un segundo problema, más sutil, y es el que ordena la historia de estos
cuatro algoritmos: **el atacante no usa el mismo hardware que el defensor**. El
servidor corre en CPU de propósito general; el atacante corre en GPU (miles de
núcleos), FPGA o ASIC. Si la función sólo cuesta *cómputo*, el atacante compra
paralelismo y la ventaja se evapora. Por eso la evolución no fue "más
iteraciones", sino **hacer que el costo sea difícil de paralelizar**.

### 2. Los cuatro, en orden histórico

| | Año | Estándar | Palancas de costo | Memoria requerida | Resistencia a GPU/ASIC |
|---|---|---|---|---|---|
| **PBKDF2** | 2000 | RFC 2898 → **RFC 8018**; NIST SP 800-132 | iteraciones | **~nada** (unos cientos de bytes) | ❌ baja |
| **bcrypt** | 1999 | *de facto* (Provos & Mazières, USENIX) | *cost factor* (log₂ de iteraciones) | fija, **4 KiB** | ⚠️ media |
| **scrypt** | 2009 | **RFC 7914** | N (memoria/tiempo), r, p | **configurable**, decenas–cientos de MiB | ✅ alta |
| **Argon2** | 2015 | **RFC 9106**; ganador del PHC | m (memoria), t (tiempo), p (paralelismo) | **configurable e independiente** | ✅ alta |

**PBKDF2** (Kaliski, RSA Labs) es el más simple: aplicar HMAC *c* veces en cadena.
Es el que usamos en el lab. Su única palanca es el conteo de iteraciones y su
huella de memoria es prácticamente nula — justo lo que necesita una GPU para
correr decenas de miles de instancias en paralelo. Sobrevive por una razón
burocrática y no criptográfica: es el único de los cuatro **aprobado por FIPS-140**,
así que en entornos regulados suele ser obligatorio.

**bcrypt** (Provos & Mazières, 1999 — anterior a PBKDF2) fue el primero en
plantear el problema en estos términos: su paper se llama *"A Future-Adaptable
Password Scheme"*, y la idea central es que el costo debe poder **subirse con el
tiempo** sin cambiar de algoritmo. Usa el *key schedule* deliberadamente caro de
Blowfish, que mantiene ~4 KiB de estado con accesos pseudoaleatorios. Esos 4 KiB
son poca memoria en términos absolutos, pero **no caben cómodamente en la caché
por núcleo de una GPU**, así que bcrypt resiste bastante mejor que PBKDF2. Se ve
en los benchmarks: la misma GPU hace 50.638 MH/s de SHA-1 y sólo **184 kH/s** de
bcrypt. Sus problemas son de ingeniería, no de diseño: **límite de 72 bytes** de
entrada (silenciosamente truncado en la mayoría de las implementaciones) y
truncamiento en el primer byte nulo, lo que rompe el pre-hasheo ingenuo.

**scrypt** (Percival, 2009) formalizó el concepto de **función secuencialmente
memory-hard**: llena un buffer grande con datos pseudoaleatorios y después lo lee
en posiciones que dependen de los propios datos. No se puede cambiar memoria por
cómputo (*time-memory trade-off*) sin penalización cuadrática, así que el atacante
está **obligado** a poner la RAM. Y la RAM es lo que hace caro un ASIC: los
transistores de cómputo son baratos, los megabytes no.

**Argon2** (Biryukov, Dinu y Khovratovich, 2015) ganó la **Password Hashing
Competition** y es el estado del arte (RFC 9106). Su aporte principal sobre scrypt
es **separar las tres palancas** — memoria (m), tiempo (t) y paralelismo (p) —
para poder afinarlas de forma independiente, y ofrecer tres variantes según la
amenaza:

- **Argon2d**: accesos dependientes de los datos. Máxima resistencia a GPU, pero
  el patrón de acceso a memoria filtra información por **canal lateral** (útil en
  proof-of-work, donde no hay secreto que filtrar).
- **Argon2i**: accesos independientes de los datos. Resistente a canal lateral,
  algo más débil ante trade-offs de memoria.
- **Argon2id**: híbrido — la primera pasada es tipo *i*, el resto tipo *d*. Es el
  **default recomendado** por el RFC y por OWASP: cubre las dos amenazas.

### 3. Lo que se mide, no lo que se supone

Costo del **defensor**, medido en esta máquina (i7-1165G7, Python 3.12,
OpenSSL 3.0.13; `scrypt` viene en `hashlib`, así que se puede medir sin instalar nada):

| Configuración | Tiempo por hash | Memoria |
|---|---:|---:|
| `sha256` pelado (el escalón que RockYou 2009 ni siquiera pisó) | 0,0006 ms | ~0 |
| PBKDF2-SHA256, 200.000 iters (este lab) | 43,4 ms | ~0 |
| PBKDF2-SHA256, 600.000 iters (mínimo OWASP) | 129,9 ms | ~0 |
| scrypt N=2¹⁴, r=8, p=1 | 28,1 ms | 16 MiB |
| scrypt N=2¹⁶, r=8, p=2 | 254,8 ms | 64 MiB |
| scrypt N=2¹⁷, r=8, p=1 (mínimo OWASP) | 282,4 ms | **128 MiB** |

El renglón clave es el último comparado con el segundo: **scrypt con los
parámetros de OWASP le cuesta al defensor 2× lo que PBKDF2-600k, pero le exige al
atacante 128 MiB por intento paralelo**. Una GPU de 24 GB de VRAM no puede correr
más de ~190 instancias simultáneas de eso, contra las decenas de miles que corre
de PBKDF2. Ahí está la diferencia real, y no aparece en la columna de tiempo:
aparece en la de memoria.

Costo del **atacante**, publicado (hashcat 6.2.6, una RTX 4090):

| Algoritmo | Velocidad | vs SHA-1 |
|---|---:|---:|
| SHA-1 (sin salt) | 50.638,7 MH/s | 1× |
| SHA2-256 | 21.975,5 MH/s | 0,4× |
| PBKDF2-HMAC-SHA256 (~1.000 iters) | 8.865,7 kH/s | 1/5.700 |
| PBKDF2-HMAC-SHA256, 200.000 iters (escalado) | ~44,3 kH/s | 1/1.140.000 |
| bcrypt (*cost* 5, el default del benchmark) | 184,0 kH/s | 1/275.000 |

Detalle importante para leer la tabla: bcrypt aparece "más rápido" que PBKDF2-200k,
pero está medido con *cost* 5 (32 iteraciones) mientras OWASP pide ≥ 10 (1.024
iteraciones): con el parámetro recomendado, bcrypt baja ~32× a ~5,7 kH/s. **Nunca
se comparan KDFs sin decir con qué parámetros**, y ése es el error más común en
las comparaciones de blog.

### 4. Qué elegir, y qué implica para este lab

Jerarquía práctica (OWASP *Password Storage Cheat Sheet*):

1. **Argon2id** — m=19 MiB, t=2, p=1 como mínimo. Default para todo lo nuevo.
2. **scrypt** — N=2¹⁷, r=8, p=1, si no hay una implementación de Argon2 confiable
   (en Python está en la stdlib, lo que la vuelve muy razonable).
3. **bcrypt** — sólo sistemas heredados; *work factor* ≥ 10 y cuidado con los 72 bytes.
4. **PBKDF2-HMAC-SHA256, 600.000 iteraciones** — cuando FIPS-140 lo obliga.

Nuestra implementación del lab está en el escalón 4 y con **200.000** iteraciones,
un tercio del mínimo actual de OWASP: es lo que pide el enunciado (stdlib y
`pbkdf2_hmac`), y es defendible como ejercicio, pero **no es lo que pondríamos en
producción**. Dos cosas nos dejan bien parados para migrar, y son decisiones de
diseño que tomamos en `auth.py`, no accidentes:

- El registro **lleva su algoritmo y sus parámetros adentro**
  (`pbkdf2_sha256$200000$...`), así que se puede convivir con `argon2id$...` y
  rehashear a cada usuario en su próximo login exitoso sin obligar a nadie a
  resetear la contraseña.
- `verify_password` **relee las iteraciones del registro** en vez de asumir su
  default: subir el costo no invalida ni un solo registro viejo.

Y el corolario incómodo, que conviene decir en voz alta y que la Parte A del
informe demuestra con datos: **ninguno de los cuatro salva una contraseña de seis
caracteres**. El 30% de los usuarios de RockYou tenía justamente eso, y el 20%
de las cuentas era alcanzable con 5.000 intentos: contra `123456`, Argon2id con
128 MiB no vale más que `sha1()`. Los hashes lentos suben el **piso** — encarecen
*recorrer* un espacio de búsqueda. Si la contraseña está entre los primeros
candidatos del diccionario, no hay espacio que recorrer. El resto lo ponen la
entropía de la contraseña, la lista de bloqueo y el **segundo factor**.

---

## Fuentes

1. Provos, N. y Mazières, D. — *A Future-Adaptable Password Scheme*, USENIX Annual Technical Conference, 1999. https://www.usenix.org/legacy/events/usenix99/provos.html
2. Percival, C. — *Stronger Key Derivation via Sequential Memory-Hard Functions*, BSDCan 2009. https://www.tarsnap.com/scrypt/scrypt.pdf — y su estandarización en **RFC 7914** (2016), https://www.rfc-editor.org/rfc/rfc7914
3. Biryukov, A., Dinu, D. y Khovratovich, D. — **RFC 9106**: *Argon2 Memory-Hard Function for Password Hashing and Proof-of-Work Applications*, IETF, septiembre 2021. https://www.rfc-editor.org/rfc/rfc9106 — (variantes d/i/id; Argon2id como default recomendado).
4. Moriarty, K. (ed.), Kaliski, B. y Rusch, A. — **RFC 8018**: *PKCS #5: Password-Based Cryptography Specification Version 2.1*, IETF, 2017. https://www.rfc-editor.org/rfc/rfc8018 — (definición de PBKDF2; obsoleta la RFC 2898).
5. OWASP — *Password Storage Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html — (parámetros mínimos de Argon2id, scrypt, bcrypt y PBKDF2; jerarquía de elección).
6. NIST — *SP 800-63B, Digital Identity Guidelines*, § 5.1.1.2. https://pages.nist.gov/800-63-3/sp800-63b.html — (salt ≥ 32 bits; iteraciones "tan grandes como permita el servidor"; salt secreto adicional).
7. Chick3nman — *Hashcat v6.2.6 benchmark on the NVIDIA RTX 4090*. https://gist.github.com/Chick3nman/32e662a5bb63bc4f51b847bb422222fd — (velocidades de SHA-1, SHA2-256, bcrypt y PBKDF2-HMAC-SHA256).
8. Password Hashing Competition — sitio oficial y resultados, 2013–2015. https://www.password-hashing.net/

## Reflexión

Lo que nos cambió la cabeza en este tema no fue la lista de algoritmos: fue
entender que **el parámetro importa más que el nombre**. "Usamos bcrypt" no dice
nada si el *cost* es 5; "usamos PBKDF2" tampoco si son 1.000 iteraciones. Las
comparaciones que circulan en blogs casi siempre omiten los parámetros con los
que midieron, y así se puede "demostrar" cualquier orden entre los cuatro. La
tabla de § 3 nos obligó a medir en serio y a aclarar cada configuración.

La segunda cosa fue el cambio de eje: de *"cuánto tarda"* a *"cuánta memoria
exige"*. Es un movimiento conceptual elegante — en vez de pelear una carrera de
velocidad contra hardware que siempre va a ser más rápido, se cambia la cancha a
un recurso que el atacante no puede paralelizar barato. Argon2 no es "PBKDF2 pero
más lento": es una respuesta a un modelo de amenaza distinto, el del atacante con
silicio dedicado.

Y la tercera, la más aplicable: **el formato del registro es parte del diseño de
seguridad**. Guardar `algoritmo$parámetros$salt$hash` en lugar de sólo el hash es
lo que permite migrar dentro de diez años sin pedirle a nadie que resetee su
contraseña: se rehashea a cada usuario cuando se autentica bien. Con ese formato,
cambiar de KDF es un `if` en el login y no un proyecto. Es la diferencia entre
poder mejorar y quedar clavado en la decisión que se tomó el primer día.
