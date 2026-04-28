"""
Módulo de comentários - Permite comentar em capítulos.
Implementa: Encapsulamento e Composição.
"""
from datetime import datetime
from typing import List, Optional


class Comentario:
    """
    Classe que representa um comentário em um capítulo.
    Implementa encapsulamento: conteúdo pode ser editado apenas pelo autor.
    Suporta respostas em threads (comentários aninhados).
    """
    
    def __init__(self, id: str, usuario: 'Usuario', conteudo: str, 
                 capitulo_id: str = "", posicao_texto: Optional[int] = None):
        """
        Args:
            id: Identificador único
            usuario: Usuário que criou o comentário
            conteudo: Texto do comentário
            capitulo_id: ID do capítulo onde foi comentado
            posicao_texto: Posição no texto para comentários específicos
        """
        self.id = id
        self.usuario = usuario
        self._conteudo = conteudo  # Protegido
        self.capitulo_id = capitulo_id
        self.posicao_texto = posicao_texto
        self.data_criacao = datetime.now()
        self.curtidas = 0
        self.respostas: List['Comentario'] = []
        self.comentario_pai: Optional['Comentario'] = None
    
    def obter_conteudo(self) -> str:
        """Acesso público protegido ao conteúdo."""
        return self._conteudo

    def editar_conteudo(self, novo_conteudo: str, usuario: 'Usuario') -> bool:
        """Apenas o autor pode editar seu comentário."""
        if usuario.id_usuario == self.usuario.id_usuario:
            self._conteudo = novo_conteudo
            return True
        return False

    def curtir(self):
        """Incrementa o contador de curtidas."""
        self.curtidas += 1

    def responder(self, id: str, usuario: 'Usuario', conteudo: str) -> 'Comentario':
        """Cria uma resposta a este comentário."""
        resposta = Comentario(id, usuario, conteudo, posicao_texto=self.posicao_texto)
        resposta.comentario_pai = self
        self.respostas.append(resposta)
        return resposta
    
    def __str__(self) -> str:
        return f"{self.usuario.nome}: {self._conteudo[:50]}..."
    
    def __repr__(self) -> str:
        return f"<Comentario {self.id} de {self.usuario.nome}>"
