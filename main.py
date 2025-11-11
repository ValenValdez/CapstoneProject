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
import manejo_de_quizzes as mdq
import datetime
import pandas as pd
import html

load_dotenv()

TOKEN_BOT_TELEGRAM = os.getenv('TELEGRAM_BOT_TOKEN')
CLAVE_API_GROQ = os.getenv('GROQ_API_KEY')
DATASET_PATH = os.getenv('DATASET_PATH')
manejador_quizzes = mdq.ManejadorQuizzes()

try:
    print("Cargando el modelo de análisis de sentimiento...")
    analizador_sentimiento = pipeline(
        "sentiment-analysis",
        model="nlptown/bert-base-multilingual-uncased-sentiment" 
    )
    print("✅ Modelo de sentimiento cargado con éxito.")
except Exception as e:
    print(f"❌ Error al cargar el modelo de sentimiento: {e}. Se desactivará el análisis de feedback.")
    analizador_sentimiento = None # Usamos None para manejar fallas

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
        system_prompt = f"""Eres Gamma Academy, un asistente virtual de capacitación interna diseñado para ayudar a los empleados de una empresa.

        Funcionalidades Clave del Bot (Tu conocimiento):
        * Capacidad de crear quizzes a partir de archivos (PDF, DOCX) y enlaces de YouTube.
        * Capacidad de evaluar respuestas de quizzes de texto (botones), voz (transcripción) e imagen (descripción visual).
        * Capacidad de exportar resultados finales de un quiz específico a un archivo Excel (.xlsx).
        * Capacidad de realizar análisis de sentimiento del feedback del usuario al finalizar un quiz.

        Comandos disponibles:
        * /start: Mensaje de bienvenida.
        * /empezar [nombre]: Inicia un quiz específico en el chat privado.
        * /cursos: Muestra la lista de todos los quizzes disponibles.
        * /exportar [nombre]: Exporta los resultados finales de un quiz específico a Excel.

        Reglas y Tono:
        1. Responde preguntas generales, conversacionales y sobre las **Funcionalidades Clave** de esta plataforma.
        2. Utiliza siempre un tono amable, profesional y formal. Sé conciso y directo.
        3. Si la pregunta está fuera del contexto de capacitación o es personal, responde: 'Mi función es asistir en temas de capacitación y aprendizaje interno.'
        4. NO inventes ni agregues información. Si la pregunta requiere datos específicos no cubiertos, indícalo educadamente.
        5. NO utilices emojis ni lenguaje coloquial.
        6. Cuando el usuario pida un quiz o evaluación, genera entre 3 y 5 preguntas cortas. No incluyas respuestas.
        7. Si el usuario solicita modificar, actualizar o agregar información al bot, responde que no tienes permisos.
        """


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


