"""
Módulo de Leitor - Subtipo de usuário especializado em leitura.
Implementa: Herança de Usuario, Polimorfismo em exibir_painel().
"""
import uuid
from datetime import datetime
from typing import List
from .usuario import Usuario
from .biblioteca import Biblioteca


class Leitor(Usuario): # ← herança
    """
    Classe especializada em leitura.
    Implementa herança: herda de Usuario e implementa exibir_painel().
    """
    
    def __init__(self, id_usuario: str, nome: str, email: str, senha: str):
        """
        Args:
            id_usuario: Identificador único
            nome: Nome do leitor
            email: Email único
            senha: Senha de acesso
        """
        super().__init__(id_usuario, nome, email, senha) 
        self.biblioteca = Biblioteca(self)
        self._avaliacoes: List['Avaliacao'] = []
        self._comentarios: List['Comentario'] = []
        self.progresso_leitura: dict = {}  # {historia_id: {percentual, capitulo_id, capitulo_titulo, atualizado_em}}
        self.sessoes_leitura: dict = {}

    def exibir_painel(self) -> str:
        """
        Implementação polimórfica: Painel específico do leitor.
        """
        lendo = len(self.biblioteca.obter_continuar_lendo())
        concluidos = len(self.biblioteca.obter_concluidos())
        favoritos = len(self.biblioteca.obter_favoritos())
        return (f"📚 Painel do Leitor: {lendo} lendo | "
                f"{concluidos} concluídos | {favoritos} favoritos")

    def avaliar_conteudo(self, alvo: 'Union[Historia, Capitulo]', 
                        nota: int, tipo: 'TipoAvaliacao') -> 'Avaliacao':
        """
        Avalia uma história ou capítulo.
        Implementa polimorfismo: alvo pode ser Historia ou Capitulo.
        """
        from .avaliacao import Avaliacao
        av = Avaliacao(
            id=str(uuid.uuid4()),
            usuario=self,
            nota=nota,
            tipo=tipo
        )
        alvo.adicionar_avaliacao(av)
        self._avaliacoes.append(av)
        return av

    def comentar(self, capitulo: 'Capitulo', texto: str) -> 'Comentario':
        """Adiciona um comentário em um capítulo."""
        from .comentario import Comentario
        coment = Comentario(
            id=str(uuid.uuid4()),
            usuario=self,
            conteudo=texto,
            capitulo_id=capitulo.id
        )
        capitulo.adicionar_comentario(coment)
        self._comentarios.append(coment)
        return coment

    def atualizar_progresso(
        self,
        historia_id: str,
        percentual: float,
        capitulo_id: str | None = None,
        capitulo_titulo: str | None = None,
    ):
        """Atualiza o progresso de leitura de uma história."""
        if 0 <= percentual <= 100:
            self.progresso_leitura[historia_id] = {
                'percentual': percentual,
                'capitulo_id': capitulo_id,
                'capitulo_titulo': capitulo_titulo,
            }

    def obter_progresso(self, historia_id: str) -> dict | None:
        """Retorna o progresso salvo para uma história."""
        return self.progresso_leitura.get(historia_id)

    def listar_progresso(self) -> list[dict]:
        """Lista todo o progresso de leitura salvo."""
        return [
            {'historia_id': historia_id, **dados}
            for historia_id, dados in self.progresso_leitura.items()
        ]

    def registrar_tempo_leitura(
        self,
        historia_id: str,
        capitulo_id: str,
        pagina_global: int,
        segundos: int,
        sessao_id: str | None = None,
    ) -> dict:
        """Acumula tempo de leitura por página, capítulo e história."""
        try:
            segundos = int(segundos)
            pagina_global = int(pagina_global)
        except (TypeError, ValueError):
            segundos = 0
            pagina_global = 0

        if not historia_id or not capitulo_id or segundos <= 0:
            return self.obter_tempo_leitura(historia_id)

        historia = self.sessoes_leitura.setdefault(historia_id, {
            'total_segundos': 0,
            'capitulos': {},
            'sessoes': {},
        })
        historia.setdefault('capitulos', {})
        historia.setdefault('sessoes', {})

        capitulo = historia['capitulos'].setdefault(capitulo_id, {
            'total_segundos': 0,
            'paginas': {},
        })
        pagina_chave = str(max(1, pagina_global))
        capitulo['paginas'][pagina_chave] = capitulo['paginas'].get(pagina_chave, 0) + segundos
        capitulo['total_segundos'] += segundos
        historia['total_segundos'] += segundos

        sessao_normalizada = str(sessao_id or '').strip()
        if sessao_normalizada:
            agora = datetime.now().isoformat()
            sessao = historia['sessoes'].setdefault(sessao_normalizada, {
                'id': sessao_normalizada,
                'iniciada_em': agora,
                'atualizada_em': agora,
                'total_segundos': 0,
                'capitulos': {},
                'paginas': {},
            })
            sessao['atualizada_em'] = agora
            sessao['total_segundos'] = int(sessao.get('total_segundos', 0)) + segundos
            sessao['capitulos'][capitulo_id] = int(sessao['capitulos'].get(capitulo_id, 0)) + segundos
            sessao['paginas'][pagina_chave] = int(sessao['paginas'].get(pagina_chave, 0)) + segundos

        return self.obter_tempo_leitura(historia_id)

    def obter_tempo_leitura(self, historia_id: str | None = None) -> dict:
        """Retorna o tempo acumulado de leitura."""
        if historia_id:
            return self.sessoes_leitura.get(historia_id, {'total_segundos': 0, 'capitulos': {}, 'sessoes': {}})
        return self.sessoes_leitura

    def obter_avaliacoes(self) -> List['Avaliacao']:
        """Retorna todas as avaliações do leitor."""
        return self._avaliacoes

    def obter_comentarios(self) -> List['Comentario']:
        """Retorna todos os comentários do leitor."""
        return self._comentarios

    def __str__(self) -> str:
        return f"Leitor: {self.nome}"

    def __repr__(self) -> str:
        return f"<Leitor {self.id_usuario} {self.nome}>"
