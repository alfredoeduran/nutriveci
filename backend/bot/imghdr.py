"""
Módulo imghdr personalizado que proporciona funcionalidad básica para identificar tipos de archivos de imagen.
Este módulo existe porque imghdr fue eliminado de la biblioteca estándar de Python en la versión 3.12+.
"""
import struct
from typing import Optional, Union, BinaryIO

def what(file: Union[str, BinaryIO], h: Optional[bytes] = None) -> Optional[str]:
    """
    Determina el tipo de una imagen.
    
    Args:
        file: Puede ser un nombre de archivo o un objeto de archivo abierto.
        h: Los primeros 32 bytes del archivo, si ya se han leído.
        
    Returns:
        Una cadena que indica el tipo de imagen ('jpeg', 'png', etc.) o None si no es reconocida.
    """
    if h is None:
        if isinstance(file, str):
            with open(file, 'rb') as f:
                h = f.read(32)
        else:
            location = file.tell()
            h = file.read(32)
            file.seek(location)
    
    # Verificar JPEG
    if h[0:2] == b'\xff\xd8':
        return 'jpeg'
    
    # Verificar PNG
    if h[0:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    
    # Verificar GIF
    if h[0:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    
    # Verificar BMP
    if h[0:2] == b'BM':
        return 'bmp'
    
    # Verificar TIFF
    if h[0:2] in (b'MM', b'II'):
        if h[2:4] == b'\x00\x2a':
            return 'tiff'
    
    # Verificar WebP
    if h[0:4] == b'RIFF' and h[8:12] == b'WEBP':
        return 'webp'
    
    return None

# Funciones adicionales para mantener compatibilidad
def test_jpeg(h):
    """Test for JPEG data."""
    return h[0:2] == b'\xff\xd8'

def test_png(h):
    """Test for PNG data."""
    return h[0:8] == b'\x89PNG\r\n\x1a\n'

def test_gif(h):
    """Test for GIF data."""
    return h[0:6] in (b'GIF87a', b'GIF89a')

def test_bmp(h):
    """Test for BMP data."""
    return h[0:2] == b'BM'

def test_tiff(h):
    """Test for TIFF data."""
    return h[0:2] in (b'MM', b'II') and h[2:4] == b'\x00\x2a' 