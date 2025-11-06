import telebot as tlb
import requests
import json
import os
from transformers import pipeline
import time
from groq import Groq
from typing import Optional
from dotenv import load_dotenv
import base64
import re
from PIL import Image
import mimetypes
from PyPDF2 import PdfReader
from docx import Document
from pytubefix import YouTube

load_dotenv()

TOKEN_BOT_TELEGRAM = os.getenv('TELEGRAM_BOT_TOKEN')
CLAVE_API_GROQ = os.getenv('GROQ_API_KEY')
DATASET_PATH = os.getenv('DATASET_PATH')

if not TOKEN_BOT_TELEGRAM:
    raise ValueError("TELEGRAM_BOT_TOKEN no está configurado en las variables de entorno")

if not CLAVE_API_GROQ:
    raise ValueError("GROQ_API_KEY no está configurado en las variables de entorno")

bot = tlb.TeleBot(TOKEN_BOT_TELEGRAM)
cliente_groq = Groq(api_key=CLAVE_API_GROQ)

def cargar_dataset():
	try:
		with open(DATASET_PATH, 'r', encoding='utf-8') as f:
			return json.load(f)
	except Exception:
		return []

#FUNCIONAMIENTO EN PRIVADO

def buscar_en_dataset(pregunta, dataset):
	pregunta = pregunta.strip().lower()
	# Recorre cada elemento del dataset
	for item in dataset:
		# Compara la pregunta del usuario con la del dataset (normalizada)
		if item['pregunta'].strip().lower() == pregunta:
			# Si hay coincidencia exacta, retorna la respuesta
			return item['respuesta']
	# Si no encuentra coincidencia, retorna None
	return None

def get_groq_response(user_message: str) -> Optional[str]:
    try:
        system_prompt = f"""Eres un asistente virtual de capacitación interna diseñado para ayudar a los empleados de una empresa a aprender sobre la organización, sus políticas, valores, procedimientos y herramientas de trabajo.
Tu tarea principal es responder preguntas relacionadas con la empresa y su cultura corporativa, además de crear pequeños quizzes o preguntas de repaso para reforzar el aprendizaje.

Tus respuestas deben ser claras, profesionales y breves, adecuadas para un entorno laboral. Puedes usar un tono amable pero siempre formal.


Datos de la empresa:
{json.dumps(DATASET_PATH, ensure_ascii=False, indent=2)}


Reglas importantes:
Responde solo con la información disponible en tu dataset o en la base de conocimiento interna de la empresa.
No inventes ni agregues contenido adicional más allá de lo que esté en el dataset.
No incluyas saludos, despedidas ni frases de cortesía (por ejemplo: "Hola", "Gracias por tu consulta", etc.).
Tus respuestas deben ir directo al punto.
Cuando el usuario pida un quiz o evaluación, genera entre 3 y 5 preguntas cortas relacionadas con los temas disponibles en tu dataset.
Pueden ser de opción múltiple o de verdadero/falso.
No evalúes las respuestas, solo formula las preguntas.
No utilices emojis ni lenguaje coloquial.
Usa redacción neutra, profesional y sin tecnicismos innecesarios.
Si el usuario solicita modificar, actualizar o agregar información, responde que no tienes permisos para modificar la base de datos.
Si el usuario formula preguntas personales o fuera del contexto de capacitación, puedes responder con una frase general del estilo:
"Mi función es asistir en temas de capacitación y aprendizaje interno."""

        chat_completion = cliente_groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_message


                }
            ],
            model = "llama-3.3-70b-versatile",
            temperature = 0.3,
            max_tokens = 500
        )


        return chat_completion.choices[0].message.content.strip()
   
    except Exception as e:
        print(f"Error al obtener la respuesta: {str(e)}")
        return None
	
dataset = cargar_dataset()


# Configuracion del bot

def load_company_data():
    try:
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al cargar el json: {str(e)}")
        return None

company_data = load_company_data()


