# Skill: Sistema de Agentes IA

## Stack
- **LLM providers:** Groq (llama-3.3-70b), Anthropic Claude (CLI), NVIDIA NIM (coder)
- **Tool calling:** OpenAI-compatible function definitions
- **Memoria:** SQLite FTS5 (corto plazo) + vector DB (largo plazo, opcional)
- **API:** FastAPI + WebSocket para streaming
- **Orquestación:** DAG custom o asyncio.gather para paralelo

## Arquitectura base
```
agents/
├── base.py              # AgentContext, AgentOutput, BaseAgent
├── specialized/         # Agentes por dominio
providers/
├── base.py              # BaseProvider, LLMResponse
├── groq_provider.py
├── claude_provider.py
├── router.py            # Selección automática de provider
tools/                   # Herramientas que los agentes pueden usar
memory/
├── engram.py            # SQLite FTS5 — memoria institucional
├── session_store.py     # Estado por sesión
```

## Patrones de tool calling
```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Busca información en internet",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    }
]

# Groq con tools
response = await client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=messages,
    tools=TOOLS,
    tool_choice="auto",
)

# Ejecutar tools y hacer segunda llamada
if response.choices[0].message.tool_calls:
    # ... ejecutar tools, agregar resultados, segunda llamada
```

## Memoria con SQLite FTS5
```python
# Guardar decisión del agente
save_signal(project, agent_name, "decision", content)

# Recuperar contexto relevante
context = retrieve_context(project, limit=5)
```

## Patrones de retry y fallback
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2))
async def call_llm(prompt: str) -> str:
    ...

# Fallback entre providers
async def safe_complete(prompt: str) -> str:
    for provider in [groq, claude, nvidia]:
        try:
            return await provider.complete(prompt)
        except Exception:
            continue
    raise RuntimeError("Todos los providers fallaron")
```

## Streaming con WebSocket
```python
@app.websocket("/ws/agent")
async def agent_stream(ws: WebSocket):
    await ws.accept()
    async for chunk in agent.stream(prompt):
        await ws.send_json({"chunk": chunk, "done": False})
    await ws.send_json({"chunk": "", "done": True})
```

## Reglas de diseño
- Un agente = una responsabilidad. No mezclar lógica.
- Tool results siempre sanitizados antes de pasar al LLM
- Logs estructurados con contexto (project, phase, agent)
- Circuit breaker: máximo 3 reintentos por fase
