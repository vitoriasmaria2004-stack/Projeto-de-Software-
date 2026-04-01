from typing import Optional
from datetime import datetime

class Comentario:
    
    def __init__(self, id: str, usuario: 'Usuario', conteudo: str, 
                 posicao_texto: Optional[int] = None):
        self.id = id
        self.usuario = usuario
        self.conteudo = conteudo
        self.posicao_texto = posicao_texto  # posição no texto (para comentários em partes específicas)
        self.data_criacao = datetime.now()
        self.respostas: List['Comentario'] = []
        self.comentario_pai: Optional['Comentario'] = None
    
    def responder(self, id: str, usuario: 'Usuario', conteudo: str) -> 'Comentario':
        resposta = Comentario(id, usuario, conteudo)
        resposta.comentario_pai = self
        self.respostas.append(resposta)
        return resposta
    
    def __str__(self) -> str:
        return f"{self.usuario.nome}: {self.conteudo[:50]}..."
