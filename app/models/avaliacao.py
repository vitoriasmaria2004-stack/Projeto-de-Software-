"""
Módulo de avaliações - Permite avaliar histórias e capítulos.
Implementa: Polimorfismo através de TipoAvaliacao.
"""
from enum import Enum
from datetime import datetime
from typing import Optional, Union


class TipoAvaliacao(Enum):
    """Enum para tipos de avaliação."""
    CAPITULO = "capitulo"
    HISTORIA = "historia"


class Avaliacao:
    """
    Classe que representa uma avaliação de capítulo ou história.
    Implementa polimorfismo: pode ser aplicada a diferentes tipos de conteúdo.
    """
    
    def __init__(self, id: str, usuario: 'Usuario', nota: int, 
                 tipo: TipoAvaliacao, conteudo_id: Optional[str] = None):
        """
        Args:
            id: Identificador único da avaliação
            usuario: Usuário que fez a avaliação
            nota: Nota de 1 a 5 estrelas
            tipo: TipoAvaliacao (CAPITULO ou HISTORIA)
            conteudo_id: ID do capítulo/história (None se for história)
        """
        self.id = id
        self.usuario = usuario
        self.nota = self._validar_nota(nota)
        self.tipo = tipo
        self.conteudo_id = conteudo_id
        self.data_criacao = datetime.now()

    @staticmethod
    def _validar_nota(nota: int) -> int:
        """Valida que a nota está entre 1 e 5."""
        if not 1 <= nota <= 5:
            raise ValueError("Nota deve estar entre 1 e 5")
        return nota

    def obter_estrelas(self) -> str:
        """Retorna representação visual da avaliação."""
        return "⭐" * self.nota

    def __str__(self) -> str:
        tipo_str = "Capítulo" if self.tipo == TipoAvaliacao.CAPITULO else "História"
        nome_usuario = self.usuario.nome if self.usuario else "Usuário desconhecido"
        return f"{self.obter_estrelas()} ({tipo_str}) - {nome_usuario}"

    def __repr__(self) -> str:
        return f"<Avaliacao {self.id} {self.nota}⭐>"
