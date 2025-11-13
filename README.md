# 🤖 Gamma Academy - Asistente de Capacitación y Visión AI
Este repositorio contiene el código fuente del bot de Telegram desarrollado para el curso Samsung Innovation Campus (SIC). Este proyecto es de Valentín Valdez, Maia Aramayo y Micaela Cafardo.
# 📋 Descripción
Gamma Academy es un bot de Telegram diseñado como un Asistente Virtual de Capacitación Interna basado en la arquitectura RAG (Retrieval-Augmented Generation) y herramientas de Visión Artificial Multimodal.

Su objetivo principal es responder de manera profesional y precisa las preguntas de los empleados sobre la organización, sus políticas y procesos, utilizando una Base de Conocimiento (JSON) y la potencia de la IA. Además, permite generar quizzes interactivos a partir de documentos y evaluar respuestas complejas (voz e imagen) mediante modelos avanzados de Groq.

El sistema almacena el progreso de los usuarios y permite la exportación de resultados a Excel para un seguimiento gerencial efectivo.

# ✨ Características Principales
* 📚 RAG Integrado: Respuestas exactas y profesionales obtenidas de una Base de Datos local (JSON) y complementadas por un Large Language Model (LLM).

* 📝 Generación de Quizzes: Crea automáticamente evaluaciones de 5 preguntas a partir de archivos subidos (PDF, DOCX, TXT) o enlaces de YouTube, usando Groq (LLM).

* 🎤 Reconocimiento de Voz (STT): Transcribe mensajes de voz usando la API de Groq (Whisper) para procesar tanto consultas de chat como respuestas a preguntas de quiz.

* 📸 Visión Artificial (Vision AI): Describe e interpreta imágenes enviadas (fotos, gráficos) usando un modelo multimodal de Groq (Llama 4 Scout), lo cual permite la evaluación automática de respuestas visuales en los quizzes.

* 🎯 Evaluación Multimodal: Evalúa respuestas de tipo texto (opción múltiple), voz e imagen comparando el input del usuario con la respuesta esperada por la IA.

* 📊 Análisis de Sentimiento: Clasifica el feedback del usuario al finalizar cada quiz (Muy Positivo, Negativo, etc.) usando BERT Multilingüe.

* 📈 Exportación de Resultados: Genera un archivo .xlsx (Excel) con los resultados de un quiz específico para seguimiento y auditoría.

# 🚀 Instalación
### Requisitos Previos:
* Python 3.10 o superior.

* Cuenta de Telegram.

* API Token de Telegram Bot (obtener de @BotFather).

* API Key de Groq.

### 1. Clonar el Repositorio
```Bash  
git clone <URL_DE_TU_REPOSITORIO>
cd gamma-academy
```


### 2. Crear Entorno Virtual
```Bash

python -m venv venv
```
### 3. Instalar Dependencias
Instala todas las librerías necesarias para el manejo de Telegram, IA, y documentos:

```Bash

pip install -r requirements.txt
```
requirements.txt:

```python-dotenv
pyTelegramBotAPI
groq
transformers
torch
pandas
PyPDF2
python-docx
pytubefix
Pillow
```
### 4. Configurar Variables de Entorno
Crear archivo .env en la raíz del proyecto:

```TELEGRAM_BOT_TOKEN=tu_token_de_telegram
GROQ_API_KEY=tu_api_key_de_groq
DATASET_PATH=data/dataset.json
```
(Asegúrate de que la ruta DATASET_PATH apunte a tu archivo de preguntas y respuestas internas).

### 5. Ejecutar el Bot
```Bash

python BOT_final.py
```

# 🎮 UsoComandos Disponibles
ComandoDescripción(Chat Privado y Grupal) 

| **Comando**           | **Descripción**                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| `/start`              | Iniciar conversación y ver mensaje de bienvenida.                              |
| `/cursos`             | Muestra la lista de todos los quizzes (cursos) disponibles actualmente.         |
| `/empezar [nombre]`   | Inicia un quiz específico en el chat privado.                                  |
| `/exportar [nombre]`  | Exporta los resultados finales de un quiz a un archivo Excel (.xlsx).          |
| `/resumen [tema]`     | Genera un resumen educativo conciso sobre un tema específico usando la IA.     |

