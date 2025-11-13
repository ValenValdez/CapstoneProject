# CapstoneProject
Este repositorio contiene el código fuente del bot de Telegram desarrollado para el curso Samsung Innovation Campus (SIC). Este proyecto es de Valentín Valdez, Maia Aramayo y Micaela Cafardo.

🤖 Gamma Academy - Asistente de Capacitación y Visión AI
📋 Descripción
Gamma Academy es un bot de Telegram diseñado como un Asistente Virtual de Capacitación Interna basado en la arquitectura RAG (Retrieval-Augmented Generation) y herramientas de Visión Artificial Multimodal.

Su objetivo principal es responder de manera profesional y precisa las preguntas de los empleados sobre la organización, sus políticas y procesos, utilizando una Base de Conocimiento (JSON) y la potencia de la IA. Además, permite generar quizzes interactivos a partir de documentos y evaluar respuestas complejas (voz e imagen) mediante modelos avanzados de Groq.

El sistema almacena el progreso de los usuarios y permite la exportación de resultados a Excel para un seguimiento gerencial efectivo.

✨ Características Principales
📚 RAG Integrado: Respuestas exactas y profesionales obtenidas de una Base de Datos local (JSON) y complementadas por un Large Language Model (LLM).

📝 Generación de Quizzes: Crea automáticamente evaluaciones de 5 preguntas a partir de archivos subidos (PDF, DOCX, TXT) o enlaces de YouTube, usando Groq (LLM).

🎤 Reconocimiento de Voz (STT): Transcribe mensajes de voz usando la API de Groq (Whisper) para procesar tanto consultas de chat como respuestas a preguntas de quiz.

📸 Visión Artificial (Vision AI): Describe e interpreta imágenes enviadas (fotos, gráficos) usando un modelo multimodal de Groq (Llama 4 Scout), lo cual permite la evaluación automática de respuestas visuales en los quizzes.

🎯 Evaluación Multimodal: Evalúa respuestas de tipo texto (opción múltiple), voz e imagen comparando el input del usuario con la respuesta esperada por la IA.

📊 Análisis de Sentimiento: Clasifica el feedback del usuario al finalizar cada quiz (Muy Positivo, Negativo, etc.) usando BERT Multilingüe.

📈 Exportación de Resultados: Genera un archivo .xlsx (Excel) con los resultados de un quiz específico para seguimiento y auditoría.

🚀 Instalación
Requisitos Previos
Python 3.10 o superior.

Cuenta de Telegram.

API Token de Telegram Bot (obtener de @BotFather).

API Key de Groq.

1. Clonar el Repositorio
Bash

git clone <URL_DE_TU_REPOSITORIO>
cd gamma-academy
2. Crear Entorno Virtual
Bash

python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
3. Instalar Dependencias
Instala todas las librerías necesarias para el manejo de Telegram, IA, y documentos:

Bash

pip install -r requirements.txt
requirements.txt:

python-dotenv
pyTelegramBotAPI
groq
transformers
torch
pandas
PyPDF2
python-docx
pytubefix
Pillow
4. Configurar Variables de Entorno
Crear archivo .env en la raíz del proyecto:

TELEGRAM_BOT_TOKEN=tu_token_de_telegram
GROQ_API_KEY=tu_api_key_de_groq
DATASET_PATH=data/dataset.json
(Asegúrate de que la ruta DATASET_PATH apunte a tu archivo de preguntas y respuestas internas).

5. Ejecutar el Bot
Bash

python BOT_final.py
