import os
import io
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import requests
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# --- Micro-servidor web para mantener Render activo ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo y funcionando.")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# --- Configuración del Bot ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

client_gemini = genai.Client(api_key=GEMINI_KEY)

ESTADO_USUARIO = {}
PROMPT_ESTILO_GUARDADO = "sacred geometry, glowing ethereal energy, deep black background with gold highlights, 8k render"

def extraer_adn_de_estilo(imagen_bytes):
    img = Image.open(io.BytesIO(imagen_bytes))
    instruccion = (
        "Analyze the visual style, art medium, lighting, color palette, and textures of this image. "
        "Write a concise, professional image-generation prompt (under 60 words) that captures ONLY this exact aesthetic style, "
        "rendering technique, and mood, without focusing on the specific subject. Return only the prompt in English."
    )
    respuesta = client_gemini.models.generate_content(
        model="gemini-3.6-flash",
        contents=[img, instruccion]
    )
    return respuesta.text.strip()

def describir_sujeto_base(imagen_bytes):
    img = Image.open(io.BytesIO(imagen_bytes))
    instruccion = "Describe the main subject, central pose, and key objects in this image in one brief English phrase."
    respuesta = client_gemini.models.generate_content(
        model="gemini-3.6-flash",
        contents=[img, instruccion]
    )
    return respuesta.text.strip()

def generar_con_estilo(sujeto, estilo):
    prompt_final = f"{sujeto}, {estilo}, masterpiece, cinematic lighting, ultra sharp focus, 8k resolution"
    prompt_encoded = urllib.parse.quote(prompt_final)
    url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=1024&nologo=true&model=flux"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    res = requests.get(url, headers=headers, timeout=90)
    if res.status_code == 200 and len(res.content) > 5000:
        return res.content
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🎨 *Bot Cloud Activo*\n\n"
        "1. Usa /guardar_estilo y envía una foto para que la IA extraiga su estética.\n"
        "2. Usa /procesar y envía la imagen base que quieres recrear con ese estilo."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def set_modo_estilo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ESTADO_USUARIO[update.effective_user.id] = "esperando_estilo"
    await update.message.reply_text("📸 Envía la imagen con el estilo que deseas extraer.")

async def set_modo_procesar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ESTADO_USUARIO[update.effective_user.id] = "esperando_entrada"
    await update.message.reply_text("📸 Envía la imagen base que deseas transformar.")

async def recibir_imagen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global PROMPT_ESTILO_GUARDADO
    user_id = update.effective_user.id
    modo = ESTADO_USUARIO.get(user_id)

    if not modo:
        await update.message.reply_text("Usa /guardar_estilo o /procesar primero.")
        return

    foto = update.message.photo[-1]
    archivo = await context.bot.get_file(foto.file_id)
    buffer = io.BytesIO()
    await archivo.download_to_memory(buffer)
    imagen_bytes = buffer.getvalue()

    if modo == "esperando_estilo":
        ESTADO_USUARIO.pop(user_id, None)
        msg_wait = await update.message.reply_text("🧠 Analizando el ADN visual de la imagen...")
        try:
            PROMPT_ESTILO_GUARDADO = extraer_adn_de_estilo(imagen_bytes)
            await msg_wait.edit_text(f"✅ *Estilo guardado:*\n\n_{PROMPT_ESTILO_GUARDADO}_\n\nYa puedes usar /procesar.", parse_mode="Markdown")
        except Exception as e:
            await msg_wait.edit_text(f"Error al analizar estilo: {str(e)}")

    elif modo == "esperando_entrada":
        ESTADO_USUARIO.pop(user_id, None)
        msg_wait = await update.message.reply_text("⚡ Reinterpretando tu imagen con el estilo maestro...")
        try:
            sujeto = describir_sujeto_base(imagen_bytes)
            resultado_bytes = generar_con_estilo(sujeto, PROMPT_ESTILO_GUARDADO)
            
            if resultado_bytes:
                await update.message.reply_photo(
                    photo=io.BytesIO(resultado_bytes),
                    caption=f"✨ *Resultado Final*\nSujeto detectado: {sujeto}"
                )
            else:
                await update.message.reply_text("Error al generar la imagen.")
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
        finally:
            await msg_wait.delete()

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("guardar_estilo", set_modo_estilo))
    app.add_handler(CommandHandler("procesar", set_modo_procesar))
    app.add_handler(MessageHandler(filters.PHOTO, recibir_imagen))
    app.run_polling()
