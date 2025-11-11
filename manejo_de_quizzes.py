import json
from typing import Optional
import os

class Pregunta:
    def __init__(self, pregunta: str, opciones: list, respuesta_correcta: str, tipo_respuesta: str = 'text'):
        self.pregunta = pregunta
        self.opciones = opciones
        self.respuesta_correcta = respuesta_correcta.lower()
        self.tipo_respuesta = tipo_respuesta.lower()

    def es_correcta(self, respuesta_usuario: str) -> bool:
        if self.tipo_respuesta != 'text':
            #HAY QUE VERIFICAR REALMENTE ESTO
            return True
        return respuesta_usuario.lower() == self.respuesta_correcta

    def formato_para_telegram(self) -> tuple:
        #Formatea la pregunta para Telegram
        if self.tipo_respuesta == 'text':
            texto_opciones = "\n".join([f"{chr(97 + i).upper()}. {opcion}" 
                                        for i, opcion in enumerate(self.opciones)])
            mensaje = f"**Pregunta {self.tipo_respuesta.upper()}:**\n{self.pregunta}\n\n**Opciones:**\n{texto_opciones}\n\nResponde con la letra de la opción (ej: A, B, C, D)."
            return mensaje
        
        elif self.tipo_respuesta == 'voice':
            mensaje = f"**Pregunta {self.tipo_respuesta.upper()}:**\n{self.pregunta}\n\n**Instrucción:** Envía un **mensaje de voz** con tu respuesta."
            return mensaje
            
        elif self.tipo_respuesta == 'photo':
            mensaje = f"**Pregunta {self.tipo_respuesta.upper()}:**\n{self.pregunta}\n\n**Instrucción:** Envía una **imagen/foto** con tu respuesta."
            return mensaje
        
        return "Pregunta mal configurada."
class Quiz:
    def __init__(self, nombre_quiz: str, ruta_archivo: str):
        self.nombre = nombre_quiz
        self.ruta_archivo = ruta_archivo
        self.preguntas = self._cargar_preguntas()
    def _cargar_preguntas(self) -> list[Pregunta]:
        try:
            with open(self.ruta_archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            return [
                Pregunta(
                    pregunta=item['pregunta'],
                    opciones=item.get('opciones', []), 
                    respuesta_correcta=item.get('respuesta_correcta', ''), 
                    tipo_respuesta=item.get('tipo_respuesta', 'text')
                )
                for item in data
            ]
        except Exception as e:
            print(f"Error simple al cargar el quiz '{self.nombre}': {e}")
            return []
        
    def get_pregunta(self, indice: int) -> Optional[Pregunta]:
        if 0 <= indice < len(self.preguntas):
            return self.preguntas[indice]
        return None
    def get_num_preguntas(self) -> int:
        return len(self.preguntas)

class ManejadorQuizzes:
    def __init__(self):
        self.sesiones_activas: dict = {}
        self.quizzes_cargados: dict = self._descubrir_quizzes()
        
    def _descubrir_quizzes(self) -> dict:
        quizzes = {}
        quiz_dir = "quizzes"
        os.makedirs(quiz_dir, exist_ok=True)
            
        for file_name in os.listdir(quiz_dir):
            if file_name.endswith(".json"):
                nombre_quiz = file_name.replace(".json", "")
                quizzes[nombre_quiz.lower()] = os.path.join(quiz_dir, file_name) 
        return quizzes

    def iniciar_quiz(self, chat_id: int, nombre_quiz: str) -> Optional[Pregunta]:
        nombre_normal = nombre_quiz.lower()
        if nombre_normal not in self.quizzes_cargados:
            return None 

        ruta = self.quizzes_cargados[nombre_normal]
        nuevo_quiz = Quiz(nombre_quiz, ruta)
        
        if not nuevo_quiz.preguntas:
            return None 

        primera_pregunta = nuevo_quiz.get_pregunta(0)
        
        self.sesiones_activas[chat_id] = {
            'quiz': nuevo_quiz,
            'indice_actual': 0,
            'puntaje': 0,
            'total_preguntas': nuevo_quiz.get_num_preguntas(),
            'tipo_esperado': primera_pregunta.tipo_respuesta 
        }
        
        return primera_pregunta 

    def avanzar_pregunta(self, chat_id: int, es_correcta: bool) -> tuple[Optional[Pregunta], bool, dict]:
        sesion = self.sesiones_activas.get(chat_id)
        if not sesion:
            return (None, True, {})

        if es_correcta:
            sesion['puntaje'] += 1
            
        sesion['indice_actual'] += 1
        es_fin_de_quiz = sesion['indice_actual'] >= sesion['total_preguntas']

        if es_fin_de_quiz:
            estado_final = {'puntaje': sesion['puntaje'], 'total': sesion['total_preguntas']}
            del self.sesiones_activas[chat_id] 
            return (None, True, estado_final)
        else:
            quiz_actual = sesion['quiz']
            siguiente_pregunta = quiz_actual.get_pregunta(sesion['indice_actual'])
            sesion['tipo_esperado'] = siguiente_pregunta.tipo_respuesta 
            return (siguiente_pregunta, False, {})
            
    def obtener_tipo_esperado(self, chat_id: int) -> Optional[str]:
        sesion = self.sesiones_activas.get(chat_id)
        return sesion.get('tipo_esperado') if sesion else None

