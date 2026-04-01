from datetime import datetime
from typing import List, Optional
from models.notificacao import Notificacao
from models.biblioteca import Biblioteca
from models.preferencias_leitura import PreferenciasLeitura

class Usuario:
    "Usuário base do sistema (leitores e autores herdam desta classe)"
    
    def __init__(self, id: str, nome: str, email: str, senha: str):
        self.id = id
        self.nome = nome
        self.email = email
        self.senha = senha
        self.data_cadastro = datetime.now()
        self.autores_seguidos: List['Autor'] = []
        self.biblioteca: Optional[Biblioteca] = None
        self.notificacoes: List[Notificacao] = []
        self.preferencias = PreferenciasLeitura()
        self.historico_leitura: List['Capitulo'] = []  # para recomendações
        
    def seguir_autor(self, autor: 'Autor') -> None:
        if autor not in self.autores_seguidos:
            self.autores_seguidos.append(autor)
            print(f"{self.nome} agora segue {autor.nome}")
    
    def adicionar_notificacao(self, notificacao: Notificacao) -> None:
        self.notificacoes.append(notificacao)
    
    def marcar_notificacoes_lidas(self) -> None:
        for notif in self.notificacoes:
            notif.lida = True
    
    def registrar_leitura(self, capitulo: 'Capitulo') -> None:
        "Registra que o usuário leu um capítulo (para recomendações)"
        self.historico_leitura.append(capitulo)
    
    def __str__(self) -> str:
        return f"Usuario({self.nome}, {self.email})"
