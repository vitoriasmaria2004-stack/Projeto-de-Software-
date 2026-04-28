"""
Utils - Utilitários
Contém funções auxiliares, validações e ferramentas reutilizáveis
"""

from .persistence import carregar_estado, salvar_estado, obter_status_persistencia

__all__ = [
    'carregar_estado',
    'salvar_estado',
    'obter_status_persistencia',
]