def trascribe_voice_with_groq(message: tlb.types.Message) -> Optional[str]:
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        temp_file = "temp_voice.ogg"


        #guardar el archivo de forma temporal
        with open(temp_file, "wb") as f:
            f.write(downloaded_file)
        with open(temp_file, "rb") as file:
            trascription = cliente_groq.audio.transcriptions.create(
                file = (temp_file, file.read()),
                model = "whisper-large-v3-turbo",
                prompt = "Especificar contexto o pronunciacion",
                response_format = "json",
                language= "es",
                temperature = 1
            )
        os.remove(temp_file)


        return trascription.text
   
    except Exception as e:
        print(f"Error al transcribir; {str(e)}")
        return None   


    
def imagen_a_base64(ruta_o_bytes_imagen):
    """Convierte una imagen a base64 para enviarla a Groq"""
    try:
        if isinstance(ruta_o_bytes_imagen, bytes):
            return base64.b64encode(ruta_o_bytes_imagen).decode('utf-8')
        else:
            with open(ruta_o_bytes_imagen, "rb") as archivo_imagen:
                return base64.b64encode(archivo_imagen.read()).decode('utf-8')
    except Exception as e:
        print(f"Error al convertir imagen a base64: {e}")
        return None

def describir_imagen_con_groq(imagen_base64):
    """Envía la imagen a Groq y obtiene la descripción"""
    try:
        completado_chat = cliente_groq.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Por favor, describe esta imagen de manera detallada y clara en español. Incluye todos los elementos importantes que veas, colores, objetos, personas, acciones, emociones, y cualquier detalle relevante que puedas observar."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{imagen_base64}"
                            }
                        }
                    ]
                }
            ],
            model= "meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.7,
            max_tokens=1000
        )
        return completado_chat.choices[0].message.content
    except Exception as e:
        print(f"Error al describir imagen con Groq: {e}")
        return None

def extraer_texto_de_documento(file_bytes, file_name):
    os.makedirs("temp", exist_ok=True)
    file_path = f"temp/{file_name}"

    # Guarda los bytes en un archivo temporal
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Detecta tipo MIME (por ejemplo: text/plain, application/pdf, etc.)
    mime_type, _ = mimetypes.guess_type(file_path)
    texto = ""

    try:
        # === TXT, JSON, CSV, etc. ===
        if mime_type and "text" in mime_type:
            texto = file_bytes.decode("utf-8", errors="ignore")

        # === PDF ===
        elif mime_type == "application/pdf" or file_name.lower().endswith(".pdf"):
            reader = PdfReader(file_path)
            texto = " ".join([page.extract_text() or "" for page in reader.pages])

        # === DOCX ===
        elif mime_type in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",) \
             or file_name.lower().endswith(".docx"):
            doc = Document(file_path)
            texto = " ".join([p.text for p in doc.paragraphs])

        else:
            texto = "⚠️ No se reconoce o no se puede leer el formato del archivo."

    except Exception as e:
        texto = f"❌ Error al extraer texto: {e}"

    return texto

def limpiar_respuesta_json(texto):
    """
    Elimina los bloques ``` y etiquetas tipo ```json de una respuesta de IA.
    """
    texto = texto.strip()
    if texto.startswith("```"):
        partes = texto.split("```")
        if len(partes) >= 2:
            texto = partes[1]
    # Borra 'json' si aparece al principio del bloque
    texto = texto.replace("json\n", "").replace("json\r\n", "")
    return texto.strip()