def transcribe_voice_with_groq(message: tlb.types.Message) -> Optional[str]:
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        temp_file = "temp_voice.ogg"


        #guardar el archivo de forma temporal
        with open(temp_file, "wb") as f:
            f.write(downloaded_file)
        with open(temp_file, "rb") as file:
            transcription = cliente_groq.audio.transcriptions.create(
                file = (temp_file, file.read()),
                model = "whisper-large-v3-turbo",
                prompt=(
                    "La persona está respondiendo una pregunta de un examen en español. "
                    "La transcripción debe conservar palabras clave importantes, "
                    "nombres propios y tecnicismos. "
                    "Ignora muletillas o repeticiones."
                ),
                response_format = "text",
                language= "es",
                temperature = 0.2
            )
        os.remove(temp_file)
        return transcription.strip()
   
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
    Generá un quiz de 5 preguntas basadas en el siguiente texto.

    Cada pregunta debe ser de uno de los siguientes tipos:
    - "text": pregunta de opción múltiple con cuatro opciones (a, b, c, d) y una respuesta correcta.
    - "photo": pregunta que requiera que el usuario envíe una imagen como respuesta (por ejemplo, "Envía una foto que muestre...").
    - "voice": pregunta que requiera una respuesta hablada (por ejemplo, "Explica brevemente...").

    Formato del JSON:
    [
    {{
        "pregunta": "¿Qué cursos están disponibles?",
        "opciones": ["Curso A", "Curso B", "Curso C", "Curso D"],
        "respuesta_correcta": "a",
        "tipo_respuesta": "text"
    }},
    {{
        "pregunta": "Muestra un ejemplo de una escena de trabajo en equipo.",
        "opciones": [],
        "respuesta_correcta": "",
        "tipo_respuesta": "photo"
    }}
    ]

    Reglas:
    - No incluyas texto extra ni explicaciones fuera del JSON.
    - Usa español neutro.
    - Siempre genera 5 preguntas.
    - Las preguntas de tipo 'photo' o 'voice' no deben tener opciones.
    - Las preguntas 'text' deben tener exactamente 4 opciones (a, b, c, d).
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

    # Registrar el nuevo quiz en el manejador en memoria para evitar reiniciar el bot
    quiz_key = os.path.splitext(os.path.basename(ruta))[0].lower()
    try:
        manejador_quizzes.quizzes_cargados[quiz_key] = ruta

        # Recarga el quiz recién creado
        nuevo_quiz = mdq.Quiz(quiz_key, ruta)
        manejador_quizzes.quizzes_cargados[quiz_key] = ruta

    except Exception as e:
        print(f"No se pudo registrar o recargar el quiz en el manejador: {e}")

    print(f"\n✅ QUIZ GENERADO: {ruta}\n")
    return quiz_key


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
                model="whisper-large-v3-turbo",
                language="es",
                prompt = "Especificar contexto o pronunciacion, responder siempre en idioma español independientemente del idioma del audio",
            )
        os.remove(audio_path)
        return transcription.text
    except Exception as e:
        print(f"Error al transcribir: {e}")
        os.remove(audio_path)
        return None
def enviar_siguiente_pregunta(bot, chat_id: int, pregunta: mdq.Pregunta):
    # Obtener el texto de la pregunta con las instrucciones específicas
    mensaje = pregunta.formato_para_telegram()
    
    if pregunta.tipo_respuesta == 'text':
        # Crear Inline Keyboard para preguntas textuales (opción múltiple)
        markup = tlb.types.InlineKeyboardMarkup()
        for i, opcion in enumerate(pregunta.opciones):
            callback_data = f"quiz_ans|{chr(97 + i)}"
            markup.add(tlb.types.InlineKeyboardButton(opcion, callback_data=callback_data))
        
        bot.send_message(chat_id, mensaje, reply_markup=markup, parse_mode='Markdown')
        
    elif pregunta.tipo_respuesta in ('voice', 'photo'):
        # Solo enviamos el mensaje de instrucciones.
        bot.send_message(chat_id, mensaje, parse_mode='Markdown')

def procesar_avance_quiz(bot, chat_id, message_or_call_message, user: tlb.types.User, es_correcta: bool):
    nombre_quiz = "desconocido"
    sesion_previa = manejador_quizzes.sesiones_activas.get(chat_id)
    if sesion_previa:
        nombre_quiz = sesion_previa['quiz'].nombre
    siguiente_pregunta, es_fin_de_quiz, estado_final = manejador_quizzes.avanzar_pregunta(chat_id, es_correcta)

    if es_fin_de_quiz:
        puntaje = estado_final['puntaje']
        total = estado_final['total']
        
        try:
            guardar_resultado(nombre_quiz, user, puntaje, total)
        except Exception as e:
            print(f"⚠️ Error al llamar a guardar_resultado: {e}")
        mensaje_final = f"🎉 **¡Quiz finalizado!** 🎉\n\nTu puntaje final es: **{puntaje} de {total}**."
        
        # Distinguimos si responder a un mensaje (reply) o enviar uno nuevo (si era botón)
        if hasattr(message_or_call_message, 'reply_to_message'):
            bot.reply_to(message_or_call_message, mensaje_final, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, mensaje_final, parse_mode='Markdown')
        msg = bot.send_message(chat_id, "¿Qué opinas del bot? Tu feedback es valioso para mejorar.")
        
        # 2. Registrar el handler para la siguiente respuesta del usuario
        bot.register_next_step_handler(msg, manejar_feedback_final)
        return
    
    else:
        # Si no terminó, mandamos la siguiente
        bot.send_message(chat_id, "✅ Respuesta recibida. Siguiente pregunta:")
        enviar_siguiente_pregunta(bot, chat_id, siguiente_pregunta)

