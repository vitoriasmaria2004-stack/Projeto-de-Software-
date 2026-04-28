"""
Módulo de notificações - Sistema de notificações do usuário.
Implementa: Encapsulamento e Organização de Dados.
"""
from enum import Enum
from datetime import datetime


class TipoNotificacao(Enum):
    """Tipos de notificações do sistema."""
    NOVO_CAPITULO = "novo_capitulo"
    ATUALIZACAO_HISTORIA = "atualizacao_historia"
    COMENTARIO_RESPONDIDO = "comentario_respondido"
    NOVA_AVALIACAO = "nova_avaliacao"
    RECOMENDACAO = "recomendacao"


class Notificacao:
    """
    Classe que representa uma notificação para o usuário.
    Implementa encapsulamento: leitura e estado.
    """
    
    def __init__(self, id: str, usuario: 'Usuario', mensagem: str, 
                 tipo: TipoNotificacao, titulo: str = ""):
        """
        Args:
            id: Identificador único
            usuario: Usuário que receberá a notificação
            mensagem: Conteúdo da notificação
            tipo: TipoNotificacao
            titulo: Título da notificação
        """
        self.id = id
        self.usuario = usuario
        self.titulo = titulo or "Notificação do StoryFlow"
        self._mensagem = mensagem
        self.tipo = tipo
        self.data_criacao = datetime.now()
        self.lida = False

    def obter_mensagem(self) -> str:
        """Acesso protegido à mensagem."""
        return self._mensagem

    def marcar_como_lida(self) -> None:
        """Marca a notificação como lida."""
        self.lida = True

    def obter_titulo_formatado(self) -> str:
        """Retorna o título com emoji apropriado."""
        emojis = {
            TipoNotificacao.NOVO_CAPITULO: "📖",
            TipoNotificacao.ATUALIZACAO_HISTORIA: "📚",
            TipoNotificacao.COMENTARIO_RESPONDIDO: "💬",
            TipoNotificacao.NOVA_AVALIACAO: "⭐",
            TipoNotificacao.RECOMENDACAO: "🎯",
        }
        emoji = emojis.get(self.tipo, "📬")
        return f"{emoji} {self.titulo}"

    def dias_desde_criacao(self) -> int:
        """Retorna quantos dias faz que a notificação foi criada."""
        delta = datetime.now() - self.data_criacao
        return delta.days

    def __str__(self) -> str:
        status = "✓" if self.lida else "●"
        return f"{status} {self.obter_titulo_formatado()}"

    def __repr__(self) -> str:
        return f"<Notificacao {self.id} {self.tipo.value}>"