def generar_quiz_con_groq(texto, nombre_documento):
    nombre_base, _ = os.path.splitext(nombre_documento)
    nombre_base = nombre_base.replace(" ", "_")

    # Buscar nombre disponible
    ruta = f"quizzes/{nombre_base}.json"
    contador = 1
    while os.path.exists(ruta):
        ruta = f"quizzes/{nombre_base}_{contador}.json"
        contador += 1

    prompt = f"""
    Generá un quiz de 5 preguntas de opción múltiple basadas en el siguiente texto.
    Incluí una respuesta correcta y 3 opciones incorrectas por pregunta.
    El quiz debe estar en formato JSON, con la siguiente estructura:
    [{{"pregunta": "¿Qué cursos están disponibles?", "opciones": ["Curso A", "Curso B", "Curso C", "Curso D"], "respuesta_correcta": "a"}}]
    No incluyas explicaciones, texto adicional ni comillas triples, solo el JSON plano.
    
    Texto: {texto}
    """

    response = cliente_groq.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": "Sos un generador de quizzes educativo."},
            {"role": "user", "content": prompt}
        ]
    )

    quiz = response.choices[0].message.content.strip()
    quiz = quiz.strip("`") 
    quiz = quiz.replace("```json", "").replace("```", "").strip()

    if not quiz.strip().startswith("["):
        quiz = f"[{quiz}]"

    with open(ruta, "w", encoding="utf-8") as f:
        f.write(quiz)

    print(f"\n✅ QUIZ GENERADO: {ruta}\n")
    return nombre_base

def download_audio_from_youtube(url, output_path="temp_audio"):
    """Descarga solo el audio de un video de YouTube y devuelve la ruta del archivo."""
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).first()

        os.makedirs(output_path, exist_ok=True)
        print(f"Descargando audio de: {yt.title}")
        out_file = stream.download(output_path)
        base, _ = os.path.splitext(out_file)
        new_file = os.path.join(output_path, f"{yt.title}.mp3")
        os.rename(out_file, new_file)

        print(f"Audio descargado en: {new_file}")
        return new_file
    except Exception as e:
        print(f"Error al descargar el audio: {e}")
        return None

def transcribe_with_groq(audio_path):
    """Transcribe un archivo de audio usando la API de Groq (Whisper Large v3)."""
    try:
        with open(audio_path, "rb") as f:
            transcription = cliente_groq.audio.transcriptions.create(
                file=f,
                model="whisper-large-v3"
            )
        os.remove(audio_path)
        return transcription.text
    except Exception as e:
        print(f"Error al transcribir: {e}")
        os.remove(audio_path)
        return None

@bot.message_handler(commands=['start'], chat_types=["private"])
def send_welcome(message):
	# Responde con un mensaje de bienvenida
	bot.send_chat_action(message.chat.id, "typing")
	bot.reply_to(message, "¡Hola! Soy Gamma Academy, un bot IA. Pregúntame algo y responderé usando IA o mi base de datos. Usa el comando /empezar 'nombre del quiz' para hacer algun quiz. Usa el comando /cursos para ver cuales estan disponibles.")

@bot.message_handler(content_types=['voice'], chat_types=["private"])
def handle_voice_message(message: tlb.types.Message):
    bot.send_chat_action(message.chat.id, 'typing')
    transcription = trascribe_voice_with_groq(message)
    if not transcription:
        bot.reply_to(message, "❌ Lo siento, no pude transcribir el audio. Por favor, intenta de nuevo.")
        return
    response = get_groq_response(transcription)
    if response:
        bot.reply_to(message, response)
    else:
        error_message = """❌ Lo siento, hubo un error al procesar tu consulta.
Por favor, intenta nuevamente"""
        bot.reply_to(message, error_message)
        return

@bot.message_handler(commands=['help'], chat_types=["private"])
def enviar_ayuda(message):
    """Mensaje de ayuda"""

    texto_ayuda = """
🔧 Comandos disponibles:



/start - Iniciar el bot
/help - Mostrar esta ayuda


📸 ¿Cómo usar el bot?


1. Envía una imagen (foto, dibujo, captura, etc.)
2. Espera unos segundos mientras proceso la imagen
3. Recibirás una descripción detallada de lo que veo


💡 Consejos:
- Las imágenes más claras y nítidas generan mejores descripciones
- Puedo analizar fotos, dibujos, gráficos, capturas de pantalla, etc.
- Respondo en español siempre


❓ ¿Problemas?
Si algo no funciona, intenta enviar la imagen de nuevo."""
    bot.reply_to(message, texto_ayuda)


