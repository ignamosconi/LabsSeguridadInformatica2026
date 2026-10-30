# Informe — Lab Extra SSRF (Server-Side Request Forgery)

**Grupo:** 05 · **Integrantes:** Magni, Gastón (@nosungam) · Mosconi, Ignacio
(@ignamosconi) · Presuttari, Matías (@matiaspresuttari) · Terreno, Valentino
(@vterreno)

**Declaración de uso de IA:** usamos un asistente de IA (Claude) para ordenar la
redacción del informe y revisar la claridad de las respuestas de análisis
(P1–P5) y del research. **La explotación la hicimos nosotros** contra los
contenedores de la cátedra: cada comando de este informe fue ejecutado desde la
consola del atacante (`make shell`) y su salida está archivada sin editar en
`evidencia/salidas/`. Validamos todo lo que la IA sugirió contrastándolo contra
la salida real del laboratorio (las flags, los mensajes de error de conexión y
el diagrama de red del enunciado) y contra las fuentes citadas en `research.md`.
No pegamos flags que no hayamos capturado: las tres salen de `./ctf status
extra` en ✓.

---

## 1. Cadena de explotación

Todos los comandos se corren desde la consola del atacante (`make shell`), que
está en `labnet`. La intranet vive en `internalnet`, una red Docker marcada
`internal: true`: **no hay ruta directa** desde el atacante. Lo comprobamos
antes de empezar (evidencia `salidas/r0_alcance.txt`):

```
$ curl -s --max-time 5 http://phantomcorp/            # portal publico: responde
$ curl -s --max-time 4 http://phantomcorp-intra/      # intranet:
exit=6                                                # (curl: could not resolve host / no route)
```

El portal público expone en la home una **herramienta de previsualización de
URLs** para empleados: `GET /preview?url=<URL>`. El servidor fetchea esa URL
**desde su posición de red** y nos devuelve el contenido. No valida el destino:
no hay allowlist, no bloquea `localhost` ni IPs internas. Eso es SSRF
(CWE-918). Ese `/preview` es el único componente que usamos en los tres retos.

