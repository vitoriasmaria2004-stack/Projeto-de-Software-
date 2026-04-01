from typing import List, Optional
from datetime import datetime

class Capitulo:
    
    def __init__(self, id: str, numero: int, titulo: str, conteudo: str):
        self.id = id
        self.numero = numero
        self.titulo = titulo
        self.conteudo = conteudo
        self.historia: Optional['Historia'] = None
        self.comentarios: List['Comentario'] = []
        self.avaliacoes: List['Avaliacao'] = []
        self.data_publicacao = datetime.now()
        self.tempo_estimado_leitura_min = self._calcular_tempo_leitura()
    
    def _calcular_tempo_leitura(self) -> int:
        # Média de 200 palavras por minuto
        palavras = len(self.conteudo.split())
        return max(1, palavras // 200)
    
    def adicionar_comentario(self, comentario: 'Comentario') -> None:
        self.comentarios.append(comentario)
    
    def adicionar_avaliacao(self, avaliacao: 'Avaliacao') -> None:
        self.avaliacoes.append(avaliacao)
    
    def get_media_avaliacoes(self) -> float:
        if not self.avaliacoes:
            return 0.0
        return sum(a.nota for a in self.avaliacoes) / len(self.avaliacoes)
    
    def __str__(self) -> str:
        return f"Capítulo {self.numero}: {self.titulo} ({self.tempo_estimado_leitura_min} min de leitura)"
