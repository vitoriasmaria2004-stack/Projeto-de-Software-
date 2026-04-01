from typing import Optional
from enum import Enum

class TipoAvaliacao(Enum):
    CAPITULO = "capitulo"
    HISTORIA = "historia"

class Avaliacao:
    #de capitulo ou história(1 a 5 estrelas)
    
    def __init__(self, id: str, usuario: 'Usuario', nota: int, 
                 tipo: TipoAvaliacao, capitulo_id: Optional[str] = None):
        self.id = id
        self.usuario = usuario
        self.nota = nota  # 1 a 5
        self.tipo = tipo
        self.capitulo_id = capitulo_id  # nenhum se for avaliação de história
    
    def __str__(self) -> str:
        tipo_str = "Capítulo" if self.tipo == TipoAvaliacao.CAPITULO else "História"
        return f"Avaliação: {self.nota}⭐ ({tipo_str}) - {self.usuario.nome}"
