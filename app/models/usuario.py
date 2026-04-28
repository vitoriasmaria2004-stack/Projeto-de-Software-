"""
Módulo de modelos de usuário - Base abstrata para toda hierarquia de usuários.
Implementa: Herança, Encapsulamento, Polimorfismo através de método abstrato.
"""
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .notificacao import Notificacao


class Usuario(ABC):
    """
    Classe abstrata que define a base para todos os usuários do StoryFlow.
    Implementa princípios de POO:
    - Encapsulamento: Senha privada (__senha)
    - Herança: Subclasses devem implementar exibir_painel()
    - Polimorfismo: Método abstrato exibir_painel()
    """
    
    def __init__(self, id_usuario: str, nome: str, email: str, senha: str):
        self.id_usuario = id_usuario
        self.nome = nome
        self.email = email
        self.__senha = senha  # Privado: Encapsulamento
        self._notificacoes: List['Notificacao'] = []  # Protegido
        self.data_criacao = datetime.now()

    @abstractmethod
    def exibir_painel(self) -> str:
        """
        Contrato polimórfico: Subclasses DEVEM implementar.
        Cada tipo de usuário exibe seu painel de forma diferente.
        """
        pass

    def adicionar_notificacao(self, notificacao: 'Notificacao'):
        """Adiciona uma notificação ao usuário."""
        self._notificacoes.append(notificacao)

    def obter_notificacoes(self) -> List['Notificacao']:
        """Retorna todas as notificações do usuário."""
        return self._notificacoes

    def validar_senha(self, senha: str) -> bool:
        """Valida a senha do usuário (encapsulamento)."""
        return self.__senha == senha

    def alterar_senha(self, senha_antiga: str, senha_nova: str) -> bool:
        """Altera a senha se a antiga estiver correta."""
        if self.validar_senha(senha_antiga):
            self.__senha = senha_nova
            return True
        return False

    def __str__(self) -> str:
        return f"{self.nome} ({self.email})"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.id_usuario}>"