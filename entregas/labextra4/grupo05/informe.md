# Entregable — Lab Extra 4: Cracking de contraseñas

**Grupo:** 05 · **Integrantes:**
- Magni, Gastón (nosungam)
- Mosconi, Ignacio (imosconi)
- Presuttari, Matías (mpresuttari)
- Terreno, Valentino (vterreno)

**Declaración de uso de IA:** Se utilizó asistencia de IA (Claude) para redactar
secciones del informe y generar variantes de las reglas de mangling. El código
del cracker fue implementado de forma guiada, comprendiendo cada línea antes
de incorporarla. Las contraseñas fueron crackeadas ejecutando el código localmente.

---

## 1. Tabla de resultados

| Usuario | Algoritmo | ¿Cayó? | Técnica | Contraseña | Tiempo aprox. |
|---|---|---|---|---|---|
| operador | MD5 + salt | ✓ Sí | Diccionario puro | `riverplate` | < 1 ms |
| analista | SHA-256 + salt | ✓ Sí | Diccionario puro | `matecocido` | < 1 ms |
| admin | SHA-256 + salt | ✓ Sí | Regla: lemma `phantom` + sufijo `2026` | `phantom2026` | < 1 ms |
| root | PBKDF2-200k | ✗ No cayó | — (ataque omitido por diseño) | — | — |

## 2. Medición de velocidad (P1)

Medición con 20 intentos para pbkdf2 y 100.000 para md5/sha256, en CPU de escritorio:

| Algoritmo | Intentos/segundo (nuestra máquina) | Diccionario completo (50 palabras) tardaría… |
|---|---|---|
| MD5 | ~1.200.000 | < 0,1 ms |
| SHA-256 | ~1.300.000 | < 0,1 ms |
| PBKDF2-200k | ~26 | ~2 segundos |

**Diferencia:** MD5/SHA-256 son ~50.000× más rápidos que PBKDF2-200k.

Con una GPU moderna (10⁹ intentos/s en MD5) y un diccionario de rockyou
(14 millones de palabras): MD5 cae en ~14 ms. Con PBKDF2-200k, la misma GPU
logra ~5.000 intentos/s (GPU es ~200× más rápida que CPU para pbkdf2, pero
las 200k iteraciones frenan todo): 14 millones de palabras tardarían ~47 minutos.
Con reglas de mangling que multiplican por 20, son ~16 horas. La contraseña de
root (`Tq9#vL2!xZ8-wK7&nB4`) no está en ningún diccionario → no cae nunca.

## 3. El loot

### operador (contraseña: `riverplate`)
```
Notas de operador — CONFIDENCIAL
==========================
Recuperaste esto porque la contraseña era débil.
Evidencia: FLAG{crack_diccionario_md5}
```
**Impacto:** acceso a documentación interna de operaciones. La contraseña
estaba literal en el diccionario — caída en 8 intentos.

### analista (contraseña: `matecocido`)
```
Notas de analista — CONFIDENCIAL
==========================
Recuperaste esto porque la contraseña era débil.
Evidencia: FLAG{crack_sha256_diccionario}
```
**Impacto:** acceso a datos de análisis/reportes. SHA-256 sin iteraciones
ofrece la misma resistencia que MD5 ante diccionario.

### admin (contraseña: `phantom2026`)
```
Notas de admin — CONFIDENCIAL
==========================
Recuperaste esto porque la contraseña era débil.
Evidencia: FLAG{crack_reglas_mangling}
```
**Impacto:** acceso de administrador — el peor escenario. La política
"tiene que tener números" hizo que el usuario eligiera `palabra + año`,
exactamente el patrón más previsible.

## 4. Las flags

```
  ✓  R1     MD5 + diccionario (caida instantanea)
  ✓  R2     SHA-256 + diccionario
  ✓  R3     SHA-256 + regla de mangling (no esta literal en el diccionario)

  ██████████████████████████████  3/3 (100%)
```
(Ver `evidencia/salidas/ctf_status.txt` para la captura completa.)

## 5. Preguntas P1–P5

### P1 — Intentos/segundo por algoritmo

Respondida en la sección 2. La clave: MD5 fue diseñado para integridad de
datos (verificar archivos rápido), no para contraseñas. SHA-256 también.
PBKDF2 fue diseñado específicamente para contraseñas: sus 200.000 iteraciones
son el costo que el defensor le impone al atacante en cada intento. Con una GPU
de 10⁹ intentos/s en MD5 y rockyou: cae en milisegundos. Contra PBKDF2-200k,
esa misma GPU hace ~5.000 intentos/s → el diccionario entero tarda horas.

### P2 — ¿Para qué sirve el salt si operador y analista cayeron igual?

El salt no protege contra el diccionario. Protege contra:

1. **Tablas precalculadas (rainbow tables):** sin salt, un atacante precomputa
   `md5("riverplate")` una vez y lo cruza contra millones de hashes. Con salt
   único por usuario, tiene que recomputar `md5(salt + "riverplate")` para
   cada usuario individualmente — las tablas no sirven.

2. **Ataque masivo:** sin salt, si dos usuarios tienen la misma contraseña,
   sus hashes son idénticos → romper uno rompe ambos. Con salt, dos usuarios
   con `riverplate` tienen hashes distintos → el atacante trabaja una cuenta
   a la vez.

Lo que el salt *no* bloquea es el ataque de diccionario sobre una cuenta
específica: si la contraseña está en el diccionario, la iteración la encuentra
sin importar el salt.

### P3 — La contraseña del admin cumplía la política y cayó

`phantom2026` tiene 10 caracteres, letras y números. Cayó porque sigue el
patrón `lemma + año`, que es exactamente lo que cubren las reglas de mangling.
Las políticas de complejidad ("al menos una mayúscula, un número, un símbolo")
empujan a los usuarios hacia patrones predecibles: `Phantom2026!`.

**NIST SP 800-63B** recomienda en cambio:
- **Longitud sobre complejidad:** mínimo 8, preferiblemente ≥ 15 caracteres.
- **Prohibir contraseñas conocidas** (listas de contraseñas comprometidas).
- **No imponer rotación periódica** — empuja a variaciones predecibles.
- **No exigir composición arbitraria** — aumenta patrones.
- **Usar frases de contraseña:** `mate.cocido.con.azucar` es más larga y
  más difícil de crackear que `M@t3C0c1d0`.