@bot.message_handler(content_types=['photo'], chat_types=["private"])
def manejar_foto(message):
    """Procesa las imágenes enviadas por el usuario"""
    try:
        bot.reply_to(message, "📸 He recibido tu imagen. Analizándola... ⏳")
        foto = message.photo[-1]
        info_archivo = bot.get_file(foto.file_id)
        archivo_descargado = bot.download_file(info_archivo.file_path)
        imagen_base64 = imagen_a_base64(archivo_descargado)
        if not imagen_base64:
            bot.reply_to(message, "❌ Error al procesar la imagen. Intenta de nuevo.")
            return
        descripcion = describir_imagen_con_groq(imagen_base64)
        if descripcion:
            respuesta = f"🤖 **Descripción de la imagen:**\n\n{descripcion}"
            bot.reply_to(message, respuesta, parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ No pude analizar la imagen. Por favor, intenta con otra imagen.")
    except Exception as e:
        print(f"Error al procesar la imagen: {e}")
        bot.reply_to(message, "❌ Ocurrió un error al procesar tu imagen. Intenta de nuevo.")

@bot.message_handler(func=lambda message: True, chat_types=["private"])
def responder(message):
	pregunta = message.text
	respuesta = buscar_en_dataset(pregunta, dataset)
	if respuesta:
		bot.reply_to(message, respuesta)
	else:
		respuesta_ia = get_groq_response(pregunta)
		bot.reply_to(message, respuesta_ia)
          
#FUNCIONAMIENTO EN GRUPOS
@bot.message_handler(commands=['start'], chat_types=["group", "supergroup"])
def send_welcome_group(message):
    bot.send_chat_action(message.chat.id, "typing")
    bot.reply_to(message, "¡Hola! Soy Gamma Academy, un bot IA. Envie un archivo y creare un quiz basado en su contenido.")

@bot.message_handler(content_types=['document'], chat_types=["group", "supergroup"])
def handle_document(message):
    bot.reply_to(message, f"Recibí tu archivo: {message.document.file_name}, voy a crear un quiz basado en su contenido. ⏳")
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_name = message.document.file_name

    file_path = f"temp/{file_name}"
    os.makedirs("temp", exist_ok=True)
    with open(file_path, 'wb') as f:
        f.write(downloaded_file)

    texto = extraer_texto_de_documento(downloaded_file, file_name)

    quiz = generar_quiz_con_groq(texto, file_name)
    
    try:
        os.remove(file_path)
        print(f"🧹 Archivo temporal eliminado: {file_path}")
    except Exception as e:
        print(f"⚠️ No se pudo eliminar {file_path}: {e}")

    bot.reply_to(message, f"✅ ¡Quiz generado!. Envienme al privado el comando /empezar {quiz} .")

@bot.message_handler(func=lambda message: bool(re.search(r'http[s]?://', message.text or '')), chat_types=["group", "supergroup"])
def handle_link(message):
    bot.reply_to(message, f"Veo que enviaste un link: {message.text}, voy a crear un quiz basado en su contenido. ⏳")
    audio_file = download_audio_from_youtube(message.text)
    if not audio_file:
        return print("No se pudo descargar el audio.")

    text = transcribe_with_groq(audio_file)
    if not text:
        bot.reply_to(message, "❌ No pude transcribir el audio.")
        return
    file_name = os.path.basename(audio_file)
    quiz = generar_quiz_con_groq(text, file_name)
    try:
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"🧹 Archivo temporal eliminado: {audio_file}")
    except Exception as e:
        print(f"⚠️ No se pudo eliminar {audio_file}: {e}")

    bot.reply_to(message, f"✅ ¡Quiz generado!. Envienme al privado el comando /empezar {quiz} .")


# Punto de entrada principal del script
if __name__ == "__main__":
    print("Gamma Academy iniciado. Esperando mensajes...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Error en el bot: {str(e)}")
            print("Reiniciando el bot...")
            time.sleep(5)  # Espera antes de reintentar