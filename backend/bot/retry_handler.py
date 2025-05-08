import time
import random
import logging
from telegram.error import NetworkError, TimedOut, RetryAfter

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

class RetryHandler:
    """Clase para gestionar reintentos con espera exponencial."""
    
    def __init__(self, max_retries=3, base_delay=1, max_delay=30):
        """
        Inicializa el gestor de reintentos.
        
        Args:
            max_retries: Número máximo de reintentos
            base_delay: Retraso base en segundos
            max_delay: Retraso máximo en segundos
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def execute_with_retry(self, func, *args, **kwargs):
        """
        Ejecuta una función con reintentos.
        
        Args:
            func: Función a ejecutar
            *args, **kwargs: Argumentos para la función
            
        Returns:
            Resultado de la función
            
        Raises:
            Exception: Si todos los reintentos fallan
        """
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (NetworkError, TimedOut, RetryAfter) as e:
                last_exception = e
                if attempt < self.max_retries:
                    # Calcular retraso con backoff exponencial y jitter
                    delay = min(self.base_delay * (2 ** attempt) + random.uniform(0, 1), self.max_delay)
                    logger.warning(f"Error de red en intento {attempt+1}/{self.max_retries+1}. Reintentando en {delay:.2f}s")
                    time.sleep(delay)
                else:
                    logger.error(f"Todos los reintentos fallaron: {str(e)}")
                    raise last_exception
            except Exception as e:
                # Para otros errores, no reintentamos
                logger.error(f"Error no recuperable: {str(e)}")
                raise e 