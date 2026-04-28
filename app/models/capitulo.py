"""
Módulo de capítulos - Representa capítulos de histórias.
Implementa: Encapsulamento e Composição com Comentário e Avaliação.
"""
import uuid
from datetime import datetime
from typing import List


class Capitulo:
    """
    Classe que representa um capítulo de uma história.
    Implementa composição: contém comentários e avaliações.
    """
    
    def __init__(self, titulo: str, conteudo: str, ordem: int):
        """
        Args:
            titulo: Título do capítulo
            conteudo: Texto do capítulo
            ordem: Posição sequencial na história
        """
        self.id = str(uuid.uuid4())
        self.titulo = titulo
        self._conteudo = conteudo  # Protegido
        self.ordem = ordem
        self._comentarios: List['Comentario'] = []
        self._avaliacoes: List['Avaliacao'] = []
        self._destaques: dict = {}
        self.data_criacao = datetime.now()
        self.data_atualizacao = datetime.now()
        self.visualizacoes = 0

    @property
    def conteudo(self) -> str:
        """Acesso à leitura do conteúdo."""
        return self._conteudo

    @conteudo.setter
    def conteudo(self, novo_conteudo: str):
        """Atualiza o conteúdo e data de modificação."""
        self._conteudo = novo_conteudo
        self.data_atualizacao = datetime.now()

    def adicionar_comentario(self, comentario: 'Comentario'):
        """Adiciona um comentário ao capítulo."""
        self._comentarios.append(comentario)

    def adicionar_avaliacao(self, avaliacao: 'Avaliacao'):
        """Adiciona uma avaliação ao capítulo."""
        self._avaliacoes.append(avaliacao)

    @property
    def comentarios(self) -> List['Comentario']:
        """Retorna lista de comentários."""
        return self._comentarios

    @property
    def avaliacoes(self) -> List['Avaliacao']:
        """Retorna lista de avaliações."""
        return self._avaliacoes

    @property
    def destaques(self) -> dict:
        """Retorna os trechos destacados por leitores."""
        return self._destaques

    def adicionar_destaque(self, usuario_id: str, trecho: str):
        """Registra que um leitor destacou um trecho do capítulo."""
        trecho_normalizado = " ".join(str(trecho or "").split())
        if not usuario_id or not trecho_normalizado:
            return None

        chave = trecho_normalizado.casefold()
        destaque = self._destaques.setdefault(chave, {
            'trecho': trecho_normalizado,
            'usuarios': [],
        })
        if usuario_id not in destaque['usuarios']:
            destaque['usuarios'].append(usuario_id)
            self.data_atualizacao = datetime.now()
        return destaque

    def remover_destaque(self, usuario_id: str, trecho: str) -> bool:
        """Remove a marcação de um leitor para um trecho."""
        trecho_normalizado = " ".join(str(trecho or "").split())
        chave = trecho_normalizado.casefold()
        destaque = self._destaques.get(chave)
        if not destaque or usuario_id not in destaque.get('usuarios', []):
            return False

        destaque['usuarios'].remove(usuario_id)
        if not destaque['usuarios']:
            self._destaques.pop(chave, None)
        self.data_atualizacao = datetime.now()
        return True

    def obter_destaques_recomendados(self, total_leitores: int, percentual_minimo: float = 0.6) -> list[dict]:
        """Retorna trechos marcados por leitores suficientes para recomendação."""
        base = max(1, total_leitores)
        recomendados = []
        for destaque in self._destaques.values():
            usuarios = destaque.get('usuarios', [])
            percentual = len(usuarios) / base
            if percentual >= percentual_minimo:
                recomendados.append({
                    'trecho': destaque.get('trecho', ''),
                    'total': len(usuarios),
                    'percentual': round(percentual * 100),
                })
        return sorted(recomendados, key=lambda item: item['total'], reverse=True)

    def obter_media_avaliacoes(self) -> float:
        """Calcula a média de avaliações do capítulo."""
        if not self._avaliacoes:
            return 0.0
        total = sum(av.nota for av in self._avaliacoes)
        return total / len(self._avaliacoes)

    def obter_total_palavras(self) -> int:
        """Retorna a quantidade aproximada de palavras do capítulo."""
        return len(self._conteudo.split())

    def obter_tempo_estimado_leitura(self) -> int:
        """Calcula o tempo estimado de leitura em minutos."""
        return max(1, round(self.obter_total_palavras() / 220))

    def registrar_visualizacao(self):
        """Registra uma visualização do capítulo."""
        self.visualizacoes += 1

    def __str__(self) -> str:
        return f"Capítulo {self.ordem}: {self.titulo}"

    def __repr__(self) -> str:
        return f"<Capitulo {self.id} '{self.titulo}'>"