## Formas de Interactuar
| Tipo de Interacción | Uso Principal |
| :--- | :--- |
| **💬 Texto** | Consultas al **RAG Bot** y respuestas a preguntas de **opción múltiple**. |
| **🎤 Audio** | Envía un mensaje de voz para chatear o para responder preguntas de tipo `voice` en los quizzes. |
| **📸 Foto** | Envía una imagen para que el bot la describa con **IA Vision** o para responder preguntas de tipo `photo` en los quizzes. |
| **📎 Documento/Link** | Sube un **PDF, DOCX, TXT, o un enlace de YouTube** en un chat grupal para **crear un nuevo quiz** basado en su contenido. |

## Ejemplos de Uso
| Escenario | Usuario (Input) | Bot/Gamma Academy (Output) |
| :--- | :--- | :--- |
| **Consulta RAG** | `¿quienes somos?` | "Somos Gamma Academy, tu plataforma de capacitación interna basada en IA, diseñada para reforzar el aprendizaje corporativo a través de quizzes interactivos y herramientas de IA." |
| **Generar Quiz** | `[Sube un PDF]` *(en chat grupal)* | "Por favor, indique el nombre que desea asignarle al nuevo quiz." |
| **Quiz Voz** | *Pregunta:* Explique brevemente la política de licencias. **Usuario:** *[Envía audio con explicación]* | **Bot:** ✅ Respuesta recibida. Siguiente pregunta: *(Evalúa la voz y continúa el quiz).* |
| **Quiz Imagen** | *Pregunta:* Muestre un ejemplo de un cable de red categoría 6. **Usuario:** *[Envía foto de un cable de red]* | **Bot:** ✅ Respuesta recibida. Siguiente pregunta: *(Evalúa la imagen con IA Vision y continúa el quiz).* |

# 📁 Estructura del Proyectotp_final_samsung/
La estructura del repositorio refleja una aplicación de bot modular con componentes dedicados a la lógica central, datos y utilidades.
```
tp_final_samsung/
├── BOT_final.py              # Script principal del bot con toda la lógica de Telegram y handlers.
├── .env                      # Variables de entorno (NO incluir en el control de versiones/git).
├── requirements.txt          # Dependencias del proyecto.
├── README.md                 # Este archivo de documentación.
├── data/
│   └── dataset.json          # Base de conocimiento estática (RAG Q&A).
├── quizzes/
│   └── quiz_ejemplo.json     # Ejemplo de un quiz generado o predefinido.
├── resultados/
│   ├── resultados_finales.json # Log histórico de puntajes finales de todos los quizzes.
│   └── resultados_quiz_A.xlsx  # Ejemplo de exportación de resultados a Excel.
└── utils/
    ├── manejo_de_quizzes.py  # Módulo principal para gestionar las sesiones y el progreso de los quizzes.
    └── + otros archivos...   # Módulos de ayuda adicionales para transcripción, visión, etc.
```
# 🛠️ Tecnologías Utilizadas
| Categoría | Tecnología/Modelo | Uso |
| :--- | :--- | :--- |
| **Framework Bot** | `pyTelegramBotAPI` | Conexión e interacción con Telegram. |
| **LLM/Generación** | **Groq API** (`llama-3.3-70b-versatile`) | Respuestas de chat, RAG *fallback* y generación de preguntas de quiz. |
| **Visión AI** | **Groq API** (`llama-4-scout`) | Descripción y evaluación de imágenes enviadas por el usuario. |
| **STT** | **Groq API** (`whisper-large-v3-turbo`) | Transcripción de audios de chat y respuestas de quiz. |
| **NLP** | `transformers` (BERT) | Análisis de sentimiento del feedback post-quiz. |
| **Datos/Análisis** | `Pandas` | Procesamiento y exportación de resultados a Excel. |
| **Documentos** | `PyPDF2`, `python-docx`, `pytubefix` | Extracción de texto de documentos y videos para la generación de quizzes. |
