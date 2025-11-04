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
from PIL import Image
from pytubefix import YouTube
from groq import Groq
from dotenv import load_dotenv

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

# Handler para los comandos /start y /help
@bot.message_handler(commands=['start'])
def send_welcome(message):
	# Responde con un mensaje de bienvenida
	bot.send_chat_action(message.chat.id, "typing")
	bot.reply_to(message, "¡Hola! Soy Gamma Academy, un bot IA. Pregúntame algo y responderé usando IA o mi base de datos. Usa el comando /empezar 'nombre del quiz' para hacer algun quiz. Usa el comando /cursos para ver cuales estan disponibles.")


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

@bot.message_handler(content_types=['voice'])
def handle_voice_message(message: tlb.types.Message):

    # Enviar mensaje de "escribiendo..."
    bot.send_chat_action(message.chat.id, 'typing')


    # Transcribir el mensaje de voz usando Groq
    transcription = trascribe_voice_with_groq(message)


    if not transcription:
        bot.reply_to(message, "❌ Lo siento, no pude transcribir el audio. Por favor, intenta de nuevo.")
        return


    # Obtener respuesta de Groq usando la transcripción como input
    response = get_groq_response(transcription)
    if response:
        bot.reply_to(message, response)
    else:
        error_message = """❌ Lo siento, hubo un error al procesar tu consulta.
Por favor, intenta nuevamente"""
        bot.reply_to(message, error_message)

# Comentario que indica que se definirá una función para convertir imágenes
# Función para convertir imagen a base64


# Define una función llamada 'imagen_a_base64'
# Acepta un parámetro llamado 'ruta_o_bytes_imagen' que puede ser una ruta de archivo o bytes
def imagen_a_base64(ruta_o_bytes_imagen):
    """Convierte una imagen a base64 para enviarla a Groq"""
    try:
        if isinstance(ruta_o_bytes_imagen, bytes):
            # Comentario explicativo para cuando el parámetro es de tipo bytes
            # Si es bytes, convertir directamente
           
            # base64.b64encode() toma bytes y los codifica en base64 (retorna bytes)
            # .decode('utf-8') convierte esos bytes codificados en una cadena de texto
            # return finaliza la función y devuelve el valor al código que la llamó
            return base64.b64encode(ruta_o_bytes_imagen).decode('utf-8')
       
        # Else se ejecuta si la condición del if es False
        # Es decir, cuando ruta_o_bytes_imagen NO es bytes (presumiblemente es una ruta de archivo)
        else:
            # Comentario explicativo para cuando el parámetro es una ruta de archivo
            # Si es un path, leer el archivo
           
            # open() abre un archivo
            # Primer argumento: la ruta del archivo a abrir
            # "rb" significa: r = read (lectura), b = binary (modo binario)
            # 'as archivo_imagen' asigna el objeto archivo a la variable archivo_imagen
            # 'with' garantiza que el archivo se cierre automáticamente al terminar el bloque
            with open(ruta_o_bytes_imagen, "rb") as archivo_imagen:
                # archivo_imagen.read() lee todo el contenido del archivo y retorna bytes
                # base64.b64encode() codifica esos bytes a base64
                # .decode('utf-8') convierte el resultado a string
                # return devuelve el string base64 y finaliza la función
                return base64.b64encode(archivo_imagen.read()).decode('utf-8')
   
    # except captura cualquier excepción (error) que ocurra en el bloque try
    # 'Exception' es la clase base de todas las excepciones en Python
    # 'as e' guarda la información del error en la variable 'e'
    except Exception as e:
        # print() muestra texto en la consola
        # f"..." es un f-string que permite insertar variables usando {variable}
        # Imprime un mensaje de error junto con los detalles del error capturado
        print(f"Error al convertir imagen a base64: {e}")
       
        # return None finaliza la función y devuelve None
        # Esto indica al código que llama a la función que hubo un error
        return None

