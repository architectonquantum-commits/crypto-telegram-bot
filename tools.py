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

# Warnings contextuales por timeframe
TIMEFRAME_WARNINGS = {
    "15m": "⚠️ SCALPING: Verifica precio ACTUAL en tu exchange antes de entrar",
    "30m": "📊 Datos de hace {age} - Verifica contexto actual antes de operar",
    "1h": "✅ Datos recientes - Válido para swing trading",
    "4h": "✅ Tendencia confirmada - Timeframe posicional"
}

def get_scanner_analysis(timeframe: str = "1h") -> Dict[str, Any]:
    """
    Ejecuta el scanner usando el endpoint con caché
    ACEPTA CACHÉ STALE - mejor dato viejo que timeout
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
            json={
                "timeframe": timeframe,
                "use_cache": True,
                "min_confluence": 70.0
            },
            timeout=180  # 3 minutos máx
        )
        response.raise_for_status()
        data = response.json()
        
        is_cached = data.get("cached", False)
        exec_time = data.get("execution_time", 0)
        cache_age = data.get("cache_age_seconds", 0)
        cache_age_human = data.get("cache_age_human", "")
        
        # Agregar warning contextual
        warning = None
        if is_cached and cache_age > 0:
            warning = TIMEFRAME_WARNINGS.get(timeframe, "").format(age=cache_age_human)
        
        if is_cached:
            print(f"✅ Cache HIT! Respuesta en {exec_time:.2f}s (edad: {cache_age_human})")
        else:
            print(f"✅ Scanner ejecutado y cacheado en {exec_time:.2f}s")
        
        return {
            "success": True,
            "data": data,
            "timeframe": timeframe,
            "cached": is_cached,
            "cache_age": cache_age_human if is_cached else None,
            "warning": warning
        }
        
    except requests.exceptions.Timeout:
        print(f"⏱️ Timeout en {timeframe}")
        return {
            "success": False,
            "error": f"Timeout ejecutando scanner en {timeframe}. El servidor puede estar sobrecargado. Intenta con otro timeframe o espera 30 segundos.",
            "timeout": True
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
        "description": "Ejecuta el scanner de señales con CACHÉ INTELIGENTE. Usa caché reciente cuando está disponible (respuesta <2s), o genera datos frescos si es necesario. IMPORTANTE: Si da timeout, recomienda al usuario intentar con otro timeframe. Los timeframes más grandes (4h) tienen más probabilidad de tener caché disponible.",
        "input_schema": {
            "type": "object",
            "properties": {
                "timeframe": {
                    "type": "string",
                    "enum": ["15m", "30m", "1h", "4h"],
                    "description": "Timeframe para el scanner. 15m=scalping, 30m=intraday, 1h=swing, 4h=tendencias"
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