def manejar_feedback_final(message):
    chat_id = message.chat.id
    feedback_texto = message.text.strip()
    user = message.from_user
    
    bot.send_chat_action(chat_id, "typing")
    
    if not analizador_sentimiento:
        bot.send_message(chat_id, "¡Gracias por tu feedback! Lamentablemente, la función de análisis de sentimiento está desactivada.")
        return
        
    try:
        resultado = analizador_sentimiento([feedback_texto])[0]
        sentimiento_raw = resultado['label']
        confianza = resultado['score']

        emoji = "😐"
        sentimiento_formal = "NEUTRAL"
        
        if sentimiento_raw == '5 stars':
            emoji = "😊"
            sentimiento_formal = "MUY POSITIVO"
        elif sentimiento_raw == '4 stars':
            emoji = "🙂"
            sentimiento_formal = "POSITIVO"
        elif sentimiento_raw == '3 stars':
            emoji = "😐"
            sentimiento_formal = "NEUTRAL"
        elif sentimiento_raw == '2 stars':
            emoji = "😟"
            sentimiento_formal = "NEGATIVO"
        elif sentimiento_raw == '1 star':
            emoji = "😠"
            sentimiento_formal = "MUY NEGATIVO"

        mensaje_respuesta = (
            f"¡Gracias por tu feedback, **{user.first_name}**! Lo valoramos mucho.\n\n"
            f"Hemos clasificado tu opinión como **{sentimiento_formal}** {emoji} "
            f"(Confianza: {confianza:.2%})."
        )
        
        # Opcional: Imprimir en consola para ver la data
        print(f"✅ Feedback de {user.full_name}: '{feedback_texto}' -> {sentimiento_formal}")

    except Exception as e:
        mensaje_respuesta = "Gracias por tu feedback. Ocurrió un error al procesar el análisis de sentimiento."
        print(f"❌ Error durante el análisis de sentimiento: {e}")

    bot.send_message(chat_id, mensaje_respuesta, parse_mode='Markdown')

