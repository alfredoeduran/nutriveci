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
        self.MODEL_ID = "food-item-recognition"
        self.MODEL_VERSION_ID = "1d5fd481e0cf4826aa72ec3ff049e044"
        
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
            # Convertir bytes a base64 para Clarifai
            image_base64 = base64.b64encode(image_content).decode('utf-8')
            
            # Crear request para Clarifai
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
            
            # Realizar la predicción
            response = self.stub.PostModelOutputs(
                request,
                metadata=self.metadata
            )
            
            if response.status.code != status_code_pb2.SUCCESS:
                print(f"Error de Clarifai: {response.status.description}, código: {response.status.code}")
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
            
            # Imprimir los conceptos detectados para depuración
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
    
    def _get_food_related_terms(self) -> List[str]:
        """
        Retorna una lista de términos relacionados con alimentos.
        Esta lista puede expandirse según sea necesario.
        """
        return [
            "food", "fruit", "vegetable", "meat", "fish", "dish", "meal",
            "apple", "banana", "orange", "carrot", "potato", "tomato",
            "chicken", "beef", "pork", "salmon", "rice", "pasta",
            "bread", "cake", "dessert", "salad", "soup", "sandwich"
        ] 