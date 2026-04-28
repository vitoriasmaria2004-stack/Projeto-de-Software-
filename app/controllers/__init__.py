"""
Módulo controllers - Camada de lógica de negócio
Implementa controllers do padrão MVC
"""
from .usuario_controller import UsuarioController
from .historia_controller import HistoriaController

__all__ = [
    'UsuarioController',
    'HistoriaController',
]