# === GUARDAR RESULTADOS ===
def guardar_resultado(quiz_name: str, user: tlb.types.User, puntaje_final: int, total_preguntas: int):
    """Guarda el resultado FINAL del quiz en un archivo JSON."""
    os.makedirs("resultados", exist_ok=True)
    ruta = "resultados/resultados_finales.json" 

    registro = {
        "usuario_id": user.id,
        "usuario_nombre": user.full_name,
        "quiz_nombre": quiz_name,
        "puntaje": puntaje_final,
        "total_preguntas": total_preguntas,
        "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        data = []
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.append(registro)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Resultado FINAL guardado en {ruta}")
    except Exception as e:
        print(f"❌ Error al guardar resultado final: {e}")


# === EXPORTAR A EXCEL ===
def exportar_resultados_a_excel(quiz_name: str):
    """Convierte el archivo JSON de resultados finales, filtrando por el nombre del quiz."""
    try:
        ruta_json = "resultados/resultados_finales.json"
        
        if not os.path.exists(ruta_json):
            print("⚠️ No hay archivo de resultados generales para exportar.")
            return None

        df_general = pd.read_json(ruta_json)
        
        if df_general.empty:
            print("⚠️ El archivo de resultados está vacío.")
            return None
        df_filtrado = df_general[df_general['quiz_nombre'] == quiz_name]
        
        if df_filtrado.empty:
            print(f"⚠️ No se encontraron resultados para el quiz: {quiz_name}")
            return None

        os.makedirs("resultados", exist_ok=True) 
        
        # El nombre del archivo de salida incluye el nombre del quiz
        ruta_excel = f"resultados/resultados_{quiz_name}.xlsx"
        df_filtrado.to_excel(ruta_excel, index=False)
        
        print(f"📊 Resultados exportados para '{quiz_name}' en {ruta_excel}")
        return ruta_excel
        
    except Exception as e:
        print(f"❌ Error al exportar a Excel: {e}")
        return None

def escapar_html(text: str) -> str:
    """Escapa los caracteres especiales para ser interpretados como texto plano en HTML."""
    return html.escape(text)

#===========================HANDLERS DEL BOT===========================
#FUNCIONAMIENTO EN PRIVADO
@bot.message_handler(commands=['start'], chat_types=["private"])
def send_welcome(message):
	# Responde con un mensaje de bienvenida
	bot.send_chat_action(message.chat.id, "typing")
	bot.reply_to(message, "¡Hola! Soy Gamma Academy, un bot IA. Pregúntame algo y responderé usando IA o mi base de datos. Usa el comando /empezar 'nombre del quiz' para hacer algun quiz. Usa el comando /cursos para ver cuales estan disponibles.")

@bot.message_handler(commands=['empezar'], chat_types=["private"])
def empezar_quiz(message):
    bot.send_chat_action(message.chat.id, "typing")
    chat_id = message.chat.id
    
    partes = message.text.split(maxsplit=1) 
    if len(partes) < 2:
        bot.reply_to(message, "⚠️ Falta el nombre del quiz. Usa: `/empezar nombre_del_quiz`")
        return

    nombre_quiz = partes[1].strip()
    primera_pregunta = manejador_quizzes.iniciar_quiz(chat_id, nombre_quiz)

    if primera_pregunta:
        bot.send_message(chat_id, f"✅ ¡Quiz '{nombre_quiz}' iniciado!")
        enviar_siguiente_pregunta(bot, chat_id, primera_pregunta)
    else:
        bot.reply_to(message, f"❌ No se pudo iniciar el quiz **'{nombre_quiz}'**. Revisa que el nombre sea correcto.")

@bot.message_handler(content_types=['voice'], chat_types=["private"])
def manejar_respuesta_voz_quiz(message: tlb.types.Message):
    chat_id = message.chat.id
    tipo_esperado = manejador_quizzes.obtener_tipo_esperado(chat_id)

    if tipo_esperado == 'voice':
        bot.send_chat_action(chat_id, "typing")
        transcription = transcribe_voice_with_groq(message)
        if not transcription:
         bot.reply_to(message, "❌ Lo siento, no pude transcribir el audio. Por favor, intenta de nuevo.")
         return
        sesion = manejador_quizzes.sesiones_activas.get(chat_id)
        quiz_actual = sesion['quiz']
        pregunta_actual = quiz_actual.get_pregunta(sesion['indice_actual'])
        prompt = f"""
        Evalúa la siguiente respuesta de un usuario a una pregunta oral.

        Debes responder con JSON del siguiente formato:
        {{"correcta": true/false, "razon": "explicación breve"}}

        Pregunta: {pregunta_actual.pregunta}
        Respuesta esperada: {pregunta_actual.respuesta_correcta}
        Respuesta del usuario: {transcription}

        Criterio:
        - Considera la respuesta correcta si comunica la misma idea general aunque use otras palabras.
        - Considera incorrecta si no aborda el tema o contradice la respuesta esperada.
        - Evalúa solo el contenido, no el tono ni la gramática.
        """

        evaluacion = cliente_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=150
        )

        texto_eval = evaluacion.choices[0].message.content.strip()
        try:
            resultado = json.loads(re.search(r'\{.*\}', texto_eval).group(0))
            es_correcta = resultado.get("correcta", False)
            razon = resultado.get("razon", "")
        except:
            es_correcta = "true" in texto_eval.lower()
            razon = ""

        feedback = "✅ ¡Correcto!" if es_correcta else "❌ Incorrecto."
        bot.reply_to(message, f"{feedback}\n\n Tu respuesta: _{transcription}_\n💬 {razon}", parse_mode="Markdown")
        procesar_avance_quiz(bot, chat_id, message, message.from_user, es_correcta)
        return
    pass