def describir_imagen_con_groq(imagen_base64):
    # Docstring que describe el propósito de la función
    """Envía la imagen a Groq y obtiene la descripción"""
   
    # Inicia un bloque try para manejar posibles errores al comunicarse con la API
    try:
        completado_chat = cliente_groq.chat.completions.create(
            messages=[
                {
                    "role": "user",
                   
                    # Clave 'content': contiene el contenido del mensaje
                    # Valor: una lista que puede incluir texto, imágenes, etc.
                    "content": [
                        # Primer elemento de la lista: un diccionario con texto
                        {
                            # Indica que este elemento es de tipo texto
                            "type": "text",
                           
                            # El contenido textual es el prompt que instruye al modelo
                            # Le indica que debe describir la imagen en español con detalle
                            # Especifica qué elementos debe incluir en la descripción
                            "text": "Por favor, describe esta imagen de manera detallada y clara en español. Incluye todos los elementos importantes que veas, colores, objetos, personas, acciones, emociones, y cualquier detalle relevante que puedas observar."
                        # Cierra el diccionario del primer elemento (texto)
                        },
                        # Segundo elemento de la lista: un diccionario con la imagen
                        {
                            # Indica que este elemento es una URL de imagen
                            "type": "image_url",
                           
                            # Clave 'image_url': contiene la configuración de la imagen
                            "image_url": {
                                # Clave 'url': la URL de la imagen
                                # f"..." es un f-string que permite insertar variables
                                # Crea una data URL con el formato: data:[tipo];base64,[datos]
                                # data:image/jpeg;base64, es el prefijo estándar para imágenes base64
                                # {imagen_base64} inserta la imagen codificada en base64
                                # Esto permite enviar la imagen directamente en la URL sin necesidad de un servidor
                                "url": f"data:image/jpeg;base64,{imagen_base64}"
                            # Cierra el diccionario image_url
                            }
                        # Cierra el diccionario del segundo elemento (imagen)
                        }
                    # Cierra la lista 'content'
                    ]
                # Cierra el diccionario del mensaje
                }
            # Cierra la lista 'messages'
            ],
           
            # Parámetro 'model': especifica qué modelo de IA usar
            # "llama-3.2-11b-vision-preview" es un modelo de Llama 3.2
            # 11b = 11 mil millones de parámetros
            # vision = puede procesar y entender imágenes
            # preview = versión preliminar del modelo
            model= "meta-llama/llama-4-scout-17b-16e-instruct",
           
            # Parámetro 'temperature': controla la aleatoriedad/creatividad de las respuestas
            # Rango: 0.0 a 2.0
            # 0.0 = muy determinista, siempre respuestas similares
            # 2.0 = muy aleatorio/creativo
            # 0.7 = equilibrio entre consistencia y creatividad
            temperature=0.7,
           
            # Parámetro 'max_tokens': límite máximo de tokens en la respuesta
            # Un token es aproximadamente una palabra o parte de una palabra
            # 1000 tokens ≈ 750 palabras en español
            # Limita la longitud de la descripción generada
            max_tokens=1000
        # Cierra la llamada al método .create()
        )
       
        # Línea en blanco para mejorar la legibilidad del código
       
        # Accede al resultado de la API:
        # completado_chat es el objeto completo de respuesta
        # .choices es una lista de posibles respuestas generadas
        # [0] obtiene la primera respuesta (índice 0)
        # .message accede al objeto mensaje de esa respuesta
        # .content obtiene el contenido textual del mensaje (la descripción)
        # return devuelve ese contenido y finaliza la función
        return completado_chat.choices[0].message.content
       
    # except captura cualquier excepción que ocurra al hacer la petición a Groq
    # Puede ser: error de red, API key inválida, límite de uso excedido, etc.
    # 'as e' guarda la información del error en la variable e
    except Exception as e:
        # Imprime en consola un mensaje de error descriptivo
        # El f-string inserta los detalles del error capturado
        print(f"Error al describir imagen con Groq: {e}")
       
        # Retorna None para indicar que la operación falló
        # Permite al código que llama esta función saber que no se obtuvo descripción
        return None

@bot.message_handler(commands=['help'])

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


