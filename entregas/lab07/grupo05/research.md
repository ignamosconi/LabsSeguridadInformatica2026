# Mini-research — Laboratorio 07

**Tema elegido:**

Elegimos el tema A:

- [x] **A.** Consultas parametrizadas / prepared statements: cómo separan datos de
  código y por qué eliminan la SQLi de raíz (con ejemplo en un lenguaje).
- [ ] **B.** sqlmap por dentro: cómo detecta la inyección (boolean-based,
  time-based, error-based) y qué significa cada técnica.
- [ ] **C.** Un caso real de RCE por command injection (CVE a elección): vector,
  impacto y parche.
- [ ] **D.** Broken Access Control (OWASP A01): IDOR vs. otras fallas de control
  de acceso, y el principio de "denegar por defecto".

## Desarrollo

### El problema de fondo: un único string con dos lenguajes mezclados

Cuando una aplicación arma SQL concatenando strings, el motor de base de datos
recibe **un solo texto** que tiene que interpretar íntegramente como código SQL.
No hay forma de que el motor distinga, dentro de ese texto, qué parte puso el
programador (la estructura de la consulta) y qué parte puso el usuario (el
valor). Si el valor del usuario contiene caracteres con significado especial en
SQL (`'`, `--`, `;`, `UNION`), el motor los interpreta como código, exactamente
como pasó en el R1 y el R2 de este lab: el `--` del payload no es "un dato
raro", es un comentario SQL válido que el parser ejecuta.

### Qué hace distinto una consulta parametrizada

Una consulta parametrizada separa ese proceso en dos pasos, a nivel del
protocolo entre la aplicación y la base de datos:

1. **Preparación (`prepare`):** la aplicación envía solamente la *forma* de la
   consulta, con placeholders (`?` en SQLite/MySQL con algunos drivers, `%s`
   en psycopg2, `:nombre` en Oracle) en lugar de los valores:
   ```sql
   SELECT user, rol FROM users WHERE user = ? AND pass = ?
   ```
   El motor **compila y fija el plan de ejecución de esa estructura** antes de
   conocer ningún valor concreto. Esto ya cierra la puerta: no hay ningún punto
   posterior en el que un valor pueda "reescribir" la consulta, porque la
   consulta ya quedó decidida.
2. **Ejecución (`execute`) con los valores separados:** la aplicación manda los
   valores (`"admin' -- "`, `"x"`) por un canal de datos distinto, no como texto
   que vuelve a pasar por el parser SQL. El motor los toma como **literales
   opacos** del tipo que corresponda (string, entero, etc.) y los asigna
   directamente a los placeholders ya compilados.

El punto clave: el contenido del valor es irrelevante para la estructura de la
consulta. Una comilla, un `--`, un `UNION SELECT` dentro del valor de `user`
sigue siendo, para el motor, *el contenido del campo* `user` — nunca vuelve a
convertirse en sintaxis SQL. Por eso la inyección no se "dificulta", **se
vuelve imposible por diseño** en ese punto de entrada.

### Ejemplo concreto (Python + sqlite3)

**Vulnerable** (lo que tiene el servidor de este lab, por diseño pedagógico):

```python
query = f"SELECT user, rol FROM users WHERE user='{user}' AND pass='{pwd}'"
cursor.execute(query)
```

Con `user = "admin' -- "`, el string que llega al motor es:

```sql
SELECT user, rol FROM users WHERE user='admin' -- ' AND pass='...'
```

**Con prepared statement:**

```python
query = "SELECT user, rol FROM users WHERE user = ? AND pass = ?"
cursor.execute(query, (user, pwd))
```

Con el mismo `user = "admin' -- "`, el driver manda la estructura fija y el
valor por separado. El motor busca, literalmente, un registro cuyo campo
`user` sea exactamente el string `admin' -- ` (16 caracteres, comilla y guiones
incluidos). Como ningún usuario se llama así, la consulta no devuelve filas: el
bypass deja de funcionar, sin haber agregado ningún `if` de validación ni
ninguna función de escape.

### Por qué "escapar comillas" no es lo mismo (y por qué falla)

Escapar comillas (reemplazar `'` por `\'` o `''`) sigue construyendo **un solo
string** que el motor vuelve a parsear como SQL. Es una lista negra de
caracteres peligrosos, y las listas negras son, por naturaleza, incompletas:
dependen de que el desarrollador haya pensado en *todos* los caracteres y
codificaciones peligrosas del motor específico (comillas Unicode, encoding
multibyte en ciertos charsets, variantes del comentario). La historia de la
seguridad web está llena de bypasses de funciones de escape "custom". La
parametrización no compite en esa carrera: no depende de anticipar caracteres
peligrosos porque el valor nunca vuelve a ser código.

