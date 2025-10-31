"""
Telegram Bot para Crypto Analyzer con Claude - OPTIMIZADO
"""
import os
import logging
from datetime import time
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from dotenv import load_dotenv
from claude_handler import chat_with_claude
import asyncio

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

user_conversations = {}
user_configs = {}

TIMEFRAMES = ["15m", "30m", "1h", "4h"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    
    user_configs[user_id] = {
        "daily_plan_enabled": True,
        "scalping_alerts": True,
        "risk_per_trade": 1.0,
        "preferred_symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    }
    
    welcome_message = """
🤖 **Crypto Analyzer Pro - Trading Assistant**

¡Bienvenido! Soy tu analista personal de criptomonedas.

**🌅 Plan Diario:**
Cada día a las 9:00 AM recibirás:
- Análisis de tendencias con datos reales
- Setups de trading del día
- Niveles clave a monitorear

**📊 Comandos disponibles:**
/start - Iniciar bot
/plan - Plan del día con datos REALES
/scan [TF] - Escanear señales (15m/30m/1h/4h)
/help - Ayuda completa

**Timeframes:**
4H (tendencia) • 1H (contexto) • 30M (setups) • 15M (scalping)

⚠️ Este bot es educativo. No es asesoría financiera.
    """
    
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    help_text = """
📚 **Guía completa:**

**🌅 PLAN DIARIO (/plan):**
Genera un plan completo con:
- Mejores oportunidades del momento
- Precios y niveles reales
- Setups con confluencias
- Gestión de riesgo

**🔍 SCANNER (/scan):**
/scan 4h - Tendencias principales
/scan 1h - Contexto del día  
/scan 30m - Setups de trading
/scan 15m - Scalping rápido

**💬 CONSULTAS LIBRES:**
"Analiza BTC/USDT"
"¿Qué opinas de ETH?"
"Dame niveles de SOL"

**⚙️ CONFIGURACIÓN:**
/config - Ver/cambiar configuración
    """
    
    await update.message.reply_text(help_text)

async def plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /plan - Plan del día OPTIMIZADO"""
    await update.message.reply_text("📊 Generando plan de trading con datos reales...")
    
    user_id = update.effective_user.id
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    
    # Prompt OPTIMIZADO - máximo 1-2 tool calls
    prompt = """Genera un PLAN DE TRADING COMPLETO usando el scanner:

**INSTRUCCIONES CRÍTICAS:**
1. Llama PRIMERO a get_scanner_analysis con timeframe "1h"
2. USA LOS DATOS REALES que retorne el scanner
3. Enfócate en las oportunidades con confluencia >65%
4. Incluye precios EXACTOS del scanner

**FORMATO DEL PLAN:**

🌅 **PLAN DE TRADING - HOY**

📊 **MEJORES OPORTUNIDADES:**
Para cada oportunidad del scanner con >65% confluencia:
- Símbolo y precio actual
- Dirección (LONG/SHORT)
- Confluencia %
- Entrada sugerida
- Stop Loss
- Take Profit
- Risk/Reward

🎯 **SETUPS PARA SCALPING:**
Las 2-3 mejores oportunidades para operar en 30M/15M

⚠️ **GESTIÓN DE RIESGO:**
- Máximo 1% por trade
- No más de 3 trades simultáneos

📍 **NIVELES CLAVE:**
Soportes y resistencias de los principales pares

**IMPORTANTE:** Usa SOLO datos del scanner. NO inventes precios."""
    
    try:
        response = chat_with_claude(prompt, [])  # Nueva conversación cada vez
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error en /plan: {e}")
        await update.message.reply_text(
            "❌ Error generando el plan. Verifica que el backend esté activo."
        )

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /scan [timeframe]"""
    timeframe = "1h"
    if context.args and len(context.args) > 0:
        tf = context.args[0].lower()
        if tf in TIMEFRAMES:
            timeframe = tf
        else:
            await update.message.reply_text(
                f"⚠️ Timeframe no válido. Usa: {', '.join(TIMEFRAMES)}"
            )
            return
    
    await update.message.reply_text(f"🔍 Escaneando señales en {timeframe}...")
    
    user_id = update.effective_user.id
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    
    prompt = f"""Ejecuta el scanner en {timeframe} y muestra las mejores 3 señales.

**FORMATO:**
Para cada señal incluye:
📊 Símbolo - Precio actual
📈 Dirección y confluencia
🎯 Niveles: Entrada / SL / TP
💰 Risk/Reward ratio

Usa SOLO datos del scanner. Sé conciso."""
    
    response = chat_with_claude(prompt, user_conversations[user_id])
    await update.message.reply_text(response)

async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /config"""
    user_id = update.effective_user.id
    
    if user_id not in user_configs:
        user_configs[user_id] = {
            "daily_plan_enabled": True,
            "scalping_alerts": True,
            "risk_per_trade": 1.0,
            "preferred_symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        }
    
    config = user_configs[user_id]
    
    config_text = f"""
⚙️ **Tu configuración:**

🌅 Plan diario (9 AM): {'✅ Activado' if config['daily_plan_enabled'] else '❌ Desactivado'}
⚡ Alertas: {'✅ Activado' if config['scalping_alerts'] else '❌ Desactivado'}
💰 Riesgo por trade: {config['risk_per_trade']}%
📊 Símbolos: {', '.join(config['preferred_symbols'])}

Escribe "configurar [opción] [valor]" para cambiar.
    """
    
    await update.message.reply_text(config_text)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /clear"""
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    await update.message.reply_text("✅ Historial limpiado")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto"""
    user_id = update.effective_user.id
    user_message = update.message.text.lower()
    
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    
    if user_message.startswith("configurar"):
        await handle_config_change(update, context, user_message)
        return
    
    await update.message.chat.send_action("typing")
    
    try:
        response = chat_with_claude(
            update.message.text,
            user_conversations[user_id]
        )
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Error procesando mensaje")

async def handle_config_change(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
    """Maneja cambios de configuración"""
    user_id = update.effective_user.id
    
    if user_id not in user_configs:
        user_configs[user_id] = {
            "daily_plan_enabled": True,
            "scalping_alerts": True,
            "risk_per_trade": 1.0,
            "preferred_symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        }
    
    parts = message.split()
    if len(parts) < 3:
        await update.message.reply_text("⚠️ Formato: configurar [opción] [valor]")
        return
    
    option = parts[1]
    value = parts[2]
    
    if option == "plan":
        user_configs[user_id]["daily_plan_enabled"] = value in ["activado", "si"]
        await update.message.reply_text(f"✅ Plan diario {'activado' if user_configs[user_id]['daily_plan_enabled'] else 'desactivado'}")
    elif option == "riesgo":
        try:
            risk = float(value)
            user_configs[user_id]["risk_per_trade"] = risk
            await update.message.reply_text(f"✅ Riesgo: {risk}%")
        except:
            await update.message.reply_text("⚠️ Valor inválido")

async def daily_plan_job(context: ContextTypes.DEFAULT_TYPE):
    """Job diario a las 9 AM"""
    logger.info("🌅 Generando planes diarios...")
    
    for user_id, config in user_configs.items():
        if config.get("daily_plan_enabled", True):
            try:
                prompt = """Genera el plan de trading para HOY usando el scanner en 1h.

Incluye las mejores 3-5 oportunidades con precios reales, niveles y gestión de riesgo.
Sé específico y profesional."""
                
                response = chat_with_claude(prompt, [])
                
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🌅 **PLAN DEL DÍA**\n\n{response}"
                )
                logger.info(f"✅ Plan enviado a {user_id}")
            except Exception as e:
                logger.error(f"Error enviando plan a {user_id}: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja errores"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Función principal"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN no encontrado")
        return
    
    application = Application.builder().token(token).build()
    
    # Comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("plan", plan_command))
    application.add_handler(CommandHandler("scan", scan_command))
    application.add_handler(CommandHandler("config", config_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Jobs
    job_queue = application.job_queue
    job_queue.run_daily(
        daily_plan_job,
        time=time(hour=9, minute=0, second=0),
        name="daily_plan"
    )
    
    logger.info("🚀 Bot iniciado")
    logger.info("📅 Plan diario: 9:00 AM")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
