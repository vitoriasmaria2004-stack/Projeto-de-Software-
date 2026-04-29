"""
Módulo de Autor - Subtipo de usuário especializado em publicação.
Implementa: Herança de Usuario, Polimorfismo em exibir_painel(), Delegação.
"""
from typing import List
from .usuario import Usuario


class EstatisticasAutor:
    """
    Componente de delegação para cálculo de estatísticas.
    Implementa padrão de composição: responsabilidade única.
    """
    
    def __init__(self):
        self._leitores_totais = 0  # Privado por convenção
        self._engajamento_total = 0  # Privado por convenção
        self._capitulos_publicados = 0  # Privado por convenção

    def adicionar_historia(self, historia: 'Historia'):
        """Atualiza estatísticas com os dados de uma história."""
        self._leitores_totais += len(historia.leitores)
        self._engajamento_total += historia.obter_total_comentarios()
        self._capitulos_publicados += historia.obter_quantidade_capitulos()

    def obter_resumo(self) -> str:
        """Retorna resumo formatado das estatísticas."""
        return (f"👥 Leitores: {self._leitores_totais} | "
                f"💬 Engajamento: {self._engajamento_total} | "
                f"📖 Capítulos: {self._capitulos_publicados}")

    def __str__(self):
        return self.obter_resumo()


class Autor(Usuario):
    """
    Classe especializada em publicação de histórias.
    Implementa herança: herda de Usuario e implementa exibir_painel().
    Implementa delegação: delega cálculos de estatísticas.
    """
    
    def __init__(self, id_usuario: str, nome: str, email: str, senha: str):
        """
        Args:
            id_usuario: Identificador único
            nome: Nome do autor
            email: Email único
            senha: Senha de acesso
        """
        super().__init__(id_usuario, nome, email, senha)
        self._obras: List['Historia'] = []
        self._estatisticas = EstatisticasAutor()

    def exibir_painel(self) -> str:
        """
        Implementação polimórfica: Painel específico do autor.
        """
        return f"✍️ Painel do Autor: {len(self._obras)} obras publicadas."

    def publicar_historia(self, historia: 'Historia') -> bool:
        """
        Publica uma nova história.
        Implementa responsabilidade: vincular autor e adicionar à lista.
        """
        historia.vincular_autor(self)
        if historia not in self._obras:
            self._obras.append(historia)
        self._estatisticas.adicionar_historia(historia)
        return True

    def editar_historia(self, historia: 'Historia', 
                       titulo: str = None, sinopse: str = None) -> bool:
        """Permite editar metadados de uma história publicada."""
        if historia in self._obras:
            if titulo:
                historia.titulo = titulo
            if sinopse:
                historia.sinopse = sinopse
            return True
        return False

    def atualizar_metricas(self) -> str:
        """
        Delegação: Autor pede para o componente processar estatísticas.
        """
        self._estatisticas = EstatisticasAutor()
        for h in self._obras:
            self._estatisticas.adicionar_historia(h)
        return str(self._estatisticas)

    def obter_obras(self) -> List['Historia']:
        """Retorna todas as obras do autor."""
        return self._obras

    def obter_total_leitores(self) -> int:
        """Retorna total de leitores únicos em todas as obras."""
        leitores_unicos = set()
        for historia in self._obras:
            for leitor in historia.leitores:
                leitores_unicos.add(leitor.id_usuario)
        return len(leitores_unicos)

    def __str__(self) -> str:
        return f"Autor: {self.nome}"

    def __repr__(self) -> str:
        return f"<Autor {self.id_usuario} {self.nome}>"
