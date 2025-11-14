# 🤖 Gamma Academy - Asistente de Capacitación y Visión AI
Este repositorio contiene el código fuente del bot de Telegram desarrollado para el curso Samsung Innovation Campus (SIC). Este proyecto es de Valentín Valdez, Maia Aramayo y Micaela Cafardo.

## 📋 Descripción
Gamma Academy es un bot de Telegram diseñado como un Asistente Virtual de Capacitación y Evaluación Interna. Combina la potencia de la arquitectura RAG (Retrieval-Augmented Generation) con herramientas de Visión Artificial Multimodal.

Su objetivo principal es digitalizar y automatizar la creación de contenido y la evaluación de empleados. Esto se logra permitiendo la generación de quizzes interactivos a partir de documentos y videos, la evaluación de respuestas complejas (voz e imagen) mediante modelos avanzados de Groq, y la complementación de conocimiento con una Base de Conocimiento (JSON) y la IA.

El sistema almacena el progreso de los usuarios y permite la exportación de resultados a Excel para un seguimiento gerencial efectivo.

## ✨ Características Principales
- 📚 **RAG Integrado**: Respuestas exactas y profesionales obtenidas de una Base de Datos local (JSON) y complementadas por un Large Language Model (LLM).

- 📝 **Generación de Quizzes**: Crea automáticamente evaluaciones de longitud variable (**Corto [5], Medio [7] o Largo [10] preguntas**) a partir de archivos subidos (PDF, DOCX) o enlaces de YouTube, usando Groq.

- 🎤 **Reconocimiento de Voz (STT)**: Transcribe mensajes de voz usando la API de Groq (Whisper) para procesar tanto consultas de chat como respuestas a preguntas de quiz.

- 📸 **Visión Artificial (Vision AI)**: Describe e interpreta imágenes enviadas (fotos, gráficos) usando un modelo multimodal de Groq (`meta-llama/llama-4-scout`) para la evaluación automática de respuestas visuales.

- 🎯 **Evaluación Multimodal**: Evalúa respuestas de tipo texto (opción múltiple), voz e imagen comparando el input del usuario con la respuesta esperada por la IA.

- 📊 **Análisis de Sentimiento**: Clasifica el feedback del usuario al finalizar cada quiz (Muy Positivo, Negativo, etc.) usando un modelo BERT Multilingüe.

- 📈 **Exportación de Resultados**: Genera un archivo `.xlsx` (Excel) con los resultados de un quiz específico para seguimiento y auditoría.

## 🚀 Acceso Rápido y Estado de Despliegue
El bot Gamma Academy se encuentra desplegado y activo. Puedes interactuar con él inmediatamente usando el siguiente enlace o buscándolo en Telegram: https://t.me/SICGammaAcademy_bot

**Nota**: El bot está activo 24/7 en el entorno de servidor. Puede empezar a probar los comandos y la creación de quizzes de inmediato

## 🛠️ Instalación y Despliegue Local
**Requisitos Previos:**
- Python 3.10 o superior.
- Cuenta de Telegram.
- API Key de Groq.

### 1. Clonar el Repositorio
```bash
git clone https://github.com/ValenValdez/CapstoneProject.git
cd CapstoneProject
```

### 2. Crear Entorno Virtual
```bash
python -m venv venv
source venv\Scripts\activate
```

### 3. Instalar Dependencias
Instala todas las librerías necesarias para el manejo de Telegram, IA, y documentos:

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
Crear archivo .env en la raíz del proyecto:
```Ini, TOML
TELEGRAM_BOT_TOKEN=tu_api_key_de_telegram
GROQ_API_KEY=tu_api_key_de_groq
DATASET_PATH=dataset.json
```

(Asegúrate de que DATASET_PATH apunte a tu archivo de preguntas y respuestas).

### 5. Ejecutar el Bot
```bash
python main.py
```

## 🎮 Uso
El comando `/start` tiene respuestas distintas si se usa en privado o en un grupo.

### Comandos Disponibles


