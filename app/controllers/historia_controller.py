"""
Controllers para gerenciar histórias e experiências de leitura.
"""
import uuid
from datetime import datetime
import io
import re
import base64
from html import unescape
from ebooklib import epub
from bs4 import BeautifulSoup
from app.models.historia import Historia
from app.models.capitulo import Capitulo
from app.models.avaliacao import Avaliacao, TipoAvaliacao
from app.models.autor import Autor
from app.models.leitor import Leitor
from app.controllers.usuario_controller import usuarios_db


# Armazenamento em memória (em produção seria um banco de dados)
historias_db = {}

TEMAS_GENERO = {
    'mistério': {'accent': '#6d597a', 'surface': '#f3ecf8'},
    'romance': {'accent': '#b56576', 'surface': '#fdf1f4'},
    'fantasia': {'accent': '#577590', 'surface': '#eef5fb'},
    'ficcao cientifica': {'accent': '#355070', 'surface': '#edf2fb'},
    'ficção científica': {'accent': '#355070', 'surface': '#edf2fb'},
    'drama': {'accent': '#7f5539', 'surface': '#f8efe8'},
    'aventura': {'accent': '#588157', 'surface': '#eef6ee'},
}


class HistoriaController:
    """Controller para gerenciamento de histórias."""

    @staticmethod
    def _limpar_texto(valor: str) -> str:
        """Normaliza campos textuais recebidos pela API."""
        return valor.strip() if isinstance(valor, str) else ""

    @staticmethod
    def _validar_capa(capa: str | None) -> tuple[bool, str | None, str | None]:
        """Valida o formato da capa e retorna (ok, capa_normalizada, erro)."""
        if capa is None:
            return True, None, None

        if not isinstance(capa, str):
            return False, None, 'Formato de capa inválido'

        capa_normalizada = capa.strip()
        if not capa_normalizada:
            return True, None, None

        if len(capa_normalizada) > 2_000_000:
            return False, None, 'Capa muito grande. Use até 2MB.'

        if not (
            capa_normalizada.startswith('data:image/')
            or capa_normalizada.startswith('https://')
            or capa_normalizada.startswith('http://')
        ):
            return False, None, 'Formato de capa inválido'

        return True, capa_normalizada, None

    @staticmethod
    def _validar_preview_video(preview_video: str | None) -> tuple[bool, str | None, str | None]:
        """Valida preview opcional, aceitando somente vídeo (nunca áudio)."""
        if preview_video is None:
            return True, None, None
        if not isinstance(preview_video, str):
            return False, None, 'Formato de preview inválido'

        preview_normalizado = preview_video.strip()
        if not preview_normalizado:
            return True, None, None

        if len(preview_normalizado) > 10_000_000:
            return False, None, 'Preview muito grande. Use até 10MB.'

        if preview_normalizado.startswith('data:audio/'):
            return False, None, 'Áudio não é aceito no modo de criação de livro'

        if preview_normalizado.startswith('data:video/'):
            if not (
                preview_normalizado.startswith('data:video/mp4')
                or preview_normalizado.startswith('data:video/quicktime')
            ):
                return False, None, 'Formato de preview inválido. Use MOV ou MP4.'
            return True, preview_normalizado, None

        if preview_normalizado.startswith('http://') or preview_normalizado.startswith('https://'):
            return True, preview_normalizado, None

        return False, None, 'Formato de preview inválido. Use MOV ou MP4.'

    @staticmethod
    def _obter_tema_visual(historia: Historia) -> dict:
        """Retorna uma paleta simples para destacar a história na interface."""
        genero = historia.genero.casefold()
        return TEMAS_GENERO.get(genero, {'accent': '#264653', 'surface': '#eef4f2'})

    @staticmethod
    def _buscar_capitulo(historia: Historia, capitulo_id: str) -> Capitulo | None:
        """Busca um capítulo por ID dentro da história."""
        for capitulo in historia.capitulos:
            if capitulo.id == capitulo_id:
                return capitulo
        return None

    @staticmethod
    def serializar_comentario(comentario) -> dict:
        """Converte um comentário para JSON."""
        return {
            'id': comentario.id,
            'usuario': comentario.usuario.nome,
            'usuario_id': comentario.usuario.id_usuario,
            'conteudo': comentario.obter_conteudo(),
            'curtidas': comentario.curtidas,
            'data_criacao': comentario.data_criacao.isoformat(),
        }

    @staticmethod
    def serializar_capitulo(capitulo: Capitulo, incluir_conteudo: bool = False) -> dict:
        """Converte um capítulo para JSON."""
        return {
            'id': capitulo.id,
            'titulo': capitulo.titulo,
            'ordem': capitulo.ordem,
            'total_palavras': capitulo.obter_total_palavras(),
            'visualizacoes': capitulo.visualizacoes,
            'comentarios': len(capitulo.comentarios),
            'media_avaliacoes': round(capitulo.obter_media_avaliacoes(), 1),
            'tempo_estimado_minutos': capitulo.obter_tempo_estimado_leitura(),
            'resumo': f"{capitulo.conteudo[:180]}..." if len(capitulo.conteudo) > 180 else capitulo.conteudo,
            'conteudo': capitulo.conteudo if incluir_conteudo else None,
            'data_atualizacao': capitulo.data_atualizacao.isoformat(),
        }

    @staticmethod
    def serializar_destaques(capitulo: Capitulo, historia: Historia, usuario_id: str | None = None) -> dict:
        """Resume destaques do capítulo para o leitor."""
        total_leitores = max(1, len(historia.leitores))
        meus_trechos = []
        todos = []
        for destaque in capitulo.destaques.values():
            usuarios = destaque.get('usuarios', [])
            item = {
                'trecho': destaque.get('trecho', ''),
                'total': len(usuarios),
                'percentual': round((len(usuarios) / total_leitores) * 100),
            }
            todos.append(item)
            if usuario_id and usuario_id in usuarios:
                meus_trechos.append(item['trecho'])

        return {
            'meus': meus_trechos,
            'recomendados': capitulo.obter_destaques_recomendados(total_leitores),
            'todos': sorted(todos, key=lambda item: item['total'], reverse=True),
            'leitores_base': total_leitores,
        }

    @staticmethod
    def serializar_historia(
        historia: Historia,
        incluir_capitulos: bool = False,
        leitor_id: str | None = None,
        incluir_conteudo_capitulos: bool = False,
    ) -> dict:
        """Converte uma história para JSON com dados voltados para leitura."""
        ultimo_capitulo = historia.obter_ultimo_capitulo()
        leitor = usuarios_db.get(leitor_id) if leitor_id else None
        progresso = leitor.obter_progresso(historia.id) if isinstance(leitor, Leitor) else None

        # If a leitor_id was provided, expose whether this user already avaliou a nota for this historia
        minha_avaliacao = None
        if leitor_id and hasattr(historia, 'avaliacoes'):
            try:
                for av in historia.avaliacoes:
                    if getattr(av.usuario, 'id_usuario', None) == leitor_id:
                        minha_avaliacao = av.nota
                        break
            except Exception:
                minha_avaliacao = None

        return {
            'id': historia.id,
            'titulo': historia.titulo,
            'sinopse': historia.sinopse,
            'genero': historia.genero,
            'capa': historia.capa,
            'status': historia.status,
            'autor': historia.autor.nome if historia.autor else None,
            'autor_id': historia.autor.id_usuario if historia.autor else None,
            'capitulos': [
                HistoriaController.serializar_capitulo(capitulo, incluir_conteudo=incluir_conteudo_capitulos)
                for capitulo in historia.capitulos
            ] if incluir_capitulos else None,
            'capitulo_inicial_id': historia.capitulos[0].id if historia.capitulos else None,
            'total_capitulos': historia.obter_quantidade_capitulos(),
            'leitores': len(historia.leitores),
            'media_avaliacoes': round(historia.obter_media_avaliacoes(), 1),
            'total_avaliacoes': len(historia.avaliacoes),
            'total_comentarios': historia.obter_total_comentarios(),
            'popularidade': round(historia.obter_popularidade(), 1),
            'tempo_estimado_minutos': historia.obter_tempo_estimado_leitura(),
            'ultimo_capitulo': {
                'id': ultimo_capitulo.id,
                'titulo': ultimo_capitulo.titulo,
                'ordem': ultimo_capitulo.ordem,
            } if ultimo_capitulo else None,
            'tem_epub': bool(getattr(historia, 'arquivo_epub', None)),
            'preview': getattr(historia, 'preview_video', None),
            'minha_avaliacao': minha_avaliacao,
            'tema': HistoriaController._obter_tema_visual(historia),
            'progresso_leitor': progresso,
            'data_criacao': historia.data_criacao.isoformat(),
            'data_atualizacao': historia.data_atualizacao.isoformat(),
        }

    @staticmethod
    def criar_historia(titulo: str, sinopse: str, genero: str, usuario_id: str, capa: str | None = None) -> dict:
        """Cria uma nova história."""
        try:
            titulo = HistoriaController._limpar_texto(titulo)
            sinopse = HistoriaController._limpar_texto(sinopse)
            genero = HistoriaController._limpar_texto(genero)
            usuario_id = HistoriaController._limpar_texto(usuario_id)
            capa_ok, capa_normalizada, capa_erro = HistoriaController._validar_capa(capa)

            if not titulo:
                return {'sucesso': False, 'erro': 'Título é obrigatório', 'codigo': 400}
            if not sinopse:
                return {'sucesso': False, 'erro': 'Sinopse é obrigatória', 'codigo': 400}
            if not usuario_id:
                return {'sucesso': False, 'erro': 'Autor é obrigatório', 'codigo': 400}
            if not capa_ok:
                return {'sucesso': False, 'erro': capa_erro or 'Capa inválida', 'codigo': 400}

            autor = usuarios_db.get(usuario_id)
            if not autor:
                return {'sucesso': False, 'erro': 'Autor não encontrado', 'codigo': 404}
            if not isinstance(autor, Autor):
                return {
                    'sucesso': False,
                    'erro': 'Apenas usuários do tipo autor podem publicar histórias',
                    'codigo': 400,
                }

            historia = Historia(titulo, sinopse, genero, capa=capa_normalizada)
            autor.publicar_historia(historia)
            historias_db[historia.id] = historia
            return {
                'sucesso': True,
                'id': historia.id,
                'autor_id': autor.id_usuario,
                'tem_epub': False,
                'mensagem': f'História "{titulo}" criada com sucesso!'
            }
        except Exception as e:
            return {'sucesso': False, 'erro': str(e), 'codigo': 500}

    @staticmethod
    def _extrair_dados_epub(epub_data: str) -> dict:
        """Extrai metadados e capítulos de um EPUB em data URL/base64."""
        epub_texto = HistoriaController._limpar_texto(epub_data)
        if not epub_texto:
            return {'sucesso': False, 'erro': 'Arquivo EPUB é obrigatório', 'codigo': 400}
        if len(epub_texto) > 20_000_000:
            return {'sucesso': False, 'erro': 'EPUB muito grande. Limite de 20MB.', 'codigo': 400}

        try:
            if ',' in epub_texto:
                _, b64 = epub_texto.split(',', 1)
            else:
                b64 = epub_texto
            raw = base64.b64decode(b64)
            book = epub.read_epub(io.BytesIO(raw))
        except Exception as exc:
            return {'sucesso': False, 'erro': f'Erro ao processar EPUB: {exc}', 'codigo': 400}

        def primeiro_metadado(chave: str) -> str:
            try:
                itens = book.get_metadata('DC', chave) or []
                if itens and itens[0]:
                    return HistoriaController._limpar_texto(unescape(str(itens[0][0])))
            except Exception:
                return ''
            return ''

        metadados = {
            'titulo': primeiro_metadado('title'),
            'sinopse': primeiro_metadado('description'),
            'genero': primeiro_metadado('subject'),
            'capa': None,
        }

        # Busca de capa: item nomeado como cover/capa e fallback para primeira imagem.
        cover_item = None
        for item in book.get_items():
            media_type = str(getattr(item, 'media_type', '') or '')
            nome_item = getattr(item, 'id', '') or getattr(item, 'file_name', '') or ''
            if not nome_item:
                obter_nome = getattr(item, 'get_name', None)
                if callable(obter_nome):
                    nome_item = obter_nome()
            nome = str(nome_item).lower()
            if media_type.startswith('image/') and any(token in nome for token in ('cover', 'capa')):
                cover_item = item
                break
        if not cover_item:
            for item in book.get_items():
                media_type = str(getattr(item, 'media_type', '') or '')
                if media_type.startswith('image/'):
                    cover_item = item
                    break
        if cover_item is not None:
            try:
                bytes_img = cover_item.get_content()
                tipo_img = getattr(cover_item, 'media_type', 'image/jpeg')
                metadados['capa'] = f"data:{tipo_img};base64,{base64.b64encode(bytes_img).decode('ascii')}"
            except Exception:
                metadados['capa'] = None

        capitulos = []
        ordem = 1
        spine_ids = [item[0] if isinstance(item, (list, tuple)) else item for item in getattr(book, 'spine', [])]
        if not spine_ids:
            spine_items = [item for item in book.get_items() if item.get_type() == epub.EpubHtml]
        else:
            spine_items = []
            for idref in spine_ids:
                try:
                    item = book.get_item_with_id(idref)
                except Exception:
                    item = None
                if item is not None:
                    spine_items.append(item)

        for item in spine_items:
            try:
                conteudo = item.get_content().decode('utf-8', errors='ignore')
            except Exception:
                continue

            soup = BeautifulSoup(conteudo, 'html.parser')

            heading = soup.find(['h1', 'h2', 'h3'])
            if heading and heading.get_text(strip=True):
                titulo_capitulo = HistoriaController._limpar_texto(unescape(heading.get_text(strip=True)))
            else:
                titulo_html = HistoriaController._limpar_texto(unescape(str(soup.title.string))) if soup.title and soup.title.string else ''
                titulo_capitulo = titulo_html or f'Capítulo {ordem}'

            texto_limpo = unescape(soup.get_text(separator=' '))
            texto_limpo = re.sub(r'\s+', ' ', texto_limpo).strip()
            if not texto_limpo:
                continue

            capitulos.append({
                'titulo': titulo_capitulo,
                'conteudo': texto_limpo,
            })
            ordem += 1

        return {
            'sucesso': True,
            'metadados': metadados,
            'capitulos': capitulos,
        }

    @staticmethod
    def consultar_metadados_epub(epub_data: str) -> dict:
        """Retorna metadados e nomes de capítulos para pré-preenchimento."""
        extraido = HistoriaController._extrair_dados_epub(epub_data)
        if not extraido.get('sucesso'):
            return extraido

        capitulos = extraido.get('capitulos', [])
        metadados = dict(extraido.get('metadados', {}))
        metadados['total_capitulos'] = len(capitulos)
        metadados['capitulos'] = [capitulo.get('titulo', '') for capitulo in capitulos[:60]]
        return {
            'sucesso': True,
            'mensagem': 'Metadados do EPUB analisados com sucesso.',
            'metadados': metadados,
        }

    @staticmethod
    def criar_historia_com_epub(titulo: str, sinopse: str, genero: str, usuario_id: str, capa: str | None = None, epub_data: str | None = None, preview_video: str | None = None) -> dict:
        """Cria história via EPUB preenchendo dados ausentes com metadados."""
        try:
            titulo = HistoriaController._limpar_texto(titulo)
            sinopse = HistoriaController._limpar_texto(sinopse)
            genero = HistoriaController._limpar_texto(genero)
            usuario_id = HistoriaController._limpar_texto(usuario_id)

            autor = usuarios_db.get(usuario_id)
            if not autor:
                return {'sucesso': False, 'erro': 'Autor não encontrado', 'codigo': 404}
            if not isinstance(autor, Autor):
                return {
                    'sucesso': False,
                    'erro': 'Apenas usuários do tipo autor podem publicar histórias',
                    'codigo': 400,
                }

            extraido = HistoriaController._extrair_dados_epub(epub_data or '')
            if not extraido.get('sucesso'):
                return extraido

            metadados = extraido.get('metadados', {})
            capitulos_extraidos = extraido.get('capitulos', [])

            titulo_final = titulo or HistoriaController._limpar_texto(metadados.get('titulo'))
            sinopse_final = sinopse or HistoriaController._limpar_texto(metadados.get('sinopse'))
            genero_final = genero or HistoriaController._limpar_texto(metadados.get('genero'))
            capa_final = capa if HistoriaController._limpar_texto(capa or '') else metadados.get('capa')

            capa_ok, capa_normalizada, capa_erro = HistoriaController._validar_capa(capa_final)
            preview_ok, preview_normalizado, preview_erro = HistoriaController._validar_preview_video(preview_video)
            if not titulo_final:
                return {'sucesso': False, 'erro': 'Título é obrigatório', 'codigo': 400}
            if not sinopse_final:
                return {'sucesso': False, 'erro': 'Sinopse é obrigatória', 'codigo': 400}
            if not capa_ok:
                return {'sucesso': False, 'erro': capa_erro or 'Capa inválida', 'codigo': 400}
            if not preview_ok:
                return {'sucesso': False, 'erro': preview_erro or 'Preview inválido', 'codigo': 400}

            historia = Historia(titulo_final, sinopse_final, genero_final, capa=capa_normalizada)
            if preview_normalizado:
                historia.preview_video = preview_normalizado

            for indice, capitulo_data in enumerate(capitulos_extraidos, start=1):
                capitulo = Capitulo(
                    capitulo_data.get('titulo') or f'Capítulo {indice}',
                    capitulo_data.get('conteudo') or '',
                    indice,
                )
                historia.adicionar_capitulo(capitulo)

            historia.arquivo_epub = 'embedded'
            historia.status = 'completa' if historia.obter_quantidade_capitulos() > 0 else historia.status

            autor.publicar_historia(historia)
            historias_db[historia.id] = historia
            return {
                'sucesso': True,
                'id': historia.id,
                'autor_id': autor.id_usuario,
                'tem_epub': True,
                'total_capitulos': historia.obter_quantidade_capitulos(),
                'mensagem': f'História "{titulo_final}" criada com sucesso!',
            }
        except Exception as e:
            return {'sucesso': False, 'erro': str(e), 'codigo': 500}

    @staticmethod
    def editar_historia(historia_id: str, titulo: str, sinopse: str, genero: str, capa: str | None = None) -> dict:
        """Atualiza dados principais de uma história."""
        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}

        try:
            titulo = HistoriaController._limpar_texto(titulo)
            sinopse = HistoriaController._limpar_texto(sinopse)
            genero = HistoriaController._limpar_texto(genero)

            if not titulo:
                return {'sucesso': False, 'erro': 'Título é obrigatório', 'codigo': 400}
            if not sinopse:
                return {'sucesso': False, 'erro': 'Sinopse é obrigatória', 'codigo': 400}
            if not genero:
                return {'sucesso': False, 'erro': 'Gênero é obrigatório', 'codigo': 400}

            if capa is not None:
                capa_ok, capa_normalizada, capa_erro = HistoriaController._validar_capa(capa)
                if not capa_ok:
                    return {'sucesso': False, 'erro': capa_erro or 'Capa inválida', 'codigo': 400}
                historia.capa = capa_normalizada

            historia.titulo = titulo
            historia.sinopse = sinopse
            historia.genero = genero
            historia.data_atualizacao = datetime.now()
            return {
                'sucesso': True,
                'historia': HistoriaController.serializar_historia(
                    historia,
                    incluir_capitulos=True,
                    incluir_conteudo_capitulos=True,
                ),
                'mensagem': f'Livro "{titulo}" atualizado com sucesso!'
            }
        except Exception as e:
            return {'sucesso': False, 'erro': str(e), 'codigo': 500}

    @staticmethod
    def listar_historias(busca: str = '', genero: str = '', ordem: str = 'destaques', leitor_id: str | None = None) -> dict:
        """Lista histórias com filtros de descoberta."""
        busca = HistoriaController._limpar_texto(busca).casefold()
        genero = HistoriaController._limpar_texto(genero).casefold()
        ordem = HistoriaController._limpar_texto(ordem).casefold() or 'destaques'

        historias = list(historias_db.values())

        if busca:
            historias = [
                historia for historia in historias
                if busca in historia.titulo.casefold()
                or busca in historia.sinopse.casefold()
                or busca in historia.genero.casefold()
                or (historia.autor and busca in historia.autor.nome.casefold())
            ]

        if genero:
            historias = [
                historia for historia in historias
                if historia.genero.casefold() == genero
            ]

        if ordem == 'recentes':
            historias.sort(key=lambda historia: historia.data_atualizacao, reverse=True)
        elif ordem == 'bem_avaliadas':
            historias.sort(
                key=lambda historia: (
                    historia.obter_media_avaliacoes(),
                    len(historia.avaliacoes),
                    historia.obter_popularidade(),
                ),
                reverse=True,
            )
        elif ordem == 'maratona':
            historias.sort(key=lambda historia: historia.obter_tempo_estimado_leitura(), reverse=True)
        else:
            historias.sort(key=lambda historia: historia.obter_popularidade(), reverse=True)

        historias_lista = [
            HistoriaController.serializar_historia(historia, incluir_capitulos=False, leitor_id=leitor_id)
            for historia in historias
        ]

        generos = sorted({historia.genero for historia in historias_db.values() if historia.genero})

        return {
            'sucesso': True,
            'total': len(historias_lista),
            'historias': historias_lista,
            'filtros': {
                'busca': busca,
                'genero': genero,
                'ordem': ordem,
                'generos_disponiveis': generos,
            },
        }

    @staticmethod
    def listar_historias_por_autor(
        autor_id: str,
        leitor_id: str | None = None,
        incluir_capitulos: bool = True,
        incluir_conteudo_capitulos: bool = False,
    ) -> dict:
        """Lista as histórias publicadas por um autor específico."""
        autor_id = HistoriaController._limpar_texto(autor_id)
        autor = usuarios_db.get(autor_id)
        if not autor:
            return {'sucesso': False, 'erro': 'Autor não encontrado', 'codigo': 404}
        if not isinstance(autor, Autor):
            return {'sucesso': False, 'erro': 'Usuário informado não é autor', 'codigo': 400}

        historias = [
            historia for historia in historias_db.values()
            if historia.autor and historia.autor.id_usuario == autor_id
        ]
        historias.sort(key=lambda historia: historia.data_atualizacao, reverse=True)

        return {
            'sucesso': True,
            'total': len(historias),
            'historias': [
                HistoriaController.serializar_historia(
                    historia,
                    incluir_capitulos=incluir_capitulos,
                    leitor_id=leitor_id,
                    incluir_conteudo_capitulos=incluir_conteudo_capitulos,
                )
                for historia in historias
            ],
        }

    @staticmethod
    def obter_historia(historia_id: str, leitor_id: str | None = None) -> dict:
        """Obtém detalhes completos de uma história."""
        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}

        return {
            'sucesso': True,
            'historia': HistoriaController.serializar_historia(
                historia,
                incluir_capitulos=True,
                leitor_id=leitor_id,
            )
        }

    @staticmethod
    def adicionar_capitulo(historia_id: str, titulo: str, conteudo: str) -> dict:
        """Adiciona um novo capítulo a uma história."""
        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}
        if getattr(historia, 'arquivo_epub', None):
            return {
                'sucesso': False,
                'erro': 'Livro importado por EPUB permite apenas edição dos capítulos existentes.',
                'codigo': 400,
            }

        try:
            titulo = HistoriaController._limpar_texto(titulo)
            conteudo = HistoriaController._limpar_texto(conteudo)

            if not titulo:
                return {'sucesso': False, 'erro': 'Título do capítulo é obrigatório', 'codigo': 400}
            if not conteudo:
                return {'sucesso': False, 'erro': 'Conteúdo do capítulo é obrigatório', 'codigo': 400}

            ordem = historia.obter_quantidade_capitulos() + 1
            capitulo = Capitulo(titulo, conteudo, ordem)
            historia.adicionar_capitulo(capitulo)
            return {
                'sucesso': True,
                'id': capitulo.id,
                'mensagem': f'Capítulo "{titulo}" adicionado com sucesso!'
            }
        except Exception as e:
            return {'sucesso': False, 'erro': str(e), 'codigo': 500}

    @staticmethod
    def editar_capitulo(historia_id: str, capitulo_id: str, titulo: str, conteudo: str) -> dict:
        """Atualiza um capítulo existente."""
        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}

        capitulo = HistoriaController._buscar_capitulo(historia, capitulo_id)
        if not capitulo:
            return {'sucesso': False, 'erro': 'Capítulo não encontrado', 'codigo': 404}

        try:
            titulo = HistoriaController._limpar_texto(titulo)
            conteudo = HistoriaController._limpar_texto(conteudo)

            if not titulo:
                return {'sucesso': False, 'erro': 'Título do capítulo é obrigatório', 'codigo': 400}
            if not conteudo:
                return {'sucesso': False, 'erro': 'Conteúdo do capítulo é obrigatório', 'codigo': 400}

            capitulo.titulo = titulo
            capitulo.conteudo = conteudo
            historia.data_atualizacao = capitulo.data_atualizacao
            return {
                'sucesso': True,
                'capitulo': HistoriaController.serializar_capitulo(capitulo, incluir_conteudo=True),
                'mensagem': f'Capítulo "{titulo}" atualizado com sucesso!'
            }
        except Exception as e:
            return {'sucesso': False, 'erro': str(e), 'codigo': 500}

    @staticmethod
    def excluir_capitulo(historia_id: str, capitulo_id: str) -> dict:
        """Exclui um capítulo e reordena os demais."""
        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}

        capitulo = HistoriaController._buscar_capitulo(historia, capitulo_id)
        if not capitulo:
            return {'sucesso': False, 'erro': 'Capítulo não encontrado', 'codigo': 404}

        try:
            historia.capitulos.remove(capitulo)
            for indice, item in enumerate(historia.capitulos, start=1):
                item.ordem = indice
            if not historia.capitulos and historia.status == 'completa':
                historia.status = 'em_escrita'
            historia.data_atualizacao = datetime.now()
            return {
                'sucesso': True,
                'capitulo_id': capitulo_id,
                'mensagem': f'Capítulo "{capitulo.titulo}" excluído com sucesso!',
            }
        except Exception as e:
            return {'sucesso': False, 'erro': str(e), 'codigo': 500}

    @staticmethod
    def avaliar_historia(historia_id: str, usuario_id: str, nota: int) -> dict:
        """Avalia uma história."""
        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}

        try:
            usuario_id = HistoriaController._limpar_texto(usuario_id)
            if not usuario_id:
                return {'sucesso': False, 'erro': 'Usuário é obrigatório', 'codigo': 400}

            usuario = usuarios_db.get(usuario_id)
            if not usuario:
                return {'sucesso': False, 'erro': 'Usuário não encontrado', 'codigo': 404}

            try:
                nota = int(nota)
            except (TypeError, ValueError):
                return {'sucesso': False, 'erro': 'Nota deve ser um número inteiro', 'codigo': 400}

            # If user already avaliou, update their nota instead of rejecting
            existente = None
            try:
                for av in historia.avaliacoes:
                    if av.usuario and getattr(av.usuario, 'id_usuario', None) == usuario_id:
                        existente = av
                        break
            except Exception:
                existente = None

            if existente:
                existente.nota = nota
                existente.data_criacao = datetime.now()
                mensagem = 'Avaliação atualizada com sucesso!'
            else:
                avaliacao = Avaliacao(
                    id=str(uuid.uuid4()),
                    usuario=usuario,
                    nota=nota,
                    tipo=TipoAvaliacao.HISTORIA
                )
                historia.adicionar_avaliacao(avaliacao)
                mensagem = 'Avaliação registrada com sucesso!'
            return {
                'sucesso': True,
                'media_atual': round(historia.obter_media_avaliacoes(), 1),
                'total_avaliacoes': len(historia.avaliacoes),
                'mensagem': mensagem,
            }
        except ValueError as e:
            return {'sucesso': False, 'erro': str(e), 'codigo': 400}
        except Exception as e:
            return {'sucesso': False, 'erro': str(e), 'codigo': 500}

    @staticmethod
    def obter_capitulos(historia_id: str) -> dict:
        """Lista todos os capítulos de uma história."""
        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}

        capitulos_lista = [
            HistoriaController.serializar_capitulo(capitulo, incluir_conteudo=False)
            for capitulo in historia.capitulos
        ]

        return {
            'sucesso': True,
            'total': len(capitulos_lista),
            'capitulos': capitulos_lista
        }

    @staticmethod
    def obter_capitulo(historia_id: str, capitulo_id: str, usuario_id: str | None = None) -> dict:
        """Obtém os detalhes completos de um capítulo para leitura."""
        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}

        capitulo = HistoriaController._buscar_capitulo(historia, capitulo_id)
        if not capitulo:
            return {'sucesso': False, 'erro': 'Capítulo não encontrado', 'codigo': 404}

        capitulo.registrar_visualizacao()

        usuario = usuarios_db.get(usuario_id) if usuario_id else None
        if usuario:
            historia.adicionar_leitor(usuario)
        tempo_leitura = usuario.obter_tempo_leitura(historia.id) if isinstance(usuario, Leitor) else {'total_segundos': 0, 'capitulos': {}, 'sessoes': {}}

        indice_atual = historia.capitulos.index(capitulo)
        anterior = historia.capitulos[indice_atual - 1] if indice_atual > 0 else None
        proximo = historia.capitulos[indice_atual + 1] if indice_atual < len(historia.capitulos) - 1 else None

        return {
            'sucesso': True,
            'historia': {
                'id': historia.id,
                'titulo': historia.titulo,
                'autor': historia.autor.nome if historia.autor else None,
                'capitulos': [
                    {
                        'id': item.id,
                        'ordem': item.ordem,
                        'titulo': item.titulo,
                        'total_palavras': item.obter_total_palavras(),
                    }
                    for item in historia.capitulos
                ],
            },
            'capitulo': {
                **HistoriaController.serializar_capitulo(capitulo, incluir_conteudo=True),
                'comentarios_recentes': [
                    HistoriaController.serializar_comentario(comentario)
                    for comentario in capitulo.comentarios[-5:]
                ],
                'destaques': HistoriaController.serializar_destaques(capitulo, historia, usuario_id),
            },
            'navegacao': {
                'anterior_id': anterior.id if anterior else None,
                'proximo_id': proximo.id if proximo else None,
            },
            'tempo_leitura': tempo_leitura,
        }

    @staticmethod
    def destacar_trecho(historia_id: str, capitulo_id: str, usuario_id: str, trecho: str) -> dict:
        """Registra destaque de trecho feito pelo leitor."""
        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}

        capitulo = HistoriaController._buscar_capitulo(historia, capitulo_id)
        if not capitulo:
            return {'sucesso': False, 'erro': 'Capítulo não encontrado', 'codigo': 404}

        usuario = usuarios_db.get(usuario_id)
        if not isinstance(usuario, Leitor):
            return {'sucesso': False, 'erro': 'Leitor não encontrado', 'codigo': 404}

        trecho_normalizado = " ".join(str(trecho or "").split())
        if len(trecho_normalizado) < 8:
            return {'sucesso': False, 'erro': 'Selecione um trecho maior para destacar', 'codigo': 400}
        if len(trecho_normalizado) > 500:
            return {'sucesso': False, 'erro': 'Destaque muito longo. Selecione até 500 caracteres.', 'codigo': 400}

        capitulo.adicionar_destaque(usuario_id, trecho_normalizado)
        historia.adicionar_leitor(usuario)
        return {
            'sucesso': True,
            'mensagem': 'Trecho destacado.',
            'destaques': HistoriaController.serializar_destaques(capitulo, historia, usuario_id),
        }

    @staticmethod
    def remover_destaque(historia_id: str, capitulo_id: str, usuario_id: str, trecho: str) -> dict:
        """Remove uma marcação do próprio leitor."""
        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}

        capitulo = HistoriaController._buscar_capitulo(historia, capitulo_id)
        if not capitulo:
            return {'sucesso': False, 'erro': 'Capítulo não encontrado', 'codigo': 404}

        trecho_normalizado = " ".join(str(trecho or "").split())
        if not trecho_normalizado:
            return {'sucesso': False, 'erro': 'Trecho é obrigatório', 'codigo': 400}

        if not capitulo.remover_destaque(usuario_id, trecho_normalizado):
            return {'sucesso': False, 'erro': 'Marcação não encontrada', 'codigo': 404}

        return {
            'sucesso': True,
            'mensagem': 'Marcação removida.',
            'destaques': HistoriaController.serializar_destaques(capitulo, historia, usuario_id),
        }

    @staticmethod
    def comentar_capitulo(historia_id: str, capitulo_id: str, usuario_id: str, conteudo: str) -> dict:
        """Adiciona um comentário a um capítulo."""
        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}

        capitulo = HistoriaController._buscar_capitulo(historia, capitulo_id)
        if not capitulo:
            return {'sucesso': False, 'erro': 'Capítulo não encontrado', 'codigo': 404}

        usuario_id = HistoriaController._limpar_texto(usuario_id)
        conteudo = HistoriaController._limpar_texto(conteudo)
        if not usuario_id:
            return {'sucesso': False, 'erro': 'Leitor é obrigatório', 'codigo': 400}
        if not conteudo:
            return {'sucesso': False, 'erro': 'Comentário não pode estar vazio', 'codigo': 400}

        usuario = usuarios_db.get(usuario_id)
        if not isinstance(usuario, Leitor):
            return {'sucesso': False, 'erro': 'Apenas leitores podem comentar', 'codigo': 400}

        comentario = usuario.comentar(capitulo, conteudo)
        historia.adicionar_leitor(usuario)

        return {
            'sucesso': True,
            'comentario': HistoriaController.serializar_comentario(comentario),
            'mensagem': 'Comentário publicado com sucesso!'
        }

    @staticmethod
    def editar_comentario(
        historia_id: str,
        capitulo_id: str,
        comentario_id: str,
        usuario_id: str,
        conteudo: str,
    ) -> dict:
        """Edita um comentário existente de autoria do próprio usuário."""
        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}

        capitulo = HistoriaController._buscar_capitulo(historia, capitulo_id)
        if not capitulo:
            return {'sucesso': False, 'erro': 'Capítulo não encontrado', 'codigo': 404}

        comentario_id = HistoriaController._limpar_texto(comentario_id)
        usuario_id = HistoriaController._limpar_texto(usuario_id)
        conteudo = HistoriaController._limpar_texto(conteudo)

        if not comentario_id:
            return {'sucesso': False, 'erro': 'Comentário é obrigatório', 'codigo': 400}
        if not usuario_id:
            return {'sucesso': False, 'erro': 'Leitor é obrigatório', 'codigo': 400}
        if not conteudo:
            return {'sucesso': False, 'erro': 'Comentário não pode estar vazio', 'codigo': 400}

        usuario = usuarios_db.get(usuario_id)
        if not isinstance(usuario, Leitor):
            return {'sucesso': False, 'erro': 'Apenas leitores podem editar comentários', 'codigo': 400}

        comentario = next((c for c in capitulo.comentarios if c.id == comentario_id), None)
        if not comentario:
            return {'sucesso': False, 'erro': 'Comentário não encontrado', 'codigo': 404}
        if not comentario.usuario or comentario.usuario.id_usuario != usuario_id:
            return {'sucesso': False, 'erro': 'Você só pode editar seus próprios comentários', 'codigo': 403}

        comentario.editar_conteudo(conteudo, usuario)
        return {
            'sucesso': True,
            'comentario': HistoriaController.serializar_comentario(comentario),
            'mensagem': 'Comentário editado com sucesso!',
        }

    @staticmethod
    def excluir_comentario(
        historia_id: str,
        capitulo_id: str,
        comentario_id: str,
        usuario_id: str,
    ) -> dict:
        """Exclui um comentário existente de autoria do próprio usuário."""
        historia = historias_db.get(historia_id)
        if not historia:
            return {'sucesso': False, 'erro': 'História não encontrada', 'codigo': 404}

        capitulo = HistoriaController._buscar_capitulo(historia, capitulo_id)
        if not capitulo:
            return {'sucesso': False, 'erro': 'Capítulo não encontrado', 'codigo': 404}

        comentario_id = HistoriaController._limpar_texto(comentario_id)
        usuario_id = HistoriaController._limpar_texto(usuario_id)

        if not comentario_id:
            return {'sucesso': False, 'erro': 'Comentário é obrigatório', 'codigo': 400}
        if not usuario_id:
            return {'sucesso': False, 'erro': 'Leitor é obrigatório', 'codigo': 400}

        usuario = usuarios_db.get(usuario_id)
        if not isinstance(usuario, Leitor):
            return {'sucesso': False, 'erro': 'Apenas leitores podem excluir comentários', 'codigo': 400}

        comentario = next((c for c in capitulo.comentarios if c.id == comentario_id), None)
        if not comentario:
            return {'sucesso': False, 'erro': 'Comentário não encontrado', 'codigo': 404}
        if not comentario.usuario or comentario.usuario.id_usuario != usuario_id:
            return {'sucesso': False, 'erro': 'Você só pode excluir seus próprios comentários', 'codigo': 403}

        capitulo.comentarios.remove(comentario)
        if comentario in usuario._comentarios:
            usuario._comentarios.remove(comentario)

        return {
            'sucesso': True,
            'comentario_id': comentario_id,
            'mensagem': 'Comentário excluído com sucesso!',
        }