@bot.message_handler(content_types=['photo'])
def manejar_foto(message):
    # Docstring que documenta la función
    """Procesa las imágenes enviadas por el usuario"""
   
    # Inicia un bloque try para manejar errores durante el procesamiento de la imagen
    try:
        # Comentario explicativo
        # Notificar al usuario que se está procesando
       
        # Envía un mensaje inmediato al usuario confirmando que se recibió la imagen
        # Esto da feedback instantáneo mientras se procesa la imagen (que puede tardar unos segundos)
        # Los emojis hacen el mensaje más amigable y visual
        bot.reply_to(message, "📸 He recibido tu imagen. Analizándola... ⏳")
       
        # Línea en blanco para legibilidad
       
        # Comentario explicativo
        # Obtener la foto de mayor calidad
       
        # mensaje.photo es una lista de objetos PhotoSize
        # Telegram envía automáticamente varias versiones de la misma foto en diferentes resoluciones
        # [-1] obtiene el último elemento de la lista, que siempre es la foto de mayor resolución
        # Se guarda en la variable 'foto'
        foto = message.photo[-1]
       
        # bot.get_file() obtiene información detallada sobre el archivo
        # Recibe como argumento el file_id (identificador único del archivo en Telegram)
        # Retorna un objeto File con información como file_path, file_size, etc.
        # info_archivo contiene la ruta donde Telegram almacenó el archivo
        info_archivo = bot.get_file(foto.file_id)
       
        # Línea en blanco para legibilidad
       
        # Comentario explicativo
        # Descargar la imagen
       
        # bot.download_file() descarga el archivo desde los servidores de Telegram
        # Recibe como argumento la ruta del archivo (obtenida en el paso anterior)
        # Retorna los bytes (contenido binario) del archivo
        # archivo_descargado contiene la imagen completa en memoria como bytes
        archivo_descargado = bot.download_file(info_archivo.file_path)
       
        # Línea en blanco para legibilidad
       
        # Comentario explicativo
        # Convertir a base64
       
        # Llama a la función imagen_a_base64 definida anteriormente
        # Le pasa los bytes de la imagen descargada
        # La función retorna la imagen codificada en base64 (string) o None si hay error
        # El resultado se guarda en imagen_base64
        imagen_base64 = imagen_a_base64(archivo_descargado)
       
        # Línea en blanco para legibilidad
       
        # Estructura condicional que verifica si la conversión falló
        # 'not imagen_base64' es True si imagen_base64 es None, cadena vacía, o False
        if not imagen_base64:
            # Si no se pudo convertir la imagen, envía un mensaje de error al usuario
            # El emoji ❌ indica claramente que hubo un problema
            bot.reply_to(message, "❌ Error al procesar la imagen. Intenta de nuevo.")
           
            # return finaliza la ejecución de la función inmediatamente
            # No se ejecuta ningún código posterior
            # Esto evita intentar procesar una imagen que no se pudo convertir
            return
       
        # Línea en blanco para legibilidad
       
        # Comentario explicativo
        # Describir la imagen con Groq
       
        # Llama a la función describir_imagen_con_groq definida anteriormente
        # Le pasa la imagen en formato base64
        # La función envía la imagen a Groq y obtiene la descripción
        # Retorna el texto de la descripción o None si hay error
        # El resultado se guarda en la variable descripcion
        descripcion = describir_imagen_con_groq(imagen_base64)
       
        # Línea en blanco para legibilidad
       
        # Estructura condicional que verifica si se obtuvo una descripción exitosa
        # 'if descripcion' es True si descripcion contiene texto (no es None, ni vacío)
        if descripcion:
            # Comentario explicativo
            # Enviar la descripción
           
            # Crea el mensaje de respuesta usando un f-string
            # f"..." permite insertar variables con {variable}
            # ** antes y después de texto indica formato negrita en Markdown
            # \n es un salto de línea
            # \n\n son dos saltos de línea (deja una línea en blanco)
            # {descripcion} inserta el texto de la descripción generada por Groq
            respuesta = f"🤖 **Descripción de la imagen:**\n\n{descripcion}"
           
            # Envía la respuesta al usuario
            # Primer argumento: el mensaje original al que responder
            # Segundo argumento: el texto de la respuesta (con la descripción)
            # parse_mode='Markdown': indica a Telegram que interprete el formato Markdown
            # Esto hace que el ** se convierta en negrita, \n en saltos de línea, etc.
            bot.reply_to(message, respuesta, parse_mode='Markdown')
       
        # else se ejecuta si descripcion es None o está vacío (no se obtuvo descripción)
        else:
            # Envía un mensaje de error al usuario indicando que no se pudo analizar
            # Sugiere intentar con otra imagen
            bot.reply_to(message, "❌ No pude analizar la imagen. Por favor, intenta con otra imagen.")
   
    # Línea en blanco (dentro del try, pero después de todo el código principal)        
   
    # except captura cualquier excepción no manejada que ocurra en el bloque try
    # Esto incluye errores de red, timeouts, problemas con la API de Telegram, etc.
    # 'as e' guarda la información del error en la variable e
    except Exception as e:
        # Imprime el error en la consola del servidor para debugging
        # Útil para que el desarrollador vea qué salió mal
        # f"..." inserta la descripción del error con {e}
        print(f"Error al procesar la imagen: {e}")
       
        # Envía un mensaje genérico de error al usuario
        # No incluye detalles técnicos para no confundir al usuario
        # Le sugiere intentar de nuevo
        bot.reply_to(message, "❌ Ocurrió un error al procesar tu imagen. Intenta de nuevo.")

