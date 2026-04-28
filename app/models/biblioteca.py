"""
Módulo de biblioteca pessoal - Organiza histórias do usuário.
Implementa: Encapsulamento e Organização de Dados.
"""
from enum import Enum
from typing import List, Dict


class CategoriaBiblioteca(Enum):
    """Categorias disponíveis na biblioteca pessoal."""
    FAVORITOS = "Favoritos"
    LENDO = "Lendo"
    CONCLUIDOS = "Concluídos"
    PAUSADOS = "Pausados"


class Biblioteca:
    """
    Classe que gerencia a biblioteca pessoal de um usuário.
    Implementa: Encapsulamento de coleções de histórias por categoria.
    """
    
    def __init__(self, usuario: 'Usuario'):
        """
        Args:
            usuario: Proprietário da biblioteca
        """
        self.usuario = usuario
        self._categorias: Dict[CategoriaBiblioteca, List['Historia']] = {
            cat: [] for cat in CategoriaBiblioteca
        }

    def _remover_de_todas_as_categorias(self, historia: 'Historia'):
        """Remove a história de qualquer categoria anterior."""
        for historias in self._categorias.values():
            if historia in historias:
                historias.remove(historia)

    def adicionar_historia(self, historia: 'Historia',
                          categoria: CategoriaBiblioteca = CategoriaBiblioteca.LENDO):
        """
        Adiciona uma história à categoria especificada.
        
        Args:
            historia: História a ser adicionada
            categoria: Categoria onde adicionar (padrão: LENDO)
        """
        self._remover_de_todas_as_categorias(historia)
        self._categorias[categoria].append(historia)

        # Registra o usuário como leitor da história
        if self.usuario not in historia.leitores:
            historia.adicionar_leitor(self.usuario)

    def remover_historia(self, historia: 'Historia', categoria: CategoriaBiblioteca) -> bool:
        """Remove uma história de uma categoria."""
        try:
            self._categorias[categoria].remove(historia)
            return True
        except ValueError:
            return False

    def mover_historia(self, historia: 'Historia', 
                      origem: CategoriaBiblioteca, 
                      destino: CategoriaBiblioteca) -> bool:
        """Move uma história de uma categoria para outra."""
        if self.remover_historia(historia, origem):
            self.adicionar_historia(historia, destino)
            return True
        return False

    def definir_categoria(self, historia: 'Historia', categoria: CategoriaBiblioteca):
        """Define uma única categoria principal para a história na biblioteca."""
        self.adicionar_historia(historia, categoria)

    def obter_categoria_da_historia(self, historia_id: str) -> CategoriaBiblioteca | None:
        """Retorna a categoria atual de uma história na biblioteca."""
        for categoria, historias in self._categorias.items():
            for historia in historias:
                if historia.id == historia_id:
                    return categoria
        return None

    def obter_continuar_lendo(self) -> List['Historia']:
        """Retorna histórias em leitura."""
        return self._categorias[CategoriaBiblioteca.LENDO]

    def obter_favoritos(self) -> List['Historia']:
        """Retorna histórias favoritas."""
        return self._categorias[CategoriaBiblioteca.FAVORITOS]

    def obter_concluidos(self) -> List['Historia']:
        """Retorna histórias concluídas."""
        return self._categorias[CategoriaBiblioteca.CONCLUIDOS]

    def obter_pausados(self) -> List['Historia']:
        """Retorna histórias pausadas."""
        return self._categorias[CategoriaBiblioteca.PAUSADOS]

    def obter_todas_as_historias(self) -> List['Historia']:
        """Retorna todas as histórias de todas as categorias."""
        historias_unicas = {}
        for historias in self._categorias.values():
            for historia in historias:
                historias_unicas[historia.id] = historia
        return list(historias_unicas.values())

    def obter_total_historias(self) -> int:
        """Retorna total de histórias na biblioteca."""
        return len(self.obter_todas_as_historias())

    def obter_historias_por_categoria(self, categoria: CategoriaBiblioteca) -> List['Historia']:
        """Retorna histórias de uma categoria específica."""
        return self._categorias[categoria]

    def __str__(self) -> str:
        total = self.obter_total_historias()
        lendo = len(self.obter_continuar_lendo())
        return f"📚 Biblioteca de {self.usuario.nome}: {total} histórias ({lendo} lendo)"
