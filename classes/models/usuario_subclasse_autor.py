from typing import List, Optional
from datetime import datetime
from models.usuario import Usuario
from models.historia import Historia
from models.capitulo import Capitulo
from models.notificacao import Notificacao, TipoNotificacao

class PainelEstatisticas:
    "Painel de estatísticas para autores (classe auxiliar)"
    
    def __init__(self):
        self.total_leitores = 0
        self.total_comentarios = 0
        self.capitulos_populares: List[Capitulo] = []
        self.tempo_medio_leitura_min = 0
    
    def atualizar(self, historia: 'Historia') -> None:
        self.total_leitores = len(historia.leitores)
        self.total_comentarios = sum(len(c.comentarios) for c in historia.capitulos)
        
        if historia.capitulos:
            self.capitulos_populares = sorted(
                historia.capitulos,
                key=lambda c: len(c.comentarios),
                reverse=True
            )[:3]
    
    def __str__(self) -> str:
        return f"Leitores: {self.total_leitores} | Comentários: {self.total_comentarios} | Capítulos populares: {len(self.capitulos_populares)}"


class Autor(Usuario):
    """
    Autor do StoryFlow - herda tudo de Usuario
    Especialização: foco em publicar e gerenciar conteúdo
    """
    
    def __init__(self, id: str, nome: str, email: str, senha: str):
        # Chama o construtor da classe pai
        super().__init__(id, nome, email, senha)
        
        # Atributos específicos do Autor
        self.historias_publicadas: List[Historia] = []
        self.estatisticas = PainelEstatisticas()
        self.rascunhos: List[Capitulo] = []  # capítulos não publicados
    
    # IMPLEMENTAÇÃO DOS MÉTODOS ABSTRATOS 
    
    def get_tipo_usuario(self) -> str:
        return "autor"
    
    def get_acoes_permitidas(self) -> List[str]:
        return [
            "publicar_historias",
            "editar_conteudo",
            "responder_comentarios",
            "ver_estatisticas",
            "seguir_outros_autores",
            "receber_notificacoes_de_seguidores"
        ]
    
    # MÉTODOS ESPECÍFICOS DO AUTOR 
    
    def publicar_historia(self, historia: Historia) -> None:
        """Publica uma nova história"""
        self.historias_publicadas.append(historia)
        historia.autor = self
        print(f"📚 {self.nome} publicou a história '{historia.titulo}'")
    
    def publicar_capitulo(self, historia: Historia, capitulo: Capitulo) -> None:
        if historia not in self.historias_publicadas:
            print(f"❌ Erro: '{historia.titulo}' não pertence a {self.nome}")
            return
        
        historia.adicionar_capitulo(capitulo)
        
        # Notifica todos os seguidores (usando o método herdado)
        for seguidor in self.autores_seguidos:
            if isinstance(seguidor, Usuario):  # Pode ser Leitor ou Autor
                notificacao = Notificacao(
                    id=f"notif_{datetime.now().timestamp()}",
                    usuario=seguidor,
                    mensagem=f"📖 Novo capítulo! '{historia.titulo}' - {capitulo.titulo}",
                    tipo=TipoNotificacao.NOVO_CAPITULO
                )
                seguidor.adicionar_notificacao(notificacao)
        
        print(f"✍️ {self.nome} publicou '{capitulo.titulo}' em '{historia.titulo}'")
    
    def editar_historia(self, historia: Historia, novo_titulo: str = None, 
                        nova_descricao: str = None) -> None:
        if historia not in self.historias_publicadas:
            print(f"❌ Erro: '{historia.titulo}' não pertence a {self.nome}")
            return
        
        if novo_titulo:
            historia.titulo = novo_titulo
        if nova_descricao:
            historia.descricao = nova_descricao
        print(f"✏️ {self.nome} editou a história '{historia.titulo}'")
    
    def editar_capitulo(self, historia: Historia, capitulo: Capitulo, 
                        novo_conteudo: str = None, novoTitulo: str = None) -> None:
        if historia not in self.historias_publicadas:
            print(f"❌ Erro: '{historia.titulo}' não pertence a {self.nome}")
            return
        
        if novo_conteudo:
            capitulo.conteudo = novo_conteudo
            capitulo.tempo_estimado_leitura_min = capitulo._calcular_tempo_leitura()
        if novoTitulo:
            capitulo.titulo = novoTitulo
        
        print(f"✏️ {self.nome} editou o capítulo '{capitulo.titulo}'")
    
    def salvar_rascunho(self, capitulo: Capitulo) -> None:
        self.rascunhos.append(capitulo)
        print(f"📝 Rascunho salvo: '{capitulo.titulo}'")
    
    def atualizar_estatisticas(self) -> None:
        for historia in self.historias_publicadas:
            self.estatisticas.atualizar(historia)
    
    def responder_comentario(self, comentario: 'Comentario', resposta_conteudo: str) -> 'Comentario':
        import uuid
        
        resposta = comentario.responder(
            id=str(uuid.uuid4()),
            usuario=self,
            conteudo=resposta_conteudo
        )
        print(f"💬 {self.nome} respondeu a um comentário: {resposta_conteudo[:50]}...")
        return resposta
    
    def marcar_historia_concluida(self, historia: Historia) -> None:
        if historia not in self.historias_publicadas:
            print(f"❌ Erro: '{historia.titulo}' não pertence a {self.nome}")
            return
        historia.marcar_como_concluida()
        print(f"🏁 '{historia.titulo}' foi marcada como CONCLUÍDA")
    
    def get_historias_por_status(self, status: str) -> List[Historia]:
        from models.historia import StatusHistoria
        status_map = {
            "em_andamento": StatusHistoria.EM_ANDAMENTO,
            "concluida": StatusHistoria.CONCLUIDA,
            "abandonada": StatusHistoria.ABANDONADA
        }
        target = status_map.get(status)
        return [h for h in self.historias_publicadas if h.status == target]
    
    def __str__(self) -> str:
        return f"✍️ Autor: {self.nome} | {len(self.historias_publicadas)} histórias | {len(self.autores_seguidos)} seguidores"