@bot.message_handler(func=lambda message: True)
def responder(message):
	# Obtiene el texto del mensaje recibido
	pregunta = message.text
	# Busca la respuesta en el dataset
	respuesta = buscar_en_dataset(pregunta, dataset)
	if respuesta:
		# Si la encuentra, responde con la respuesta del dataset
        
		bot.reply_to(message, respuesta)
	else:
		# Si no la encuentra, consulta la IA de Groq y responde con la respuesta generada
		respuesta_ia = get_groq_response(pregunta)
		bot.reply_to(message, respuesta_ia)
# Punto de entrada principal del script
if __name__ == "__main__":
    # Imprime un mensaje en consola indicando que el bot está iniciado
    print("Gamma Academy iniciado. Esperando mensajes...")
    # Inicia el polling infinito para recibir mensajes de Telegram
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Error en el bot: {str(e)}")
            print("Reiniciando el bot...")
            time.sleep(5)  # Espera antes de reintentar


#Transcripcion de youtube con Groq


client = Groq(api_key=GROQ_API_KEY)

def download_audio_from_youtube(url, output_path="downloads"):
    """Descarga solo el audio de un video de YouTube y devuelve la ruta del archivo."""
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).first()

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        print(f"Descargando audio de: {yt.title}")
        out_file = stream.download(output_path)
        base, _ = os.path.splitext(out_file)
        new_file = base + ".mp3"
        os.rename(out_file, new_file)

        print(f"Audio descargado en: {new_file}")
        return new_file
    except Exception as e:
        print(f"Error al descargar el audio: {e}")
        return None

def transcribe_with_groq(audio_path):
    """Transcribe un archivo de audio usando la API de Groq (Whisper Large v3)."""
    try:
        print("Transcribiendo con Groq (modelo Whisper-Large-V3)...")
        with open(audio_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=f,
                model="whisper-large-v3"
            )
        print("Transcripción completada.")
        return transcription.text
    except Exception as e:
        print(f"Error al transcribir: {e}")
        return None

def youtube_to_text(url):
    """Descarga el audio, lo transcribe y guarda el texto en un archivo."""
    audio_file = download_audio_from_youtube(url)
    if not audio_file:
        return

    text = transcribe_with_groq(audio_file)
    if text:
        output_file = "transcripcion.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Transcripción guardada en: {output_file}")

if __name__ == "__main__":
    url = input("Pegá el enlace del video de YouTube: ").strip()
    youtube_to_text(url)