"""
Tools para que Claude llame al backend con caché optimizado
"""
import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

def normalize_symbol(symbol: str) -> str:
    """Convierte BTCUSDT -> BTC/USDT para Kraken"""
    if "/" in symbol:
        return symbol
    symbol_map = {
        "BTCUSDT": "BTC/USDT", "ETHUSDT": "ETH/USDT", "XRPUSDT": "XRP/USDT",
        "ADAUSDT": "ADA/USDT", "SOLUSDT": "SOL/USDT", "DOGEUSDT": "DOGE/USDT",
        "DOTUSDT": "DOT/USDT", "LTCUSDT": "LTC/USDT", "LINKUSDT": "LINK/USDT",
        "TRXUSDT": "TRX/USDT", "ATOMUSDT": "ATOM/USDT", "UNIUSDT": "UNI/USDT",
        "BNBUSDT": "BNB/USDT", "AVAXUSDT": "AVAX/USDT", "XLMUSDT": "XLM/USDT",
        "HBARUSDT": "HBAR/USDT", "ARBUSDT": "ARB/USDT", "XDCUSDT": "XDC/USDT"
    }
    if symbol in symbol_map:
        return symbol_map[symbol]
    if symbol.endswith("USDT"):
        return symbol.replace("USDT", "/USDT")
    return symbol


BACKEND_URL = os.getenv("BACKEND_URL")

if not BACKEND_URL:
    print("⚠️ WARNING: BACKEND_URL no configurado en .env")
else:
    print(f"✅ Backend configurado: {BACKEND_URL}")

def get_scanner_analysis(timeframe: str = "1h") -> Dict[str, Any]:
    """
    Ejecuta el scanner usando el endpoint con caché (respuesta < 1 segundo)
    """
    if not BACKEND_URL:
        return {
            "success": False,
            "error": "BACKEND_URL no configurado en .env"
        }
    
    try:
        print(f"🔍 Llamando scanner CACHEADO en {timeframe}...")
        response = requests.post(
            f"{BACKEND_URL}/api/scanner/cached/run",
            auth=("architecton", "751826Tm#@!"),
            json={
                "timeframe": timeframe,
                "use_cache": True,
                "max_cache_age": 5
            },
            timeout=60  # Reducido a 10 segundos (debería responder en <1s)
        )
        response.raise_for_status()
        data = response.json()
        
        is_cached = data.get("cached", False)
        exec_time = data.get("execution_time", 0)
        
        if is_cached:
            print(f"✅ Cache HIT! Respuesta en {exec_time:.2f}s")
        else:
            print(f"✅ Scanner ejecutado y cacheado en {exec_time:.2f}s")
        
        return {
            "success": True,
            "data": data,
            "timeframe": timeframe,
            "cached": is_cached
        }
    except requests.exceptions.Timeout:
        print(f"⏱️ Timeout - intentando sin caché...")
        # Fallback: intentar sin caché si el timeout fue por primera ejecución
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/scanner/run",
                auth=("architecton", "751826Tm#@!"),
                json={"timeframe": timeframe},
                timeout=120
            )
            response.raise_for_status()
            return {
                "success": True,
                "data": response.json(),
                "timeframe": timeframe,
                "cached": False
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error en fallback: {str(e)}"
            }
    except Exception as e:
        print(f"❌ Error en scanner: {e}")
        return {
            "success": False,
            "error": f"Error llamando al scanner: {str(e)}"
        }

def validate_signal(
    symbol: str,
    direction: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    timeframe: str = "1h"
) -> Dict[str, Any]:
    """
    Valida una señal de trading usando el validador
    """
    if not BACKEND_URL:
        return {
            "success": False,
            "error": "BACKEND_URL no configurado en .env"
        }
    
    try:
        print(f"🔍 Validando señal {direction} {symbol}...")
        response = requests.post(
            f"{BACKEND_URL}/api/validator/validate-signal",
            json={
                "symbol": normalize_symbol(symbol),
                "direction": direction,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "timeframe": timeframe
            },
            timeout=60
        )
        response.raise_for_status()
        return {
            "success": True,
            "data": response.json()
        }
    except Exception as e:
        print(f"❌ Error en validación: {e}")
        return {
            "success": False,
            "error": f"Error validando señal: {str(e)}"
        }

# Tool definitions para Claude
TOOLS = [
    {
        "name": "get_scanner_analysis",
        "description": "Ejecuta el scanner de señales en el backend con CACHÉ OPTIMIZADO (respuesta <1 segundo). Retorna las mejores oportunidades del momento con confluencias, precio actual, stop loss y take profit sugeridos. USA ESTA HERRAMIENTA PRIMERO para obtener datos reales del mercado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "timeframe": {
                    "type": "string",
                    "enum": ["15m", "30m", "1h", "4h"],
                    "description": "Timeframe para el scanner"
                }
            },
            "required": ["timeframe"]
        }
    },
    {
        "name": "validate_signal",
        "description": "Valida una señal específica con módulos de confluencia y backtesting. Usa solo cuando el usuario pida validar una señal concreta.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Par de trading (ej: BTCUSDT, sin / ni guión)"
                },
                "direction": {
                    "type": "string",
                    "enum": ["LONG", "SHORT"],
                    "description": "Dirección de la señal"
                },
                "entry_price": {
                    "type": "number",
                    "description": "Precio de entrada propuesto"
                },
                "stop_loss": {
                    "type": "number",
                    "description": "Precio de stop loss"
                },
                "take_profit": {
                    "type": "number",
                    "description": "Precio de take profit"
                },
                "timeframe": {
                    "type": "string",
                    "enum": ["15m", "30m", "1h", "4h"],
                    "description": "Timeframe de la señal"
                }
            },
            "required": ["symbol", "direction", "entry_price", "stop_loss", "take_profit"]
        }
    }
]
