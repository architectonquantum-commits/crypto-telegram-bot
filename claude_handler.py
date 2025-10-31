"""
Handler para interactuar con Claude API y gestionar tool calling
"""
import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv
from tools import (
    get_scanner_analysis,
    validate_signal,
    TOOLS
)

# Cargar .env PRIMERO
load_dotenv()

# Inicializar cliente DESPUÉS de cargar .env
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# System prompt para el análisis de trading
SYSTEM_PROMPT = """Eres un analista cuantitativo experto en criptomonedas y trading algorítmico.

## Tu rol:
- Analizar señales de trading con rigor profesional
- Proporcionar análisis técnico basado en datos reales
- Validar setups con confluencias múltiples
- Gestionar riesgo de forma profesional

## Reglas estrictas:
1. **NUNCA inventes datos** - Usa SOLO lo que retornan las herramientas
2. **NO des asesoría financiera** - Todo es educativo
3. **SIEMPRE menciona riesgos** - Trading es riesgoso
4. **Incluye disclaimer** - "No es asesoría financiera"
5. **Sé preciso con números** - Precios exactos, porcentajes claros

## Formato de respuesta:
Usa emojis para mejor legibilidad:
- 📊 Para datos de mercado
- 📈 Para señales alcistas
- 📉 Para señales bajistas
- 🎯 Para niveles de entrada
- 🛑 Para stop loss
- 💰 Para take profit
- ✅ Para confluencias positivas
- ⚠️ Para riesgos

## Herramientas disponibles:
1. **get_scanner_analysis**: Escanea múltiples criptos buscando señales
2. **validate_signal**: Valida una señal específica con backtesting

## Disclaimer obligatorio:
Termina SIEMPRE con: "⚠️ No es asesoría financiera. Opera bajo tu propio riesgo."
"""

def process_tool_call(tool_name: str, tool_input: dict) -> dict:
    """
    Ejecuta la herramienta solicitada por Claude
    """
    if tool_name == "get_scanner_analysis":
        return get_scanner_analysis(**tool_input)
    elif tool_name == "validate_signal":
        return validate_signal(**tool_input)
    else:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

def chat_with_claude(user_message: str, conversation_history: list = None) -> str:
    """
    Interactúa con Claude usando tool calling
    """
    if conversation_history is None:
        conversation_history = []
    # Agregar mensaje del usuario
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    # Llamada inicial a Claude
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        messages=conversation_history
    )
    # Loop de tool calling
    while response.stop_reason == "tool_use":
        # Procesar tool calls
        tool_results = []
        
        for content_block in response.content:
            if content_block.type == "tool_use":
                tool_name = content_block.name
                tool_input = content_block.input
                tool_id = content_block.id
                
                print(f"🔧 Claude llamó a: {tool_name}")
                
                # Ejecutar herramienta
                result = process_tool_call(tool_name, tool_input)
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": json.dumps(result)
                })
        
        # Agregar respuesta de Claude con tool calls a la conversación
        conversation_history.append({
            "role": "assistant",
            "content": response.content
        })
        
        # Agregar resultados de tools
        conversation_history.append({
            "role": "user",
            "content": tool_results
        })
        
        # Continuar conversación con los resultados
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=conversation_history
        )
    # Extraer respuesta final de texto
    final_response = ""
    for content_block in response.content:
        if hasattr(content_block, "text"):
            final_response += content_block.text
    return final_response

# Función simple para testing
def test_claude():
    """
    Test rápido de Claude
    """
    response = chat_with_claude("Analiza BTC/USDT en 5m")
    print(response)

if __name__ == "__main__":
    test_claude()