|**Comando**|**Descripción**|**Contexto**|
|-|-|-|
| `/start`| Iniciar conversación y ver mensaje de bienvenida.|Privado / Grupal|
| `/help`| Muestra un mensaje de ayuda con todos los comandos disponibles.|Privado / Grupal|
| `/cursos`| Muestra la lista de todos los quizzes (cursos) disponibles actualmente.|Privado / Grupal|
| `/exportar [nombre]`| Exporta los resultados finales de un quiz a un archivo Excel (.xlsx).|Privado / Grupal|
| `/resumen [tema]`| Genera un resumen educativo conciso sobre un tema específico usando la IA.|Privado / Grupal|
| `/estadisticas`| Muestra tu puntaje promedio en los quizzes.|Privado / Grupal|
| `/ranking`| Muestra un top 10 de personas con promedios mayores en los quizzes.|Privado / Grupal|
| `/empezar [nombre]`| Inicia un quiz específico en el chat privado.|Solo Privado|

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
| **Consulta RAG** |`¿Cómo te llamas?`|"Me llamo Gamma Academy, soy un asistente virtual de capacitación."|
| **Generar Quiz** | `[Sube un PDF]` *(en chat grupal)* | "📄 Recibí tu archivo... Por favor, respondé con el nombre que querés para el quiz." |
|...Sigue Generación|`Usuario responde: "Test_de_Ventas"`|"Has elegido el nombre: test_de_ventas. Ahora selecciona la longitud del quiz:"  `[Botones: Corto/Medio/Largo] `|
|...Termina Generación|`[Usuario clickea "🟢 Corto"]`|"⚙️ Generando quiz test_de_ventas con 5 preguntas... ✅ ¡Quiz generado con éxito!"|
| **Quiz Voz** | *Pregunta:* Explique brevemente la política de licencias. **Usuario:** *[Envía audio con explicación]* | **Bot:** ✅ Respuesta recibida. Siguiente pregunta: *(Evalúa la voz y continúa el quiz).* |
| **Quiz Imagen** | *Pregunta:* Muestre un ejemplo de un cable de red categoría 6. **Usuario:** *[Envía foto de un cable de red]* | **Bot:** ✅ Respuesta recibida. Siguiente pregunta: *(Evalúa la imagen con IA Vision y continúa el quiz).* |

## 📁 Estructura del Proyecto
La estructura del repositorio refleja una aplicación de bot modular con componentes dedicados a la lógica central, datos y utilidades.
```
gamma-academy/
├── main.py                 # Script principal del bot con handlers de Telegram y lógica de IA.
├── manejo_de_quizzes.py    # Módulo POO para gestionar sesiones, quizzes y preguntas.
├── .env                    # Variables de entorno (Ignorado por .git).
├── requirements.txt        # Dependencias del proyecto.
├── README.md               # Este archivo de documentación.
├── dataset.json            # Base de conocimiento estática (RAG Q&A).
├── quizzes/
│   └── (vacío por defecto) # Aquí se guardan los .json de quizzes generados.
├── resultados/
│   ├── resultados_finales.json # Log histórico de puntajes (se crea automáticamente).
└── temp/
    └── (vacío por defecto) # Almacenamiento temporal para archivos subidos.
└── temp_audio/
    └── (vacío por defecto) # Almacenamiento temporal para audio descargado.
```

## 🛠️ Tecnologías usadas
| Categoría | Tecnología/Modelo | Uso |
| :--- | :--- | :--- |
| **Framework Bot** | `pyTelegramBotAPI` | Conexión e interacción con Telegram. |
| **LLM/Generación** | **Groq API** (`llama-3.3-70b-versatile`) | Respuestas de chat, RAG *fallback* y generación de preguntas de quiz. |
| **Generación IA** |  **Groq API** (`meta-llama/llama-4-scout...`) | Generación de preguntas de quiz y explicaciones.|
| **Visión AI** | **Groq API** (`meta-llama/llama-4-scout...`) | Descripción y evaluación de imágenes enviadas por el usuario como respuesta al quiz. |
| **STT** | **Groq API** (`whisper-large-v3-turbo`) | Transcripción de audios de chat y respuestas de quiz. |
| **NLP** | `transformers` (BERT) | Análisis de sentimiento del feedback post-quiz. |
| **Datos/Análisis** | `Pandas` | Procesamiento y exportación de resultados a Excel. |
| **Documentos** | `PyPDF2`, `python-docx`, `pytubefix` | Extracción de texto de documentos y videos para la generación de quizzes. |

