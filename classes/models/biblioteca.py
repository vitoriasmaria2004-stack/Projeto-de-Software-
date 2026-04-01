from typing import List, Dict
from enum import Enum

class CategoriaBiblioteca(Enum):
    FAVORITOS = "favoritos"
    LENDO = "lendo"
    CONCLUIDOS = "concluidos"
    PARA_LER_DEPOIS = "para_ler_depois"

class Biblioteca:
    
    def __init__(self, usuario: 'Usuario'):
        self.usuario = usuario
        self.categorias: Dict[CategoriaBiblioteca, List['Historia']] = {
            CategoriaBiblioteca.FAVORITOS: [],
            CategoriaBiblioteca.LENDO: [],
            CategoriaBiblioteca.CONCLUIDOS: [],
            CategoriaBiblioteca.PARA_LER_DEPOIS: []
        }
        self.progresso_leitura: Dict[str, int] = {}  # historia_id -> ultimo_capitulo_numero
        self.ultima_linha_lida: Dict[str, int] = {}  # capitulo_id -> posicao_linha
    
    def adicionar_historia(self, historia: 'Historia', categoria: CategoriaBiblioteca) -> None:
        if historia not in self.categorias[categoria]:
            self.categorias[categoria].append(historia)
    
    def remover_historia(self, historia: 'Historia', categoria: CategoriaBiblioteca) -> None:
        if historia in self.categorias[categoria]:
            self.categorias[categoria].remove(historia)
    
    def mover_historia(self, historia: 'Historia', 
                       de_categoria: CategoriaBiblioteca, 
                       para_categoria: CategoriaBiblioteca) -> None:
        self.remover_historia(historia, de_categoria)
        self.adicionar_historia(historia, para_categoria)
    
    def marcar_progresso(self, historia: 'Historia', capitulo_numero: int, 
                         linha: int = 0) -> None:
        self.progresso_leitura[historia.id] = capitulo_numero
        # também salva última linha (para futuro)
    
    def get_continuar_lendo(self) -> List['Historia']:
        return self.categorias[CategoriaBiblioteca.LENDO]
    
    def __str__(self) -> str:
        total = sum(len(hist) for hist in self.categorias.values())
        return f"Biblioteca de {self.usuario.nome}: {total} histórias"
