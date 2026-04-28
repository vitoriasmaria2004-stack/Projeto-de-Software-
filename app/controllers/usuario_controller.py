"""
Controllers para gerenciar usuários, autenticação e experiências híbridas.
"""
import uuid
from datetime import datetime
from app.models.leitor import Leitor
from app.models.autor import Autor
from app.models.biblioteca import CategoriaBiblioteca


# Armazenamento em memória
usuarios_db = {}
contas_db = {}
sessoes_db = {}


class UsuarioController:
    """Controller para gerenciamento de usuários."""

    @staticmethod
    def _limpar_texto(valor: str) -> str:
        """Normaliza campos textuais recebidos pela API."""
        return valor.strip() if isinstance(valor, str) else ""

    @classmethod
    def _validar_dados_usuario(cls, nome: str, email: str, senha: str):
        """Valida e normaliza os dados básicos de um usuário."""
        nome = cls._limpar_texto(nome)
        email = cls._limpar_texto(email).lower()
        senha = cls._limpar_texto(senha)

        if not nome:
            return {'sucesso': False, 'erro': 'Nome é obrigatório', 'codigo': 400}
        if not email:
            return {'sucesso': False, 'erro': 'Email é obrigatório', 'codigo': 400}
        if '@' not in email or '.' not in email.split('@')[-1]:
            return {'sucesso': False, 'erro': 'Email inválido', 'codigo': 400}
        if not senha:
            return {'sucesso': False, 'erro': 'Senha é obrigatória', 'codigo': 400}

        return nome, email, senha

    @staticmethod
    def _parse_categoria(categoria: str):
        """Converte o texto recebido em uma categoria de biblioteca."""
        categoria_normalizada = UsuarioController._limpar_texto(categoria).casefold()
        mapa = {
            'favoritos': CategoriaBiblioteca.FAVORITOS,
            'favorito': CategoriaBiblioteca.FAVORITOS,
            'lendo': CategoriaBiblioteca.LENDO,
            'concluidos': CategoriaBiblioteca.CONCLUIDOS,
            'concluídos': CategoriaBiblioteca.CONCLUIDOS,
            'pausados': CategoriaBiblioteca.PAUSADOS,
            'pausado': CategoriaBiblioteca.PAUSADOS,
        }
        return mapa.get(categoria_normalizada)

    @staticmethod
    def _buscar_conta_por_email(email: str):
        """Busca uma conta por email."""
        email_normalizado = UsuarioController._limpar_texto(email).lower()
        for conta in contas_db.values():
            if conta['email'] == email_normalizado:
                return conta
        return None

    @staticmethod
    def _criar_sessao(conta_id: str) -> str:
        """Cria um token de sessão para a conta."""
        token = str(uuid.uuid4())
        sessoes_db[token] = conta_id
        return token

    @staticmethod
    def _serializar_conta(conta: dict) -> dict:
        """Converte uma conta para resposta pública."""
        return {
            'id': conta['id'],
            'nome': conta['nome'],
            'email': conta['email'],
            'leitor_id': conta['leitor_id'],
            'autor_id': conta['autor_id'],
            'foto_perfil': conta.get('foto_perfil'),
            'data_criacao': conta['data_criacao'],
        }

    @staticmethod
    def _obter_contexto_autenticado(token: str):
        """Valida o token e retorna conta, leitor e autor associados."""
        token = UsuarioController._limpar_texto(token)
        if not token:
            return {'sucesso': False, 'erro': 'Token é obrigatório', 'codigo': 401}

        conta_id = sessoes_db.get(token)
        if not conta_id:
            return {'sucesso': False, 'erro': 'Sessão inválida ou expirada', 'codigo': 401}

        conta = contas_db.get(conta_id)
        if not conta:
            sessoes_db.pop(token, None)
            return {'sucesso': False, 'erro': 'Conta não encontrada para esta sessão', 'codigo': 401}

        leitor = usuarios_db.get(conta['leitor_id'])
        autor = usuarios_db.get(conta['autor_id'])
        if not isinstance(leitor, Leitor) or not isinstance(autor, Autor):
            return {'sucesso': False, 'erro': 'Conta inconsistente. Refaça o login.', 'codigo': 500}

        return {
            'sucesso': True,
            'conta': conta,
            'leitor': leitor,
            'autor': autor,
        }

    @staticmethod
    def obter_conta_por_email(email: str):
        """Retorna os dados públicos de uma conta pelo email."""
        conta = UsuarioController._buscar_conta_por_email(email)
        if not conta:
            return None
        return UsuarioController._serializar_conta(conta)

    @staticmethod
    def validar_token(token: str) -> dict:
        """Valida um token e retorna os dados da conta."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto

        return {
            'sucesso': True,
            'conta': UsuarioController._serializar_conta(contexto['conta']),
        }

    @staticmethod
    def contexto_por_token(token: str):
        """Retorna o contexto autenticado completo para uso interno (middleware)."""
        return UsuarioController._obter_contexto_autenticado(token)

    @staticmethod
    def registrar_conta(nome: str, email: str, senha: str) -> dict:
        """Registra uma conta que já nasce com perfil de leitor e autor."""
        dados_validados = UsuarioController._validar_dados_usuario(nome, email, senha)
        if isinstance(dados_validados, dict):
            return dados_validados

        nome, email, senha = dados_validados
        if UsuarioController._buscar_conta_por_email(email):
            return {'sucesso': False, 'erro': 'Já existe uma conta com este email', 'codigo': 409}

        leitor_resp = UsuarioController.criar_leitor(nome, email, senha, permitir_email_repetido=True)
        if not leitor_resp['sucesso']:
            return leitor_resp

        autor_resp = UsuarioController.criar_autor(nome, email, senha, permitir_email_repetido=True)
        if not autor_resp['sucesso']:
            usuarios_db.pop(leitor_resp.get('id'), None)
            return autor_resp

        conta_id = str(uuid.uuid4())
        conta = {
            'id': conta_id,
            'nome': nome,
            'email': email,
            'senha': senha,
            'leitor_id': leitor_resp['id'],
            'autor_id': autor_resp['id'],
            'foto_perfil': None,
            'data_criacao': datetime.now().isoformat(),
        }
        contas_db[conta_id] = conta

        token = UsuarioController._criar_sessao(conta_id)
        return {
            'sucesso': True,
            'mensagem': f'Conta de "{nome}" criada com sucesso!',
            'token': token,
            'conta': UsuarioController._serializar_conta(conta),
        }

    @staticmethod
    def login(email: str, senha: str) -> dict:
        """Realiza o login de uma conta existente."""
        email = UsuarioController._limpar_texto(email).lower()
        senha = UsuarioController._limpar_texto(senha)
        if not email or not senha:
            return {'sucesso': False, 'erro': 'Email e senha são obrigatórios', 'codigo': 400}

        conta = UsuarioController._buscar_conta_por_email(email)
        if not conta or conta['senha'] != senha:
            return {'sucesso': False, 'erro': 'Credenciais inválidas', 'codigo': 401}

        token = UsuarioController._criar_sessao(conta['id'])
        return {
            'sucesso': True,
            'mensagem': f'Bem-vindo de volta, {conta["nome"]}!',
            'token': token,
            'conta': UsuarioController._serializar_conta(conta),
        }

    @staticmethod
    def logout(token: str) -> dict:
        """Encerra a sessão atual."""
        token = UsuarioController._limpar_texto(token)
        if not token:
            return {'sucesso': False, 'erro': 'Token é obrigatório', 'codigo': 400}

        if token in sessoes_db:
            sessoes_db.pop(token, None)
            return {'sucesso': True, 'mensagem': 'Sessão encerrada com sucesso.'}

        return {'sucesso': False, 'erro': 'Sessão não encontrada', 'codigo': 401}

    @staticmethod
    def atualizar_foto_perfil(token: str, foto_perfil: str | None) -> dict:
        """Atualiza a foto de perfil da conta autenticada."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto

        conta = contexto['conta']
        foto = foto_perfil if isinstance(foto_perfil, str) else ''
        foto = foto.strip()

        if foto:
            if len(foto) > 2_000_000:
                return {'sucesso': False, 'erro': 'Imagem muito grande. Use até 2MB.', 'codigo': 400}

            if not (
                foto.startswith('data:image/')
                or foto.startswith('https://')
                or foto.startswith('http://')
            ):
                return {'sucesso': False, 'erro': 'Formato de foto inválido', 'codigo': 400}

            conta['foto_perfil'] = foto
            mensagem = 'Foto de perfil atualizada com sucesso.'
        else:
            conta['foto_perfil'] = None
            mensagem = 'Foto de perfil removida com sucesso.'

        return {
            'sucesso': True,
            'mensagem': mensagem,
            'conta': UsuarioController._serializar_conta(conta),
        }

    @staticmethod
    def obter_painel_hibrido(token: str) -> dict:
        """Retorna um painel único de leitura e autoria para a conta logada."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto

        conta = contexto['conta']
        from app.controllers.historia_controller import HistoriaController

        leitura = UsuarioController.obter_painel_leitura(conta['leitor_id'])
        if not leitura['sucesso']:
            return leitura

        autoria = HistoriaController.listar_historias_por_autor(
            conta['autor_id'],
            leitor_id=conta['leitor_id'],
            incluir_capitulos=True,
        )
        if not autoria['sucesso']:
            return autoria

        return {
            'sucesso': True,
            'conta': UsuarioController._serializar_conta(conta),
            'leitura': {
                'leitor': leitura['leitor'],
                'progresso': leitura['progresso'],
                'biblioteca': leitura['biblioteca'],
                'recomendacoes': leitura['recomendacoes'],
                'marcacoes': leitura.get('marcacoes', []),
            },
            'autoria': {
                'total': autoria['total'],
                'historias': autoria['historias'],
            },
        }

    @staticmethod
    def listar_minhas_historias(token: str) -> dict:
        """Lista as histórias publicadas pela conta autenticada."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto

        conta = contexto['conta']
        from app.controllers.historia_controller import HistoriaController
        return HistoriaController.listar_historias_por_autor(
            conta['autor_id'],
            leitor_id=conta['leitor_id'],
            incluir_capitulos=True,
            incluir_conteudo_capitulos=True,
        )

    @staticmethod
    def publicar_historia(token: str, titulo: str, sinopse: str, genero: str, capa: str | None = None, epub_data: str | None = None, preview_video: str | None = None) -> dict:
        """Publica uma nova história usando o perfil de autor da conta logada.
        Suporta envio de EPUB e vídeo de preview (data URLs) para criação automática de capítulos.
        """
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto

        conta = contexto['conta']
        from app.controllers.historia_controller import HistoriaController
        if preview_video:
            preview_ok, _, preview_erro = HistoriaController._validar_preview_video(preview_video)
            if not preview_ok:
                return {'sucesso': False, 'erro': preview_erro or 'Preview inválido', 'codigo': 400}
        if epub_data:
            return HistoriaController.criar_historia_com_epub(
                titulo, sinopse, genero, conta['autor_id'], capa=capa, epub_data=epub_data, preview_video=preview_video
            )
        return HistoriaController.criar_historia(titulo, sinopse, genero, conta['autor_id'], capa=capa)

    @staticmethod
    def consultar_metadados_epub_por_token(token: str, epub_data: str) -> dict:
        """Consulta metadados de EPUB para pré-preenchimento no fluxo de criação."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto
        from app.controllers.historia_controller import HistoriaController
        return HistoriaController.consultar_metadados_epub(epub_data)

    @staticmethod
    def editar_historia_por_token(token: str, historia_id: str, titulo: str, sinopse: str, genero: str, capa: str | None = None) -> dict:
        """Edita dados de uma história da própria conta."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto

        conta = contexto['conta']
        from app.controllers.historia_controller import historias_db, HistoriaController

        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}
        if not historia.autor or historia.autor.id_usuario != conta['autor_id']:
            return {'sucesso': False, 'erro': 'Você só pode editar suas próprias histórias', 'codigo': 403}

        return HistoriaController.editar_historia(historia_id, titulo, sinopse, genero, capa=capa)

    @staticmethod
    def adicionar_capitulo_por_token(token: str, historia_id: str, titulo: str, conteudo: str) -> dict:
        """Adiciona capítulo em uma história da própria conta."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto

        conta = contexto['conta']
        from app.controllers.historia_controller import historias_db, HistoriaController

        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}
        if not historia.autor or historia.autor.id_usuario != conta['autor_id']:
            return {'sucesso': False, 'erro': 'Você só pode editar suas próprias histórias', 'codigo': 403}

        return HistoriaController.adicionar_capitulo(historia_id, titulo, conteudo)

    @staticmethod
    def editar_capitulo_por_token(token: str, historia_id: str, capitulo_id: str, titulo: str, conteudo: str) -> dict:
        """Edita capítulo em uma história da própria conta."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto

        conta = contexto['conta']
        from app.controllers.historia_controller import historias_db, HistoriaController

        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}
        if not historia.autor or historia.autor.id_usuario != conta['autor_id']:
            return {'sucesso': False, 'erro': 'Você só pode editar suas próprias histórias', 'codigo': 403}

        return HistoriaController.editar_capitulo(historia_id, capitulo_id, titulo, conteudo)

    @staticmethod
    def excluir_capitulo_por_token(token: str, historia_id: str, capitulo_id: str) -> dict:
        """Exclui capítulo em uma história da própria conta."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto

        conta = contexto['conta']
        from app.controllers.historia_controller import historias_db, HistoriaController

        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}
        if not historia.autor or historia.autor.id_usuario != conta['autor_id']:
            return {'sucesso': False, 'erro': 'Você só pode editar suas próprias histórias', 'codigo': 403}

        return HistoriaController.excluir_capitulo(historia_id, capitulo_id)

    @staticmethod
    def salvar_na_biblioteca(token: str, historia_id: str, categoria: str) -> dict:
        """Salva/move história na biblioteca do leitor da conta."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto
        conta = contexto['conta']
        return UsuarioController.adicionar_historia_biblioteca(conta['leitor_id'], historia_id, categoria)

    @staticmethod
    def atualizar_progresso_por_token(token: str, historia_id: str, percentual: float, capitulo_id: str | None = None) -> dict:
        """Atualiza progresso de leitura da conta logada."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto
        conta = contexto['conta']
        return UsuarioController.atualizar_progresso(conta['leitor_id'], historia_id, percentual, capitulo_id)

    @staticmethod
    def avaliar_historia_por_token(token: str, historia_id: str, nota: int) -> dict:
        """Avalia uma história com o perfil de leitor da conta."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto
        conta = contexto['conta']
        from app.controllers.historia_controller import HistoriaController
        return HistoriaController.avaliar_historia(historia_id, conta['leitor_id'], nota)

    @staticmethod
    def comentar_capitulo_por_token(token: str, historia_id: str, capitulo_id: str, conteudo: str) -> dict:
        """Comenta em capítulo com o perfil de leitor da conta."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto
        conta = contexto['conta']
        from app.controllers.historia_controller import HistoriaController
        return HistoriaController.comentar_capitulo(historia_id, capitulo_id, conta['leitor_id'], conteudo)

    @staticmethod
    def destacar_trecho_por_token(token: str, historia_id: str, capitulo_id: str, trecho: str) -> dict:
        """Destaca um trecho de capítulo com o perfil de leitor autenticado."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto
        conta = contexto['conta']
        from app.controllers.historia_controller import HistoriaController
        return HistoriaController.destacar_trecho(historia_id, capitulo_id, conta['leitor_id'], trecho)

    @staticmethod
    def remover_destaque_por_token(token: str, historia_id: str, capitulo_id: str, trecho: str) -> dict:
        """Remove uma marcação do perfil de leitor autenticado."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto
        conta = contexto['conta']
        from app.controllers.historia_controller import HistoriaController
        return HistoriaController.remover_destaque(historia_id, capitulo_id, conta['leitor_id'], trecho)

    @staticmethod
    def registrar_tempo_leitura_por_token(
        token: str,
        historia_id: str,
        capitulo_id: str,
        pagina_global: int,
        segundos: int,
        sessao_id: str | None = None,
    ) -> dict:
        """Registra tempo de leitura acumulado para a conta logada."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto
        leitor = contexto['leitor']

        from app.controllers.historia_controller import historias_db, HistoriaController
        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}
        if not HistoriaController._buscar_capitulo(historia, capitulo_id):
            return {'sucesso': False, 'erro': 'Capítulo não encontrado', 'codigo': 404}

        tempo = leitor.registrar_tempo_leitura(
            historia_id,
            capitulo_id,
            pagina_global,
            segundos,
            sessao_id=sessao_id,
        )
        return {
            'sucesso': True,
            'mensagem': 'Tempo de leitura registrado.',
            'tempo_leitura': tempo,
        }

    @staticmethod
    def editar_comentario_por_token(
        token: str,
        historia_id: str,
        capitulo_id: str,
        comentario_id: str,
        conteudo: str,
    ) -> dict:
        """Edita comentário com o perfil de leitor da conta autenticada."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto
        conta = contexto['conta']
        from app.controllers.historia_controller import HistoriaController
        return HistoriaController.editar_comentario(
            historia_id,
            capitulo_id,
            comentario_id,
            conta['leitor_id'],
            conteudo,
        )

    @staticmethod
    def excluir_comentario_por_token(
        token: str,
        historia_id: str,
        capitulo_id: str,
        comentario_id: str,
    ) -> dict:
        """Exclui comentário com o perfil de leitor da conta autenticada."""
        contexto = UsuarioController._obter_contexto_autenticado(token)
        if not contexto['sucesso']:
            return contexto
        conta = contexto['conta']
        from app.controllers.historia_controller import HistoriaController
        return HistoriaController.excluir_comentario(
            historia_id,
            capitulo_id,
            comentario_id,
            conta['leitor_id'],
        )

    @staticmethod
    def serializar_leitor(leitor: Leitor) -> dict:
        """Converte um leitor para JSON."""
        return {
            'id': leitor.id_usuario,
            'nome': leitor.nome,
            'email': leitor.email,
            'tipo': leitor.__class__.__name__,
            'painel': leitor.exibir_painel(),
            'biblioteca_total': leitor.biblioteca.obter_total_historias(),
            'progresso_total': len(leitor.progresso_leitura),
            'tempo_leitura': leitor.obter_tempo_leitura(),
        }

    @staticmethod
    def criar_leitor(nome: str, email: str, senha: str, permitir_email_repetido: bool = False) -> dict:
        """Cria um novo leitor."""
        try:
            dados_validados = UsuarioController._validar_dados_usuario(nome, email, senha)
            if isinstance(dados_validados, dict):
                return dados_validados

            nome, email, senha = dados_validados

            if not permitir_email_repetido:
                for usuario in usuarios_db.values():
                    if usuario.email.lower() == email:
                        return {'sucesso': False, 'erro': 'Email já registrado', 'codigo': 409}

            usuario_id = str(uuid.uuid4())
            leitor = Leitor(usuario_id, nome, email, senha)
            usuarios_db[usuario_id] = leitor

            return {
                'sucesso': True,
                'id': usuario_id,
                'tipo': 'Leitor',
                'mensagem': f'Leitor "{nome}" criado com sucesso!'
            }
        except Exception as e:
            return {'sucesso': False, 'erro': str(e), 'codigo': 500}

    @staticmethod
    def criar_autor(nome: str, email: str, senha: str, permitir_email_repetido: bool = False) -> dict:
        """Cria um novo autor."""
        try:
            dados_validados = UsuarioController._validar_dados_usuario(nome, email, senha)
            if isinstance(dados_validados, dict):
                return dados_validados

            nome, email, senha = dados_validados

            if not permitir_email_repetido:
                for usuario in usuarios_db.values():
                    if usuario.email.lower() == email:
                        return {'sucesso': False, 'erro': 'Email já registrado', 'codigo': 409}

            usuario_id = str(uuid.uuid4())
            autor = Autor(usuario_id, nome, email, senha)
            usuarios_db[usuario_id] = autor

            return {
                'sucesso': True,
                'id': usuario_id,
                'tipo': 'Autor',
                'mensagem': f'Autor "{nome}" criado com sucesso!'
            }
        except Exception as e:
            return {'sucesso': False, 'erro': str(e), 'codigo': 500}

    @staticmethod
    def listar_usuarios() -> dict:
        """Lista todos os usuários."""
        usuarios_lista = []
        for usuario in usuarios_db.values():
            usuarios_lista.append({
                'id': usuario.id_usuario,
                'nome': usuario.nome,
                'email': usuario.email,
                'tipo': usuario.__class__.__name__
            })

        return {
            'sucesso': True,
            'total': len(usuarios_lista),
            'usuarios': usuarios_lista
        }

    @staticmethod
    def listar_leitores() -> dict:
        """Lista apenas os leitores disponíveis."""
        leitores = [
            UsuarioController.serializar_leitor(usuario)
            for usuario in usuarios_db.values()
            if isinstance(usuario, Leitor)
        ]
        leitores.sort(key=lambda leitor: leitor['nome'])

        return {
            'sucesso': True,
            'total': len(leitores),
            'leitores': leitores,
        }

    @staticmethod
    def obter_usuario(usuario_id: str) -> dict:
        """Obtém informações de um usuário."""
        usuario = usuarios_db.get(usuario_id)
        if not usuario:
            return {'sucesso': False, 'erro': 'Usuário não encontrado', 'codigo': 404}

        return {
            'sucesso': True,
            'usuario': {
                'id': usuario.id_usuario,
                'nome': usuario.nome,
                'email': usuario.email,
                'tipo': usuario.__class__.__name__,
                'painel': usuario.exibir_painel(),
                'data_criacao': usuario.data_criacao.isoformat()
            }
        }

    @staticmethod
    def obter_notificacoes(usuario_id: str) -> dict:
        """Obtém notificações de um usuário."""
        usuario = usuarios_db.get(usuario_id)
        if not usuario:
            return {'sucesso': False, 'erro': 'Usuário não encontrado', 'codigo': 404}

        notificacoes = []
        for notif in usuario.obter_notificacoes():
            notificacoes.append({
                'id': notif.id,
                'titulo': notif.obter_titulo_formatado(),
                'mensagem': notif.obter_mensagem(),
                'tipo': notif.tipo.value,
                'lida': notif.lida,
                'data': notif.data_criacao.isoformat()
            })

        return {
            'sucesso': True,
            'total': len(notificacoes),
            'notificacoes': notificacoes
        }

    @staticmethod
    def obter_biblioteca(usuario_id: str) -> dict:
        """Obtém a biblioteca detalhada de um leitor."""
        usuario = usuarios_db.get(usuario_id)
        if not usuario:
            return {'sucesso': False, 'erro': 'Usuário não encontrado', 'codigo': 404}
        if not isinstance(usuario, Leitor):
            return {'sucesso': False, 'erro': 'O usuário informado não é um leitor', 'codigo': 400}

        from app.controllers.historia_controller import HistoriaController

        categorias = {}
        for categoria in CategoriaBiblioteca:
            historias = usuario.biblioteca.obter_historias_por_categoria(categoria)
            categorias[categoria.value] = [
                HistoriaController.serializar_historia(historia, incluir_capitulos=False, leitor_id=usuario_id)
                for historia in historias
            ]

        return {
            'sucesso': True,
            'biblioteca': {
                'total': usuario.biblioteca.obter_total_historias(),
                'lendo': len(usuario.biblioteca.obter_continuar_lendo()),
                'concluidos': len(usuario.biblioteca.obter_concluidos()),
                'favoritos': len(usuario.biblioteca.obter_favoritos()),
                'pausados': len(usuario.biblioteca.obter_pausados()),
                'categorias': categorias,
            }
        }

    @staticmethod
    def adicionar_historia_biblioteca(usuario_id: str, historia_id: str, categoria: str) -> dict:
        """Adiciona ou move uma história para uma categoria da biblioteca."""
        usuario = usuarios_db.get(usuario_id)
        if not isinstance(usuario, Leitor):
            return {'sucesso': False, 'erro': 'Leitor não encontrado', 'codigo': 404}

        categoria_enum = UsuarioController._parse_categoria(categoria)
        if not categoria_enum:
            return {'sucesso': False, 'erro': 'Categoria inválida', 'codigo': 400}

        from app.controllers.historia_controller import historias_db, HistoriaController

        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}

        usuario.biblioteca.definir_categoria(historia, categoria_enum)

        progresso_existente = usuario.obter_progresso(historia_id)
        if categoria_enum == CategoriaBiblioteca.CONCLUIDOS:
            ultimo_capitulo = historia.obter_ultimo_capitulo()
            usuario.atualizar_progresso(
                historia_id,
                100,
                capitulo_id=ultimo_capitulo.id if ultimo_capitulo else None,
                capitulo_titulo=ultimo_capitulo.titulo if ultimo_capitulo else None,
            )
        elif categoria_enum == CategoriaBiblioteca.LENDO and not progresso_existente:
            primeiro_capitulo = historia.capitulos[0] if historia.capitulos else None
            usuario.atualizar_progresso(
                historia_id,
                5,
                capitulo_id=primeiro_capitulo.id if primeiro_capitulo else None,
                capitulo_titulo=primeiro_capitulo.titulo if primeiro_capitulo else None,
            )

        return {
            'sucesso': True,
            'mensagem': f'"{historia.titulo}" foi salva em {categoria_enum.value}.',
            'historia': HistoriaController.serializar_historia(historia, incluir_capitulos=False, leitor_id=usuario_id),
            'categoria': categoria_enum.value,
        }

    @staticmethod
    def atualizar_progresso(usuario_id: str, historia_id: str, percentual: float, capitulo_id: str | None = None) -> dict:
        """Atualiza o progresso de leitura de uma obra."""
        usuario = usuarios_db.get(usuario_id)
        if not isinstance(usuario, Leitor):
            return {'sucesso': False, 'erro': 'Leitor não encontrado', 'codigo': 404}

        from app.controllers.historia_controller import historias_db, HistoriaController

        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}

        try:
            percentual = float(percentual)
        except (TypeError, ValueError):
            return {'sucesso': False, 'erro': 'Percentual inválido', 'codigo': 400}

        if percentual < 0 or percentual > 100:
            return {'sucesso': False, 'erro': 'O percentual deve ficar entre 0 e 100', 'codigo': 400}

        capitulo = None
        if capitulo_id:
            capitulo = HistoriaController._buscar_capitulo(historia, capitulo_id)
            if not capitulo:
                return {'sucesso': False, 'erro': 'Capítulo não encontrado', 'codigo': 404}

        usuario.atualizar_progresso(
            historia_id,
            percentual,
            capitulo_id=capitulo.id if capitulo else None,
            capitulo_titulo=capitulo.titulo if capitulo else None,
        )
        historia.adicionar_leitor(usuario)

        if percentual >= 100:
            usuario.biblioteca.definir_categoria(historia, CategoriaBiblioteca.CONCLUIDOS)
        else:
            usuario.biblioteca.definir_categoria(historia, CategoriaBiblioteca.LENDO)

        return {
            'sucesso': True,
            'mensagem': 'Progresso atualizado com sucesso!',
            'progresso': usuario.obter_progresso(historia_id),
            'historia': HistoriaController.serializar_historia(historia, incluir_capitulos=False, leitor_id=usuario_id),
        }

    @staticmethod
    def obter_painel_leitura(usuario_id: str) -> dict:
        """Retorna o painel completo do leitor."""
        usuario = usuarios_db.get(usuario_id)
        if not isinstance(usuario, Leitor):
            return {'sucesso': False, 'erro': 'Leitor não encontrado', 'codigo': 404}

        from app.controllers.historia_controller import historias_db, HistoriaController

        progresso = []
        for item in usuario.listar_progresso():
            historia = historias_db.get(item['historia_id'])
            if not historia:
                continue
            progresso.append({
                'historia': HistoriaController.serializar_historia(historia, incluir_capitulos=False, leitor_id=usuario_id),
                'percentual': item['percentual'],
                'capitulo_id': item.get('capitulo_id'),
                'capitulo_titulo': item.get('capitulo_titulo'),
            })

        progresso.sort(key=lambda item: item['percentual'], reverse=True)

        biblioteca = UsuarioController.obter_biblioteca(usuario_id)
        recomendacoes = UsuarioController.obter_recomendacoes(usuario_id)
        marcacoes = []

        for historia in historias_db.values():
            for capitulo in historia.capitulos:
                for destaque in capitulo.destaques.values():
                    usuarios = destaque.get('usuarios', [])
                    if usuario_id not in usuarios:
                        continue
                    marcacoes.append({
                        'historia_id': historia.id,
                        'historia_titulo': historia.titulo,
                        'capitulo_id': capitulo.id,
                        'capitulo_titulo': capitulo.titulo,
                        'trecho': destaque.get('trecho', ''),
                    })

        return {
            'sucesso': True,
            'leitor': UsuarioController.serializar_leitor(usuario),
            'progresso': progresso,
            'biblioteca': biblioteca.get('biblioteca', {}),
            'recomendacoes': recomendacoes.get('historias', []),
            'marcacoes': marcacoes[-20:],
        }

    @staticmethod
    def obter_recomendacoes(usuario_id: str, limite: int = 4) -> dict:
        """Retorna recomendações com foco em gêneros amados e bloqueio por desgosto."""
        usuario = usuarios_db.get(usuario_id)
        if not isinstance(usuario, Leitor):
            return {'sucesso': False, 'erro': 'Leitor não encontrado', 'codigo': 404}

        from app.controllers.historia_controller import historias_db, HistoriaController

        def normalizar_genero(genero: str) -> str:
            genero_limpo = UsuarioController._limpar_texto(genero)
            return genero_limpo.casefold() if genero_limpo else 'geral'

        preferencias: dict[str, float] = {}
        generos_amados: set[str] = set()
        generos_bloqueados: set[str] = set()
        minhas_notas_por_historia: dict[str, int] = {}

        # Preferências explícitas vindas de avaliação do próprio leitor.
        for historia in historias_db.values():
            genero = normalizar_genero(historia.genero)
            for avaliacao in historia.avaliacoes:
                avaliador = getattr(avaliacao, 'usuario', None)
                if not avaliador or getattr(avaliador, 'id_usuario', None) != usuario_id:
                    continue
                nota = int(getattr(avaliacao, 'nota', 0) or 0)
                if nota >= 5:
                    preferencias[genero] = preferencias.get(genero, 0) + 6.0
                    generos_amados.add(genero)
                elif nota >= 4:
                    preferencias[genero] = preferencias.get(genero, 0) + 3.0
                elif nota <= 2:
                    preferencias[genero] = preferencias.get(genero, 0) - 10.0
                    generos_bloqueados.add(genero)
                else:
                    preferencias[genero] = preferencias.get(genero, 0) + 1.0
                minhas_notas_por_historia[historia.id] = nota

        # Leitura/biblioteca entra como sinal secundário.
        for historia in usuario.biblioteca.obter_todas_as_historias():
            genero = normalizar_genero(historia.genero)
            if genero in generos_bloqueados:
                continue
            preferencias[genero] = preferencias.get(genero, 0) + 0.8

        historias_salvas = {historia.id for historia in usuario.biblioteca.obter_todas_as_historias()}
        candidatas = [
            historia for historia in historias_db.values()
            if historia.id not in historias_salvas
            and normalizar_genero(historia.genero) not in generos_bloqueados
            and (
                len(historia.avaliacoes) == 0
                or minhas_notas_por_historia.get(historia.id, 0) >= 4
            )
        ]

        def pontuacao(historia):
            genero = normalizar_genero(historia.genero)
            genero_score = preferencias.get(genero, 0) * 4
            bonus_amado = 10 if genero in generos_amados else 0
            return bonus_amado + genero_score + historia.obter_popularidade() + (historia.obter_media_avaliacoes() * 1.2)

        candidatas.sort(key=pontuacao, reverse=True)
        recomendadas = candidatas[:limite]

        return {
            'sucesso': True,
            'total': len(recomendadas),
            'historias': [
                HistoriaController.serializar_historia(historia, incluir_capitulos=False, leitor_id=usuario_id)
                for historia in recomendadas
            ]
        }
