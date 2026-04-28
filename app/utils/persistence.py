"""
Persistência do estado da aplicação em Google Firebase Firestore.

A aplicação continua funcional em memória; quando as credenciais Firebase são
fornecidas, o estado passa a ser salvo/carregado automaticamente do Firestore.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from threading import Lock

from app.models.autor import Autor
from app.models.leitor import Leitor
from app.models.historia import Historia
from app.models.capitulo import Capitulo
from app.models.avaliacao import Avaliacao, TipoAvaliacao
from app.models.comentario import Comentario
from app.models.notificacao import Notificacao, TipoNotificacao
from app.models.biblioteca import CategoriaBiblioteca

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except Exception:  # pragma: no cover - dependência opcional em runtime
    firebase_admin = None
    credentials = None
    firestore = None


_LOCK = Lock()
_CLIENT = None
_INITIALIZED = False
_STATUS = {
    'backend': 'memory',
    'ativo': False,
    'motivo': 'Firebase não inicializado',
    'project_id': None,
}


def _collection_name() -> str:
    return os.getenv('FIREBASE_COLLECTION', 'storyflow')


def _document_name() -> str:
    return os.getenv('FIREBASE_DOCUMENT', 'app_state')


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if isinstance(dt, datetime) else None


def _parse_iso(value: str | None, fallback: datetime | None = None) -> datetime:
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return fallback or datetime.now()


def _parse_categoria(nome: str | None) -> CategoriaBiblioteca | None:
    if not isinstance(nome, str):
        return None
    normalizado = nome.strip().casefold()
    mapa = {
        'favoritos': CategoriaBiblioteca.FAVORITOS,
        'lendo': CategoriaBiblioteca.LENDO,
        'concluidos': CategoriaBiblioteca.CONCLUIDOS,
        'concluídos': CategoriaBiblioteca.CONCLUIDOS,
        'pausados': CategoriaBiblioteca.PAUSADOS,
    }
    return mapa.get(normalizado)


def _parse_tipo_avaliacao(valor: str | None) -> TipoAvaliacao:
    if valor == TipoAvaliacao.CAPITULO.value:
        return TipoAvaliacao.CAPITULO
    return TipoAvaliacao.HISTORIA


def _parse_tipo_notificacao(valor: str | None) -> TipoNotificacao:
    try:
        return TipoNotificacao(valor)
    except Exception:
        return TipoNotificacao.RECOMENDACAO


def _build_firestore_client():
    """Inicializa cliente Firestore caso as credenciais estejam disponíveis."""
    global _CLIENT, _INITIALIZED, _STATUS
    if _INITIALIZED:
        return _CLIENT

    _INITIALIZED = True

    if firebase_admin is None or credentials is None or firestore is None:
        _STATUS = {
            'backend': 'memory',
            'ativo': False,
            'motivo': 'Dependência firebase-admin não instalada',
            'project_id': None,
        }
        return None

    cred_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON', '').strip()
    cred_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', '').strip() or os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '').strip()
    project_id = os.getenv('FIREBASE_PROJECT_ID', '').strip() or None

    try:
        if not firebase_admin._apps:
            cred = None
            if cred_json:
                cred = credentials.Certificate(json.loads(cred_json))
            elif cred_path:
                cred = credentials.Certificate(cred_path)

            if cred:
                options = {'projectId': project_id} if project_id else None
                firebase_admin.initialize_app(cred, options=options)
            else:
                # Suporta ambientes com credenciais padrão (ex.: Cloud Run/GCP)
                options = {'projectId': project_id} if project_id else None
                firebase_admin.initialize_app(options=options)

        _CLIENT = firestore.client()
        _STATUS = {
            'backend': 'firestore',
            'ativo': True,
            'motivo': 'Conectado',
            'project_id': project_id,
        }
        return _CLIENT
    except Exception as exc:  # pragma: no cover - depende de ambiente
        _CLIENT = None
        _STATUS = {
            'backend': 'memory',
            'ativo': False,
            'motivo': f'Falha ao iniciar Firebase: {exc}',
            'project_id': project_id,
        }
        return None


def obter_status_persistencia() -> dict:
    """Retorna o status atual da camada de persistência."""
    _build_firestore_client()
    return dict(_STATUS)


def _serializar_state(usuarios_db: dict, contas_db: dict, sessoes_db: dict, historias_db: dict) -> dict:
    senha_por_usuario = {}
    for conta in contas_db.values():
        senha = conta.get('senha')
        if senha:
            senha_por_usuario[conta.get('leitor_id')] = senha
            senha_por_usuario[conta.get('autor_id')] = senha

    usuarios_serializados = {}
    for usuario_id, usuario in usuarios_db.items():
        tipo = usuario.__class__.__name__
        dados = {
            'id': usuario_id,
            'tipo': tipo,
            'nome': usuario.nome,
            'email': usuario.email,
            'senha': senha_por_usuario.get(usuario_id),
            'data_criacao': _iso(getattr(usuario, 'data_criacao', None)),
            'notificacoes': [
                {
                    'id': notif.id,
                    'titulo': notif.titulo,
                    'mensagem': notif.obter_mensagem(),
                    'tipo': notif.tipo.value,
                    'lida': notif.lida,
                    'data_criacao': _iso(notif.data_criacao),
                }
                for notif in usuario.obter_notificacoes()
            ],
        }

        if isinstance(usuario, Leitor):
            dados['progresso_leitura'] = dict(usuario.progresso_leitura)
            dados['sessoes_leitura'] = dict(usuario.sessoes_leitura)
            dados['biblioteca'] = {
                categoria.value: [historia.id for historia in usuario.biblioteca.obter_historias_por_categoria(categoria)]
                for categoria in CategoriaBiblioteca
            }
        elif isinstance(usuario, Autor):
            dados['obras'] = [historia.id for historia in usuario.obter_obras()]

        usuarios_serializados[usuario_id] = dados

    historias_serializadas = {}
    for historia_id, historia in historias_db.items():
        historias_serializadas[historia_id] = {
            'id': historia.id,
            'titulo': historia.titulo,
            'sinopse': historia.sinopse,
            'genero': historia.genero,
            'capa': historia.capa,
            'status': historia.status,
            'autor_id': historia.autor.id_usuario if historia.autor else None,
            'leitor_ids': [leitor.id_usuario for leitor in historia.leitores],
            'data_criacao': _iso(historia.data_criacao),
            'data_atualizacao': _iso(historia.data_atualizacao),
            'avaliacoes': [
                {
                    'id': av.id,
                    'usuario_id': av.usuario.id_usuario if av.usuario else None,
                    'nota': av.nota,
                    'tipo': av.tipo.value,
                    'conteudo_id': av.conteudo_id,
                    'data_criacao': _iso(av.data_criacao),
                }
                for av in historia.avaliacoes
            ],
            'capitulos': [
                {
                    'id': capitulo.id,
                    'titulo': capitulo.titulo,
                    'conteudo': capitulo.conteudo,
                    'ordem': capitulo.ordem,
                    'visualizacoes': capitulo.visualizacoes,
                    'data_criacao': _iso(capitulo.data_criacao),
                    'data_atualizacao': _iso(capitulo.data_atualizacao),
                    'destaques': dict(capitulo.destaques),
                    'avaliacoes': [
                        {
                            'id': av.id,
                            'usuario_id': av.usuario.id_usuario if av.usuario else None,
                            'nota': av.nota,
                            'tipo': av.tipo.value,
                            'conteudo_id': av.conteudo_id,
                            'data_criacao': _iso(av.data_criacao),
                        }
                        for av in capitulo.avaliacoes
                    ],
                    'comentarios': [
                        {
                            'id': comentario.id,
                            'usuario_id': comentario.usuario.id_usuario if comentario.usuario else None,
                            'conteudo': comentario.obter_conteudo(),
                            'capitulo_id': comentario.capitulo_id,
                            'posicao_texto': comentario.posicao_texto,
                            'curtidas': comentario.curtidas,
                            'data_criacao': _iso(comentario.data_criacao),
                        }
                        for comentario in capitulo.comentarios
                    ],
                }
                for capitulo in historia.capitulos
            ],
        }

    return {
        'schema_version': 1,
        'gerado_em': datetime.now().isoformat(),
        'contas': dict(contas_db),
        'sessoes': dict(sessoes_db),
        'usuarios': usuarios_serializados,
        'historias': historias_serializadas,
    }


def _desserializar_state(state: dict, usuarios_db: dict, contas_db: dict, sessoes_db: dict, historias_db: dict):
    usuarios_db.clear()
    contas_db.clear()
    sessoes_db.clear()
    historias_db.clear()

    contas_recebidas = state.get('contas', {})
    if isinstance(contas_recebidas, dict):
        contas_db.update(contas_recebidas)

    sessoes_recebidas = state.get('sessoes', {})
    if isinstance(sessoes_recebidas, dict):
        for token, conta_id in sessoes_recebidas.items():
            if conta_id in contas_db:
                sessoes_db[token] = conta_id

    senha_por_usuario = {}
    for conta in contas_db.values():
        senha = conta.get('senha')
        if not senha:
            continue
        senha_por_usuario[conta.get('leitor_id')] = senha
        senha_por_usuario[conta.get('autor_id')] = senha

    usuarios_origem = state.get('usuarios', {})
    usuarios_items = usuarios_origem.items() if isinstance(usuarios_origem, dict) else []
    metadados_usuarios = {}

    for usuario_id, dados in usuarios_items:
        if not isinstance(dados, dict):
            continue
        tipo = dados.get('tipo')
        nome = dados.get('nome', 'Usuário')
        email = dados.get('email', '')
        senha = dados.get('senha') or senha_por_usuario.get(usuario_id) or '__restored__'

        if tipo == 'Leitor':
            usuario = Leitor(usuario_id, nome, email, senha)
        elif tipo == 'Autor':
            usuario = Autor(usuario_id, nome, email, senha)
        else:
            continue

        usuario.data_criacao = _parse_iso(dados.get('data_criacao'), usuario.data_criacao)
        usuarios_db[usuario_id] = usuario
        metadados_usuarios[usuario_id] = dados

    historias_origem = state.get('historias', {})
    historias_items = historias_origem.items() if isinstance(historias_origem, dict) else []

    # Primeira passada: cria histórias base
    for historia_id, dados in historias_items:
        if not isinstance(dados, dict):
            continue
        historia = Historia(
            titulo=dados.get('titulo', 'Sem título'),
            sinopse=dados.get('sinopse', ''),
            genero=dados.get('genero', ''),
            capa=dados.get('capa'),
        )
        historia.id = historia_id
        historia.status = dados.get('status', 'em_escrita')
        historia.data_criacao = _parse_iso(dados.get('data_criacao'), historia.data_criacao)
        historia.data_atualizacao = _parse_iso(dados.get('data_atualizacao'), historia.data_atualizacao)
        historias_db[historia_id] = historia

    # Segunda passada: cria vínculos complexos
    for historia_id, dados in historias_items:
        historia = historias_db.get(historia_id)
        if not historia or not isinstance(dados, dict):
            continue

        autor_id = dados.get('autor_id')
        autor = usuarios_db.get(autor_id)
        if isinstance(autor, Autor):
            historia.vincular_autor(autor)
            if historia not in autor._obras:
                autor._obras.append(historia)

        historia.leitores = [
            usuario for usuario_id in dados.get('leitor_ids', [])
            for usuario in [usuarios_db.get(usuario_id)]
            if isinstance(usuario, Leitor)
        ]

        capitulos = dados.get('capitulos', [])
        if isinstance(capitulos, list):
            for capitulo_data in sorted(capitulos, key=lambda c: c.get('ordem', 0) if isinstance(c, dict) else 0):
                if not isinstance(capitulo_data, dict):
                    continue
                capitulo = Capitulo(
                    titulo=capitulo_data.get('titulo', 'Capítulo'),
                    conteudo=capitulo_data.get('conteudo', ''),
                    ordem=capitulo_data.get('ordem', len(historia.capitulos) + 1),
                )
                capitulo.id = capitulo_data.get('id', capitulo.id)
                capitulo.visualizacoes = int(capitulo_data.get('visualizacoes', 0))
                capitulo.data_criacao = _parse_iso(capitulo_data.get('data_criacao'), capitulo.data_criacao)
                capitulo.data_atualizacao = _parse_iso(capitulo_data.get('data_atualizacao'), capitulo.data_atualizacao)
                destaques = capitulo_data.get('destaques', {})
                if isinstance(destaques, dict):
                    capitulo.destaques.update(destaques)

                for comentario_data in capitulo_data.get('comentarios', []):
                    if not isinstance(comentario_data, dict):
                        continue
                    usuario = usuarios_db.get(comentario_data.get('usuario_id'))
                    if not isinstance(usuario, Leitor):
                        continue

                    comentario = Comentario(
                        id=comentario_data.get('id', ''),
                        usuario=usuario,
                        conteudo=comentario_data.get('conteudo', ''),
                        capitulo_id=capitulo.id,
                        posicao_texto=comentario_data.get('posicao_texto'),
                    )
                    comentario.curtidas = int(comentario_data.get('curtidas', 0))
                    comentario.data_criacao = _parse_iso(comentario_data.get('data_criacao'), comentario.data_criacao)
                    capitulo.adicionar_comentario(comentario)
                    usuario._comentarios.append(comentario)

                for avaliacao_data in capitulo_data.get('avaliacoes', []):
                    if not isinstance(avaliacao_data, dict):
                        continue
                    usuario = usuarios_db.get(avaliacao_data.get('usuario_id'))
                    if not isinstance(usuario, Leitor):
                        continue
                    try:
                        avaliacao = Avaliacao(
                            id=avaliacao_data.get('id', ''),
                            usuario=usuario,
                            nota=int(avaliacao_data.get('nota', 1)),
                            tipo=_parse_tipo_avaliacao(avaliacao_data.get('tipo')),
                            conteudo_id=avaliacao_data.get('conteudo_id'),
                        )
                    except ValueError:
                        continue
                    avaliacao.data_criacao = _parse_iso(avaliacao_data.get('data_criacao'), avaliacao.data_criacao)
                    capitulo.adicionar_avaliacao(avaliacao)
                    usuario._avaliacoes.append(avaliacao)

                historia.adicionar_capitulo(capitulo)

        for avaliacao_data in dados.get('avaliacoes', []):
            if not isinstance(avaliacao_data, dict):
                continue
            usuario = usuarios_db.get(avaliacao_data.get('usuario_id'))
            if not isinstance(usuario, Leitor):
                continue
            try:
                avaliacao = Avaliacao(
                    id=avaliacao_data.get('id', ''),
                    usuario=usuario,
                    nota=int(avaliacao_data.get('nota', 1)),
                    tipo=_parse_tipo_avaliacao(avaliacao_data.get('tipo')),
                    conteudo_id=avaliacao_data.get('conteudo_id'),
                )
            except ValueError:
                continue

            avaliacao.data_criacao = _parse_iso(avaliacao_data.get('data_criacao'), avaliacao.data_criacao)
            historia.adicionar_avaliacao(avaliacao)
            usuario._avaliacoes.append(avaliacao)

        historia.data_atualizacao = _parse_iso(dados.get('data_atualizacao'), historia.data_atualizacao)

    # Restaura dados específicos de leitor/autor
    for usuario_id, dados in metadados_usuarios.items():
        usuario = usuarios_db.get(usuario_id)
        if not usuario or not isinstance(dados, dict):
            continue

        if isinstance(usuario, Leitor):
            progresso = dados.get('progresso_leitura', {})
            if isinstance(progresso, dict):
                usuario.progresso_leitura = progresso

            sessoes = dados.get('sessoes_leitura', {})
            if isinstance(sessoes, dict):
                usuario.sessoes_leitura = sessoes

            biblioteca = dados.get('biblioteca', {})
            if isinstance(biblioteca, dict):
                for categoria_nome, historias_ids in biblioteca.items():
                    categoria = _parse_categoria(categoria_nome)
                    if not categoria or not isinstance(historias_ids, list):
                        continue
                    for historia_id in historias_ids:
                        historia = historias_db.get(historia_id)
                        if historia:
                            usuario.biblioteca.definir_categoria(historia, categoria)

        if isinstance(usuario, Autor):
            usuario.atualizar_metricas()

        notificacoes = dados.get('notificacoes', [])
        if isinstance(notificacoes, list):
            for notif_data in notificacoes:
                if not isinstance(notif_data, dict):
                    continue
                notificacao = Notificacao(
                    id=notif_data.get('id', ''),
                    usuario=usuario,
                    mensagem=notif_data.get('mensagem', ''),
                    tipo=_parse_tipo_notificacao(notif_data.get('tipo')),
                    titulo=notif_data.get('titulo', ''),
                )
                notificacao.lida = bool(notif_data.get('lida', False))
                notificacao.data_criacao = _parse_iso(notif_data.get('data_criacao'), notificacao.data_criacao)
                usuario.adicionar_notificacao(notificacao)


def carregar_estado(usuarios_db: dict, contas_db: dict, sessoes_db: dict, historias_db: dict) -> bool:
    """Carrega estado do Firestore (se configurado)."""
    client = _build_firestore_client()
    if client is None:
        return False

    try:
        snapshot = client.collection(_collection_name()).document(_document_name()).get()
        if not snapshot.exists:
            return False

        payload = snapshot.to_dict() or {}
        state = payload.get('state') if isinstance(payload.get('state'), dict) else payload
        if not isinstance(state, dict):
            return False

        _desserializar_state(state, usuarios_db, contas_db, sessoes_db, historias_db)
        return True
    except Exception as exc:  # pragma: no cover - depende de ambiente
        _STATUS.update({
            'backend': 'memory',
            'ativo': False,
            'motivo': f'Falha ao carregar estado: {exc}',
        })
        return False


def salvar_estado(usuarios_db: dict, contas_db: dict, sessoes_db: dict, historias_db: dict) -> bool:
    """Salva estado completo no Firestore (se configurado)."""
    client = _build_firestore_client()
    if client is None:
        return False

    state = _serializar_state(usuarios_db, contas_db, sessoes_db, historias_db)

    try:
        with _LOCK:
            client.collection(_collection_name()).document(_document_name()).set(
                {
                    'state': state,
                    'updated_at': datetime.now().isoformat(),
                },
                merge=True,
            )
        return True
    except Exception as exc:  # pragma: no cover - depende de ambiente
        _STATUS.update({
            'backend': 'memory',
            'ativo': False,
            'motivo': f'Falha ao salvar estado: {exc}',
        })
        return False