@bot.message_handler(content_types=['photo'], chat_types=["private"])
def manejar_respuesta_imagen_quiz(message: tlb.types.Message):
    chat_id = message.chat.id
    tipo_esperado = manejador_quizzes.obtener_tipo_esperado(chat_id)

    if tipo_esperado == 'photo':
        bot.send_chat_action(chat_id, "typing")
        foto = message.photo[-1]
        info_archivo = bot.get_file(foto.file_id)
        archivo_descargado = bot.download_file(info_archivo.file_path)
        imagen_base64 = imagen_a_base64(archivo_descargado)
        if not imagen_base64:
            bot.reply_to(message, "❌ Error al procesar la imagen. Intenta de nuevo.")
            return
        descripcion = describir_imagen_con_groq(imagen_base64)
        if not descripcion:
            bot.reply_to(message, "❌ No pude analizar la imagen. Por favor, intenta con otra imagen.")
            return
        
        sesion = manejador_quizzes.sesiones_activas.get(chat_id)
        quiz_actual = sesion['quiz']
        pregunta_actual = quiz_actual.get_pregunta(sesion['indice_actual'])

        prompt = f"""
        INSTRUCCIÓN CLAVE: Responde ÚNICAMENTE con la palabra 'True' o con la palabra 'False'. No agregues comillas, explicación, saludos, puntuación ni ningún texto adicional.
        INSTRUCCIÓN CLAVE: NO utilices asteriscos (*), guiones bajos (_) ni ningún otro carácter para dar formato. Responde ÚNICAMENTE con texto plano.
        Evalúa si la imagen del usuario (descrita abajo) cumple correctamente la consigna.

        Pregunta: {pregunta_actual.pregunta}
        Respuesta esperada: {pregunta_actual.respuesta_correcta}
        Descripción de la imagen enviada por el usuario: {descripcion}
        """

        evaluacion = cliente_groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0, # Usar temperatura baja ayuda a la estrictez
        max_tokens=5 # Aseguramos que solo dé una palabra
    )
        evaluacion_texto = evaluacion.choices[0].message.content.strip().lower()
        es_correcta = "true" in evaluacion_texto
        feedback = "✅ ¡Correcto!" if es_correcta else "❌ Incorrecto."
        descripcion_segura = escapar_html(descripcion)
        bot.reply_to(message, f"{feedback}\n\nDescripción de tu imagen: {descripcion_segura}", parse_mode="HTML")
        procesar_avance_quiz(bot, chat_id, message, message.from_user, es_correcta)
        return
    pass

@bot.callback_query_handler(func=lambda call: call.data.startswith('quiz_ans'))
def manejar_respuesta_quiz(call):
    chat_id = call.message.chat.id
    sesion = manejador_quizzes.sesiones_activas.get(chat_id)

    if not sesion or sesion['tipo_esperado'] != 'text':
        bot.answer_callback_query(call.id, "El quiz no está activo.")
        return

    quiz_actual = sesion['quiz']
    pregunta_actual = quiz_actual.get_pregunta(sesion['indice_actual'])
    respuesta_usuario = call.data.split('|')[1] 
    es_correcta = pregunta_actual.es_correcta(respuesta_usuario)

    feedback = "✅ ¡Correcto!" if es_correcta else "❌ Incorrecto."
    explicacion = ""
    if not es_correcta:
        prompt_explicacion = f"""
        El usuario respondió incorrectamente la siguiente pregunta de un quiz educativo.
        Explica brevemente (en no más de 3 líneas) por qué la respuesta correcta es la adecuada,
        de forma amable y pedagógica, en español neutro.

        Pregunta: {pregunta_actual.pregunta}
        Opciones: {pregunta_actual.opciones}
        Respuesta correcta: {pregunta_actual.respuesta_correcta}
        """
        try:
            explicacion_response = cliente_groq.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[{"role": "user", "content": prompt_explicacion}],
                temperature=0.4,
                max_tokens=100
            )
            explicacion = "\n\n💡 " + explicacion_response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ Error al generar explicación: {e}")

    try:
        texto_original = call.message.text
        opcion_elegida = respuesta_usuario.upper() 
        texto_modificado = f"{texto_original}\n\n**Tu respuesta:** {opcion_elegida}\n\n{feedback}{explicacion}"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=texto_modificado,
            reply_markup=None, 
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error al editar mensaje de callback: {e}")

    bot.answer_callback_query(call.id, feedback)
    procesar_avance_quiz(bot, chat_id, call.message, call.from_user, es_correcta)

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