## 💻 Librerías y Tecnologías Clave

- telebot: Permite la integración con Telegram para recibir y enviar mensajes, imágenes, audios y manejar interacciones con los usuarios mediante comandos y botones.

- transformers: Se utiliza para análisis de sentimiento de los comentarios de los usuarios mediante modelos de lenguaje avanzados (BERT multilingüe).

- pandas: Facilita la manipulación y exportación de datos, especialmente para generar archivos Excel con los resultados de los quizzes.

- dotenv: Gestiona de manera segura las variables de entorno, como tokens de Telegram y claves de API.

- groq: API para generar respuestas automáticas de IA y transcripciones de audio, análisis de imágenes y evaluación de quizzes.

- Pillow (PIL) y PyPDF2/python-docx: Permiten el manejo y extracción de contenido de imágenes, PDFs y documentos Word.

## 🏗️ Estructura y Paradigmas

El proyecto utiliza POO para:

- Manejar quizzes como objetos (Quiz) con atributos como preguntas, tipo de respuesta y progreso del usuario.

- Controlar sesiones activas de cada usuario, almacenando su avance y resultados de manera individual.

- Permitir la extensión futura del bot mediante clases y métodos modulares sin afectar la lógica principal.

# 🧪 Archivo de Prueba para Evaluación del Bot

Para probar la funcionalidad completa del bot (generación de quizzes a partir de documentos, evaluación multimodal, análisis de sentimiento y exportación), se incluye un **archivo de prueba** dentro del repositorio.

---

## 📄 Archivo de Prueba  
Incluimos el archivo **test.pdf** en la raíz del proyecto para que pueda generar un quiz sin necesidad de subir un archivo externo. Este archivo contiene información sobre CodificAr Dev, y al enviarlo al bot, este hará un quiz sobre esta empresa.

---

## ❗ Importante 
Es necesario hacer un grupo con el bot para crear el quiz, sin importar la cantidad de personas que pertenezcan a este grupo. Esta es la unica función que necesariamente tiene que ser dentro de un grupo. 

## 🔍 Pasos de Prueba

| **Paso** | **Contexto** | **Comando / Acción** | **Resultado Esperado** |
|---------|--------------|-----------------------|-------------------------|
| **1. Generación** | Chat Grupal | Suba el archivo `test.pdf` al grupo. Luego responda al bot con el nombre del quiz que desee y seleccione la longitud que desee. | El bot confirmará la creación del quiz y mostrará el comando: `/empezar nombre-elegido`. |
| **2. Inicio** | Chat Privado | Escriba: `/empezar nombre-elegido`. | El bot iniciará el quiz y enviará la primera pregunta (tipo `text`, `voice` o `photo`). |
| **3. Evaluación** | Chat Privado | Responda la pregunta: si es **text**, use el botón. Si es **photo** o **voice**, envíe el contenido correspondiente. | El bot evaluará la respuesta (Correcto/Incorrecto) y avanzará a la siguiente pregunta. |
| **4. Finalización** | Chat Privado | Complete todas las preguntas. | El bot mostrará el puntaje final, registrará el resultado y pedirá un feedback, el cual será analizado con IA (transformers). |
| **5. Exportación** | Chat Privado o Grupal | Escriba: `/exportar nombre-elegido`. | El bot enviará un archivo `.xlsx` con los resultados del quiz recién completado. |
| **6. Probar otros comandos** | Chat Privado o Grupal | Pruebe con otros comandos como `/ranking`, `/estadisticas` o `/resumen`, entre otros. Use `/help` para la lista completa de comandos. | El bot hará la función relacionada al comando dado.
