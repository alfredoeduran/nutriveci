"""
Módulo para la detección de alimentos en imágenes usando Clarifai API.
"""
import os
import base64
from typing import List, Dict, Optional
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class FoodDetector:
    def __init__(self):
        """Inicializa el cliente de Clarifai."""
        self.PAT = os.getenv("CLARIFAI_PAT", "d14555c665f14af59a2be1bd74a8d6c6")
        self.USER_ID = "clarifai"
        self.APP_ID = "main"
        self.MODEL_ID = os.getenv("CLARIFAI_MODEL_ID", "food-item-recognition")
        self.MODEL_VERSION_ID = os.getenv("CLARIFAI_MODEL_VERSION_ID", "1d5fd481e0cf4826aa72ec3ff049e044")
        
        print(f"✅ Inicializando Clarifai con PAT: {self.PAT[:4]}...{self.PAT[-4:]}")
        
        # Configurar canal y stub
        self.channel = ClarifaiChannel.get_grpc_channel()
        self.stub = service_pb2_grpc.V2Stub(self.channel)
        self.metadata = (('authorization', 'Key ' + self.PAT),)
        self.user_data_object = resources_pb2.UserAppIDSet(
            user_id=self.USER_ID,
            app_id=self.APP_ID
        )
        
    async def detect_food(self, image_content: bytes) -> Dict:
        """
        Detecta alimentos en una imagen usando Clarifai.
        
        Args:
            image_content: Contenido binario de la imagen
            
        Returns:
            Dict con la información de los alimentos detectados
        """
        try:
            print(f"Procesando imagen de {len(image_content)} bytes")
            
            # Crear request para Clarifai - NO USAR image_base64 aquí, la API espera los bytes directamente
            request = service_pb2.PostModelOutputsRequest(
                user_app_id=self.user_data_object,
                model_id=self.MODEL_ID,
                version_id=self.MODEL_VERSION_ID,
                inputs=[
                    resources_pb2.Input(
                        data=resources_pb2.Data(
                            image=resources_pb2.Image(
                                base64=image_content
                            )
                        )
                    )
                ]
            )
            
            print("Enviando request a Clarifai...")
            
            # Realizar la predicción
            response = self.stub.PostModelOutputs(
                request,
                metadata=self.metadata
            )
            
            print(f"Respuesta recibida, código de estado: {response.status.code}")
            
            if response.status.code != status_code_pb2.SUCCESS:
                print(f"Error de Clarifai: {response.status.description}")
                return {
                    "detected_foods": [],
                    "confidence_scores": {},
                    "success": False,
                    "error": response.status.description
                }
            
            # Procesar resultados
            output = response.outputs[0]
            food_items = []
            confidence_scores = {}
            
            print("Conceptos detectados por Clarifai:")
            all_concepts = []
            for concept in output.data.concepts:
                print(f"  {concept.name}: {concept.value}")
                if concept.value > 0.15:  # Solo incluir predicciones con confianza > 15% (antes era 50%)
                    all_concepts.append((concept.name, concept.value))
            
            # Ordenar por confianza y limitar a los 5 mejores resultados
            all_concepts.sort(key=lambda x: x[1], reverse=True)
            top_concepts = all_concepts[:5]  # Tomar solo los 5 mejores resultados
            
            food_items = [name for name, _ in top_concepts]
            confidence_scores = {name: value for name, value in top_concepts}
            
            return {
                "detected_foods": food_items,
                "confidence_scores": confidence_scores,
                "success": True
            }
            
        except Exception as e:
            import traceback
            print(f"Error en detect_food: {str(e)}")
            print(traceback.format_exc())
            return {
                "detected_foods": [],
                "confidence_scores": {},
                "success": False,
                "error": str(e)
            }

    def detect_food_sync(self, image_content: bytes) -> Dict:
        """
        Versión sincrónica para detectar alimentos en una imagen usando Clarifai.
        
        Args:
            image_content: Contenido binario de la imagen
            
        Returns:
            Dict con la información de los alimentos detectados
        """
        import asyncio
        
        try:
            # Crear un nuevo bucle de eventos para ejecutar la función asíncrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.detect_food(image_content))
            loop.close()
            return result
        except Exception as e:
            import traceback
            print(f"Error en detect_food_sync: {str(e)}")
            print(traceback.format_exc())
            return {
                "detected_foods": [],
                "confidence_scores": {},
                "success": False,
                "error": str(e)
            } 