#Funcionamiento en publico y en privado
# === COMANDO PARA EXPORTAR ===
@bot.message_handler(commands=['exportar'])
def exportar_resultados(message):
    bot.send_chat_action(message.chat.id, "typing")
    partes = message.text.split(maxsplit=1) 
    if len(partes) < 2:
        bot.reply_to(message, "⚠️ Falta el nombre del quiz. Usa: `/exportar nombre_del_quiz`")
        return

    nombre_quiz_a_exportar = partes[1].strip()
    ruta_excel = exportar_resultados_a_excel(nombre_quiz_a_exportar)
    if ruta_excel and os.path.exists(ruta_excel):
        with open(ruta_excel, "rb") as f:
            nombre_archivo = f"resultados_{nombre_quiz_a_exportar}.xlsx"
            bot.send_document(message.chat.id, f, visible_file_name=nombre_archivo)
        try:
            os.remove(ruta_excel)
            print(f"🗑️ Archivo temporal borrado: {ruta_excel}")
        except Exception as e:
            print(f"❌ Error al borrar el archivo {ruta_excel}: {e}")
    else:
        bot.reply_to(message, f"⚠️ No hay resultados para el quiz \"{nombre_quiz_a_exportar}\" o el archivo no pudo ser creado.")

@bot.message_handler(commands=['cursos'])
def mostrar_cursos_disponibles(message):
    bot.send_chat_action(message.chat.id, "typing")
    chat_id = message.chat.id
    
    # Obtenemos la lista de nombres de quizzes cargados
    cursos = manejador_quizzes.quizzes_cargados.keys()
    
    if cursos:
        # Generamos una lista numerada
        lista_cursos = "\n".join([f"• {nombre.upper()}" for nombre in sorted(cursos)])
        
        mensaje = (
            "📚 **Cursos disponibles (Quizzes):**\n\n"
            f"{lista_cursos}\n\n"
            "Para empezar uno, usa el comando:\n"
            "`/empezar nombre_del_quiz`"
        )
    else:
        mensaje = "⚠️ Por el momento, no hay quizzes/cursos disponibles. Genera uno con un archivo o link de YouTube."
        
    bot.send_message(chat_id, mensaje, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True, chat_types=["private"])
def responder_a_texto_general(message):
    chat_id = message.chat.id
    tipo_esperado_quiz = manejador_quizzes.obtener_tipo_esperado(chat_id)
    if tipo_esperado_quiz in ('voice', 'photo'):
        return 
    
    pregunta = message.text
    bot.send_chat_action(chat_id, "typing")

    respuesta = buscar_en_dataset(pregunta, dataset) 

    if respuesta:
        bot.reply_to(message, respuesta)
    else:
        respuesta_ia = get_groq_response(pregunta)
        if respuesta_ia:
            bot.reply_to(message, respuesta_ia)
        else:
            bot.reply_to(message, "Lo siento, no pude encontrar una respuesta ni generar una con la IA.")

#FUNCIONAMIENTO EN GRUPOS
@bot.message_handler(commands=['start'], chat_types=["group", "supergroup"])
def send_welcome_group(message):
    bot.send_chat_action(message.chat.id, "typing")
    bot.reply_to(message, "¡Hola! Soy Gamma Academy, un bot IA. Envie un archivo o un video de Youtube y creare un quiz basado en su contenido.")

