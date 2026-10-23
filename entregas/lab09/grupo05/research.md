# Mini-research — Laboratorio 09

**Tema elegido:** A — Tool-use / function calling: cómo lo implementan Claude y OpenAI a nivel de API, y en qué se parecen y diferencian.

- [x] **A.** Tool-use / function calling: cómo lo implementan Claude y OpenAI a
  nivel de API, y en qué se parecen y diferencian.


## Desarrollo

### Contexto

Tanto Anthropic (Claude) como OpenAI implementan un mecanismo que permite a los LLMs "llamar funciones": en vez de responder solo con texto, el modelo puede devolver una estructura de datos que indica qué función ejecutar y con qué argumentos. El código del cliente intercepta esa estructura, corre la función real, y devuelve el resultado al modelo. Ese ciclo es el loop de tool-use.

Este laboratorio implementa exactamente ese mecanismo en `llm.py`, con dos clientes reales (`ClienteClaude`, `ClienteOpenAI`) y uno simulado (`ClienteMock`). Estudiar las diferencias de protocolo entre ambas APIs permite entender por qué el diseño agnóstico de `llm.py` existe y qué abstrae.


### Cómo lo implementa Claude (Anthropic)

**Documentación de referencia:** https://docs.anthropic.com/en/docs/tool-use

#### Definición de tools

Al hacer la llamada a `POST /v1/messages`, se incluye un array `tools` donde cada herramienta se describe así:

```json
{
  "name": "http_get",
  "description": "Hace un GET HTTP a una URL y devuelve status, headers y cuerpo.",
  "input_schema": {
    "type": "object",
    "properties": {
      "url": { "type": "string", "description": "la URL a pedir" }
    },
    "required": ["url"]
  }
}
```

El `input_schema` es JSON Schema. Claude usa esta descripción para decidir cuándo llamar la herramienta y con qué argumentos.

#### Respuesta del modelo cuando elige una tool

Claude devuelve un bloque de tipo `tool_use` en `content`:

```json
{
  "type": "tool_use",
  "id": "toolu_01abc...",
  "name": "http_get",
  "input": { "url": "http://phantomcorp/robots.txt" }
}
```

El campo clave es `id`: es el identificador de esta tool call específica, que hay que devolver en el siguiente mensaje.

#### Cómo se devuelve el resultado

El resultado se envía como un mensaje de rol `user` con un bloque de tipo `tool_result`:

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_01abc...",
      "content": "HTTP 200\nUser-agent: *\nDisallow: /vault-interno-x7\n"
    }
  ]
}
```

El `tool_use_id` vincula el resultado con la tool call que lo generó. Claude puede tener múltiples tool calls en un mismo mensaje; cada una se devuelve con su propio `tool_use_id`.

#### Condición de fin

Cuando Claude considera que terminó (o no necesita más tools), devuelve un bloque de tipo `text` en lugar de `tool_use`. En `ClienteClaude.paso()` esto se detecta así:

```python
for bloque in resp["content"]:
    if bloque["type"] == "tool_use":
        return {"tipo": "tool", ...}
texto = "".join(b.get("text", "") for b in resp["content"] if b["type"] == "text")
return {"tipo": "final", "texto": texto}
```

---

### Cómo lo implementa OpenAI

**Documentación de referencia:** https://platform.openai.com/docs/guides/function-calling

#### Definición de tools

En `POST /v1/chat/completions`, las tools van como:

```json
{
  "type": "function",
  "function": {
    "name": "http_get",
    "description": "Hace un GET HTTP a una URL y devuelve status, headers y cuerpo.",
    "parameters": {
      "type": "object",
      "properties": {
        "url": { "type": "string", "description": "la URL a pedir" }
      },
      "required": ["url"]
    }
  }
}
```

La diferencia visible con Claude: el campo se llama `parameters` (no `input_schema`) y está anidado bajo `function`. El wrapper `type: "function"` es obligatorio.

#### Respuesta del modelo cuando elige una tool

OpenAI devuelve la tool call en `choices[0].message.tool_calls`:

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "call_abc123",
      "type": "function",
      "function": {
        "name": "http_get",
        "arguments": "{\"url\": \"http://phantomcorp/robots.txt\"}"
      }
    }
  ]
}
```

Diferencia importante: `arguments` es un **string JSON** (no un objeto), así que hay que hacer `json.loads(tc["function"]["arguments"])`. Claude devuelve `input` directamente como un objeto.

#### Cómo se devuelve el resultado

El resultado va como un mensaje de rol `tool` (no `user`):

```json
{
  "role": "tool",
  "tool_call_id": "call_abc123",
  "content": "HTTP 200\nUser-agent: *\nDisallow: /vault-interno-x7\n"
}
```

#### Condición de fin

Cuando OpenAI termina, `message.tool_calls` está ausente o vacío, y `message.content` tiene el texto final.

---

### Tabla comparativa

| Aspecto | Claude (Anthropic) | OpenAI |
|---|---|---|
| Endpoint | `POST /v1/messages` | `POST /v1/chat/completions` |
| Clave de tools en request | `tools[].input_schema` | `tools[].function.parameters` |
| Formato de argumentos en respuesta | Objeto JSON (`input`) | String JSON (`arguments`) |
| Rol para devolver resultados | `user` (bloque `tool_result`) | `tool` (mensaje separado) |
| ID de la tool call | `tool_use_id` | `tool_call_id` |
| Tipo del bloque de tool call | `tool_use` | dentro de `tool_calls[]` |
| Condición de fin | bloque `text` en vez de `tool_use` | `tool_calls` ausente |
| Auth header | `x-api-key` + `anthropic-version` | `Authorization: Bearer` |

---

### Por qué el diseño agnóstico importa

La tabla muestra que las diferencias son de formato, no de concepto: ambas APIs implementan el mismo loop. `llm.py` absorbe esas diferencias en dos clases (`ClienteClaude`, `ClienteOpenAI`) que exponen la misma interfaz (`paso(resultados) → accion`). El loop en `agente_esqueleto.py` no sabe cuál está usando.

Esto es el **principio de acoplamiento a interfaces**: el agente depende de la abstracción, no de la implementación. Si mañana aparece un tercer proveedor (Gemini, Mistral), se agrega una tercera clase sin tocar el loop.


## Fuentes

1. Anthropic — Tool use (function calling): https://docs.anthropic.com/en/docs/tool-use
2. OpenAI — Function calling guide: https://platform.openai.com/docs/guides/function-calling
3. Código fuente del laboratorio: `labs/lab09-agentes/src/llm.py` (implementación de `ClienteClaude` y `ClienteOpenAI` lado a lado, para comparación directa)


## Reflexión

Lo más valioso de este tema no es la diferencia de nombres de campos entre APIs: es entender que "agente" y "function calling" son el mismo mecanismo visto desde lados distintos. El LLM decide; el código ejecuta; el resultado vuelve al LLM. Ese loop de tres pasos es universal. Las diferencias de protocolo entre Claude y OpenAI son accidentales, no esenciales.

Para seguridad, esto tiene una implicación directa: el guardrail no vive en el LLM, sino en el código que ejecuta las tools. No importa qué proveedor use el agente: si `_verificar_alcance()` está bien implementada, ningún LLM puede salir del scope autorizado, porque el control está en el lado del cliente, no en el razonamiento del modelo.