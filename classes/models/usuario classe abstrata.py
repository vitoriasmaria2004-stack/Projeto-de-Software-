from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Set
from models.notificacao import Notificacao
from models.preferencias_leitura import PreferenciasLeitura

class Usuario(ABC):
    
    
    def __init__(self, id: str, nome: str, email: str, senha: str):
        self.id = id
        self.nome = nome
        self.email = email
        self.senha = senha 
        self.data_cadastro = datetime.now()
        self.autores_seguidos: List['Autor'] = []
        self.notificacoes: List[Notificacao] = []
        self.preferencias = PreferenciasLeitura()
        
        # Protegido (protected) - pode ser acessado por subclasses
        self._historico_leitura: List['Capitulo'] = []
    
    #  MÉTODOS COMUNS A TODOS USUÁRIOS 
    
    def seguir_autor(self, autor: 'Autor') -> None:
        if autor not in self.autores_seguidos:
            self.autores_seguidos.append(autor)
            print(f"✓ {self.nome} agora segue {autor.nome}")
    
    def adicionar_notificacao(self, notificacao: Notificacao) -> None:
        self.notificacoes.append(notificacao)
    
    def marcar_notificacoes_lidas(self) -> None:
        for notif in self.notificacoes:
            notif.lida = True
    
    def registrar_leitura(self, capitulo: 'Capitulo') -> None:
        self._historico_leitura.append(capitulo)
        if capitulo.historia:
            capitulo.historia.registrar_leitor(self)
    
    def get_historico_leitura(self) -> List['Capitulo']:
        "Retorna o histórico de leitura (leitura apenas)"
        return self._historico_leitura.copy()
    
    # MÉTODOS ABSTRATOS (CADA SUBCLASSE IMPLEMENTA) 
    
    @abstractmethod
    def get_tipo_usuario(self) -> str:
        "Retorna o tipo de usuário: 'leitor' ou 'autor'"
        pass
    
    @abstractmethod
    def get_acoes_permitidas(self) -> List[str]:
        pass
    
    #  MÉTODOS DE VALIDAÇÃO 
    
    def autenticar(self, senha: str) -> bool:
        """Verifica se a senha está correta"""
        return self.senha == senha
    
    # MÉTODOS DE REPRESENTAÇÃO 
    
    def __str__(self) -> str:
        return f"{self.get_tipo_usuario().title()}: {self.nome} ({self.email})"