archivos_pendientes = {}  # Estructura separada para no interferir con sesiones de quizzes en privado
@bot.message_handler(content_types=['document'], chat_types=["group", "supergroup"])
def handle_document(message):
    """Recibe un archivo en grupo y pide el nombre del quiz."""
    chat_id = message.chat.id
    file_name = message.document.file_name

    bot.reply_to(
        message,
        f"📄 Recibí tu archivo: *{file_name}*.\n\nPor favor, respondé con el nombre que querés para el quiz.",
        parse_mode='Markdown'
    )

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    os.makedirs("temp", exist_ok=True)
    temp_path = f"temp/{file_name}"
    with open(temp_path, 'wb') as f:
        f.write(downloaded_file)

    # Guardar estado del chat
    archivos_pendientes[chat_id] = {
        "tipo": "documento",
        "archivo": temp_path,
        "esperando_nombre": True
    }


@bot.message_handler(func=lambda m: bool(re.search(r'http[s]?://', m.text or '')), chat_types=["group", "supergroup"])
def handle_youtube_link(message):
    """Recibe un link de YouTube y pide el nombre del quiz."""
    chat_id = message.chat.id
    link = message.text.strip()

    bot.reply_to(
        message,
        f"🎥 Recibí tu link de YouTube:\n{link}\n\nPor favor, respondé con el nombre que querés para el quiz.",
        parse_mode='Markdown'
    )

    # Guardar estado del chat
    archivos_pendientes[chat_id] = {
        "tipo": "youtube",
        "link": link,
        "esperando_nombre": True
    }

@bot.message_handler(func=lambda m: m.chat.type in ["group", "supergroup"])
def recibir_nombre_quiz(message):
    """Recibe el nombre elegido por el usuario y genera el quiz."""
    chat_id = message.chat.id
    sesion = archivos_pendientes.get(chat_id)

    if not sesion or not sesion.get("esperando_nombre"):
        return  # si no está esperando nombre, no hace nada

    nombre_quiz = message.text.strip().replace(" ", "_")
    bot.send_message(
        chat_id,
        f"✏️ Nombre elegido: *{nombre_quiz}*\n\nGenerando el quiz... ⏳",
        parse_mode='Markdown'
    )

    try:
        tipo = sesion["tipo"]

        if tipo == "documento":
            temp_path = sesion["archivo"]
            texto = extraer_texto_de_documento(open(temp_path, "rb").read(), os.path.basename(temp_path))

            if not texto.strip():
                bot.send_message(chat_id, "⚠️ No se pudo extraer texto del documento.")
                return

            quiz_key = generar_quiz_con_groq(texto, nombre_quiz)
            os.remove(temp_path)

        elif tipo == "youtube":
            link = sesion["link"]
            audio_file = download_audio_from_youtube(link)
            if not audio_file:
                bot.send_message(chat_id, "❌ No se pudo descargar el audio de YouTube.")
                return

            text = transcribe_with_groq(audio_file)
            if not text or not text.strip():
                bot.send_message(chat_id, "❌ No se pudo transcribir el audio.")
                return

            quiz_key = generar_quiz_con_groq(text, nombre_quiz)

            if os.path.exists(audio_file):
                os.remove(audio_file)

        # Limpiar estado
        archivos_pendientes.pop(chat_id, None)
        bot.send_message(
            chat_id,
            f"✅ ¡Quiz *{nombre_quiz}* generado!\n\nEnvienme al privado el comando:\n\n`/empezar {quiz_key}`",
            parse_mode='Markdown'
        )
        bot.send_message(
            chat_id,
            f"💡 Cuando se desee exportar los resultados del quiz escriba el comando\n\n`/exportar {quiz_key}`",
            parse_mode='Markdown'
        )

    except Exception as e:
        print(f"Error al generar el quiz: {e}")
        bot.send_message(chat_id, f"❌ Ocurrió un error al generar el quiz: {e}")


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
