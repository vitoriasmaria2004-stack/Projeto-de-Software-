"""
Módulo de histórias - Representa histórias na plataforma.
Implementa: Composição com Capítulo, Avaliação e Polimorfismo.
"""
import uuid
from datetime import datetime
from typing import List, Optional


class Historia:
    """
    Classe que representa uma história na plataforma StoryFlow.
    Implementa composição: contém capítulos, avaliações e comentários.
    """
    
    def __init__(self, titulo: str, sinopse: str, genero: str = "", capa: str | None = None):
        """
        Args:
            titulo: Título da história
            sinopse: Descrição breve da história
            genero: Gênero da história (Romance, Ficção Científica, etc)
            capa: URL ou Data URL da capa da história
        """
        self.id = str(uuid.uuid4())
        self.titulo = titulo
        self.sinopse = sinopse
        self.genero = genero
        self.capa = capa.strip() if isinstance(capa, str) and capa.strip() else None
        self.autor: Optional['Autor'] = None
        self._capitulos: List['Capitulo'] = []
        self._avaliacoes: List['Avaliacao'] = []
        self.leitores: List['Usuario'] = []
        self.data_criacao = datetime.now()
        self.data_atualizacao = datetime.now()
        self.status = "em_escrita"  # em_escrita, pausada, completa, abandonada
        self.arquivo_epub: str | None = None
        self.preview_video: str | None = None

    def adicionar_capitulo(self, capitulo: 'Capitulo'):
        """Adiciona um novo capítulo à história."""
        self._capitulos.append(capitulo)
        self.data_atualizacao = datetime.now()

    def vincular_autor(self, autor: 'Autor'):
        """Define o autor da história."""
        self.autor = autor

    def adicionar_avaliacao(self, avaliacao: 'Avaliacao'):
        """Adiciona uma avaliação à história (polimorfismo)."""
        self._avaliacoes.append(avaliacao)

    @property
    def capitulos(self) -> List['Capitulo']:
        """Retorna lista de capítulos."""
        return self._capitulos

    @property
    def avaliacoes(self) -> List['Avaliacao']:
        """Retorna lista de avaliações."""
        return self._avaliacoes

    def obter_quantidade_capitulos(self) -> int:
        """Retorna total de capítulos."""
        return len(self._capitulos)

    def obter_ultimo_capitulo(self) -> Optional['Capitulo']:
        """Retorna o capítulo mais recente da história."""
        if not self._capitulos:
            return None
        return self._capitulos[-1]

    def obter_media_avaliacoes(self) -> float:
        """Calcula a média de avaliações da história."""
        if not self._avaliacoes:
            return 0.0
        total = sum(av.nota for av in self._avaliacoes)
        return total / len(self._avaliacoes)

    def obter_total_palavras(self) -> int:
        """Retorna a quantidade total de palavras da história."""
        return sum(cap.obter_total_palavras() for cap in self._capitulos)

    def obter_tempo_estimado_leitura(self) -> int:
        """Retorna o tempo estimado de leitura da obra completa."""
        return max(1, round(self.obter_total_palavras() / 220))

    def adicionar_leitor(self, usuario: 'Usuario'):
        """Adiciona um leitor à história."""
        if usuario not in self.leitores:
            self.leitores.append(usuario)

    def atualizar_status(self, novo_status: str):
        """Atualiza o status da história."""
        status_validos = ["em_escrita", "pausada", "completa", "abandonada"]
        if novo_status in status_validos:
            self.status = novo_status
            self.data_atualizacao = datetime.now()

    def obter_total_comentarios(self) -> int:
        """Retorna total de comentários em todos os capítulos."""
        return sum(len(cap.comentarios) for cap in self._capitulos)

    def obter_popularidade(self) -> float:
        """Calcula uma pontuação simples de descoberta para a obra."""
        return (
            len(self.leitores) * 1.5
            + len(self._avaliacoes) * 2
            + self.obter_total_comentarios() * 1.2
            + self.obter_quantidade_capitulos()
            + self.obter_media_avaliacoes() * 3
        )

    def __str__(self) -> str:
        return f"'{self.titulo}' por {self.autor.nome if self.autor else 'Desconhecido'}"

    def __repr__(self) -> str:
        return f"<Historia {self.id} '{self.titulo}'>"
