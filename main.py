"""
Aplicação Flask para StoryFlow com telas separadas e middleware de autenticação.
"""
import os
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, g

from app.controllers.historia_controller import HistoriaController, historias_db
from app.controllers.usuario_controller import UsuarioController, usuarios_db, contas_db, sessoes_db
from app.utils.persistence import carregar_estado, salvar_estado, obter_status_persistencia

app = Flask(__name__, template_folder='app/views', static_folder='static')
app.config['JSON_SORT_KEYS'] = False

DEMO_DADOS_INICIALIZADOS = False
DEMO_AUTO_SEED = os.getenv('STORYFLOW_DEMO_SEED', 'true').strip().lower() in {'1', 'true', 'yes', 'on'}
PAGINAS_APP = {'inicio', 'historias', 'biblioteca', 'escrever', 'voce'}


def persistir_estado():
    """Persiste o estado atual no Firestore (quando configurado)."""
    salvar_estado(usuarios_db, contas_db, sessoes_db, historias_db)


ESTADO_RESTAURADO = carregar_estado(usuarios_db, contas_db, sessoes_db, historias_db)
if ESTADO_RESTAURADO and (contas_db or historias_db):
    DEMO_DADOS_INICIALIZADOS = True


def obter_json_requisicao() -> dict:
    """Retorna o corpo JSON da requisição sem gerar erro para payload ausente."""
    dados = request.get_json(silent=True)
    return dados if isinstance(dados, dict) else {}

def resposta_api(resultado: dict, codigo_sucesso: int = 200):
    """Converte o retorno dos controllers em uma resposta HTTP consistente."""
    corpo = dict(resultado)
    codigo = corpo.pop('codigo', codigo_sucesso)
    return jsonify(corpo), codigo


def buscar_historia_por_titulo_e_autor(titulo: str, autor_id: str):
    """Localiza uma história pelo título e autor."""
    titulo_normalizado = titulo.strip().casefold()
    for historia in historias_db.values():
        if historia.titulo.casefold() == titulo_normalizado and historia.autor and historia.autor.id_usuario == autor_id:
            return historia
    return None


def garantir_conta(nome: str, email: str, senha: str):
    """Cria ou reutiliza uma conta híbrida."""
    conta = UsuarioController.obter_conta_por_email(email)
    if conta:
        return conta

    resposta = UsuarioController.registrar_conta(nome, email, senha)
    if not resposta.get('sucesso'):
        return None
    return resposta.get('conta')


def garantir_historia(titulo: str, sinopse: str, genero: str, autor_id: str):
    """Cria ou reutiliza uma história de demonstração."""
    historia = buscar_historia_por_titulo_e_autor(titulo, autor_id)
    if historia:
        return historia

    resposta = HistoriaController.criar_historia(titulo, sinopse, genero, autor_id)
    return historias_db.get(resposta.get('id'))


def garantir_capitulo(historia, titulo: str, conteudo: str):
    """Cria um capítulo apenas se ele ainda não existir."""
    if historia is None:
        return None
    for capitulo in historia.capitulos:
        if capitulo.titulo == titulo:
            return capitulo

    resposta = HistoriaController.adicionar_capitulo(historia.id, titulo, conteudo)
    return HistoriaController._buscar_capitulo(historia, resposta.get('id'))


def garantir_avaliacao(historia, usuario_id: str, nota: int):
    """Registra avaliação se o usuário ainda não avaliou a história."""
    if any(av.usuario and av.usuario.id_usuario == usuario_id for av in historia.avaliacoes):
        return
    HistoriaController.avaliar_historia(historia.id, usuario_id, nota)


def garantir_comentario(historia, capitulo, usuario_id: str, conteudo: str):
    """Registra comentário de demonstração sem duplicar."""
    for comentario in capitulo.comentarios:
        if comentario.usuario.id_usuario == usuario_id and comentario.obter_conteudo() == conteudo:
            return
    HistoriaController.comentar_capitulo(historia.id, capitulo.id, usuario_id, conteudo)


def garantir_historia_varias_paginas(autor_id: str):
    """Garante uma obra demo longa para testar páginas, capítulos e marcações."""
    biblioteca_estelar = garantir_historia(
        'A Biblioteca das Constelações',
        'Uma bibliotecária descobre que cada livro aberto move uma estrela e muda o destino de uma cidade inteira.',
        'Fantasia',
        autor_id,
    )

    trechos_longos = [
        'Clara atravessou o corredor central da biblioteca com a sensação de que as estantes respiravam devagar.',
        'Cada lombada guardava uma pequena luz, e cada luz parecia responder ao som dos passos no assoalho antigo.',
        'Quando abriu o primeiro volume, uma constelação inteira brilhou no teto e desenhou uma rota sobre sua mão.',
        'O mapa não apontava para um lugar, mas para uma escolha que ela vinha adiando desde a infância.',
        'Do lado de fora, os relógios da cidade pararam por um segundo, como se alguém tivesse virado uma página enorme.',
        'Clara percebeu que ler ali não era observar uma história; era negociar com ela, palavra por palavra.',
        'Quanto mais avançava, mais a cidade mudava: uma praça surgia, uma ponte desaparecia, uma janela aprendia outro céu.',
        'Ainda assim, havia ternura naquele perigo, porque os livros pareciam pedir cuidado antes de obediência.',
    ]
    garantir_capitulo(
        biblioteca_estelar,
        'Capítulo 1: O catálogo vivo',
        ' '.join(trechos_longos * 18),
    )
    garantir_capitulo(
        biblioteca_estelar,
        'Capítulo 2: A sala que muda de norte',
        ' '.join(list(reversed(trechos_longos)) * 16),
    )
    garantir_capitulo(
        biblioteca_estelar,
        'Capítulo 3: Margens de poeira dourada',
        ' '.join((trechos_longos[2:] + trechos_longos[:2]) * 17),
    )
    biblioteca_estelar.atualizar_status('completa')
    return biblioteca_estelar


def inicializar_dados_demo():
    """Inicializa um cenário com contas híbridas."""
    global DEMO_DADOS_INICIALIZADOS
    if not DEMO_AUTO_SEED:
        return
    if DEMO_DADOS_INICIALIZADOS:
        demo = garantir_conta('Conta Demo', 'demo@storyflow.local', 'demo123')
        if demo:
            garantir_historia_varias_paginas(demo['autor_id'])
            persistir_estado()
        return

    ana = garantir_conta('Ana Ribeiro', 'ana@example.com', 'senha123')
    bruno = garantir_conta('Bruno Lopes', 'bruno@example.com', 'senha123')
    carla = garantir_conta('Carla Melo', 'carla@example.com', 'senha123')
    demo = garantir_conta('Conta Demo', 'demo@storyflow.local', 'demo123')

    if not ana or not bruno or not carla or not demo:
        return

    torre = garantir_historia(
        'O Mistério da Torre Perdida',
        'Uma arqueóloga encontra um mapa incompleto e precisa subir uma torre que muda de lugar a cada amanhecer.',
        'Mistério',
        ana['autor_id'],
    )
    cartas = garantir_historia(
        'Cartas para o Mar',
        'Duas pessoas separadas por uma cidade portuária passam a se conhecer por cartas deixadas em garrafas.',
        'Romance',
        bruno['autor_id'],
    )
    bronze = garantir_historia(
        'Cidade de Bronze e Névoa',
        'Uma aprendiz de cartógrafa descobre bairros inteiros apagados dos mapas oficiais.',
        'Fantasia',
        carla['autor_id'],
    )
    aurora = garantir_historia(
        'Quinze Minutos Antes da Aurora',
        'Uma estação orbital recebe mensagens do futuro antes de cada desastre.',
        'Ficção Científica',
        ana['autor_id'],
    )
    biblioteca_estelar = garantir_historia_varias_paginas(demo['autor_id'])

    garantir_capitulo(
        torre,
        'Capítulo 1: O mapa dobrado',
        'Elisa encontrou o mapa dentro de uma caixa de metal enterrada sob o piso do observatório.'
    )
    torre_c2 = garantir_capitulo(
        torre,
        'Capítulo 2: O corredor sem eco',
        'A escadaria interna não devolvia nenhum som e isso tornava a subida ainda mais inquietante.'
    )
    garantir_capitulo(
        torre,
        'Capítulo 3: A sala das lanternas',
        'No topo, centenas de lanternas acesas flutuavam sem corda nem teto visível.'
    )

    garantir_capitulo(
        cartas,
        'Capítulo 1: Garrafa azul',
        'Lia encontrou a primeira carta presa entre as redes de pesca.'
    )
    garantir_capitulo(
        cartas,
        'Capítulo 2: O píer das sete marés',
        'Toda quinta-feira uma nova garrafa azul tocava o cais.'
    )

    bronze_c1 = garantir_capitulo(
        bronze,
        'Capítulo 1: Ruas riscadas',
        'Mina percebeu uma rua inteira desaparecendo da planta oficial.'
    )
    garantir_capitulo(
        bronze,
        'Capítulo 2: O mercado dos nomes antigos',
        'Os vendedores do mercado chamavam Mina por um sobrenome que ela nunca ouvira.'
    )

    garantir_capitulo(
        aurora,
        'Capítulo 1: Sinal de quinze minutos',
        'A capitã Nara ouviu o alerta antes mesmo do radar registrar movimento.'
    )

    for historia in [torre, cartas, bronze, aurora, biblioteca_estelar]:
        historia.atualizar_status('completa')

    garantir_avaliacao(torre, ana['leitor_id'], 5)
    garantir_avaliacao(torre, bruno['leitor_id'], 4)
    garantir_avaliacao(cartas, carla['leitor_id'], 5)
    garantir_avaliacao(bronze, ana['leitor_id'], 4)
    garantir_avaliacao(biblioteca_estelar, ana['leitor_id'], 5)

    garantir_comentario(torre, torre_c2, bruno['leitor_id'], 'Esse corredor silencioso criou um clima muito bom.')
    garantir_comentario(bronze, bronze_c1, carla['leitor_id'], 'A ideia da rua apagada ficou excelente.')

    UsuarioController.adicionar_historia_biblioteca(ana['leitor_id'], torre.id, 'lendo')
    UsuarioController.adicionar_historia_biblioteca(ana['leitor_id'], cartas.id, 'favoritos')
    UsuarioController.adicionar_historia_biblioteca(bruno['leitor_id'], bronze.id, 'lendo')
    UsuarioController.adicionar_historia_biblioteca(carla['leitor_id'], cartas.id, 'lendo')

    UsuarioController.atualizar_progresso(ana['leitor_id'], torre.id, 45, torre_c2.id)
    UsuarioController.atualizar_progresso(bruno['leitor_id'], bronze.id, 35, bronze_c1.id)

    DEMO_DADOS_INICIALIZADOS = True
    persistir_estado()


def token_da_requisicao() -> str:
    """Extrai token de header/query/body."""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.lower().startswith('bearer '):
        return auth_header[7:].strip()

    token_header = request.headers.get('X-Session-Token', '').strip()
    if token_header:
        return token_header

    token_query = request.args.get('token', '').strip()
    if token_query:
        return token_query

    dados = request.get_json(silent=True)
    if isinstance(dados, dict):
        return str(dados.get('token', '')).strip()

    return ''


def require_auth(func):
    """Middleware de autenticação para endpoints privados."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = token_da_requisicao()
        contexto = UsuarioController.contexto_por_token(token)
        if not contexto.get('sucesso'):
            return resposta_api(contexto, contexto.get('codigo', 401))

        conta = contexto['conta']
        g.auth_token = token
        g.auth = {
            'conta_id': conta['id'],
            'nome': conta['nome'],
            'email': conta['email'],
            'leitor_id': conta['leitor_id'],
            'autor_id': conta['autor_id'],
            'foto_perfil': conta.get('foto_perfil'),
        }
        return func(*args, **kwargs)

    return wrapper


@app.after_request
def persistencia_automatica(response):
    """Salva alterações em operações mutáveis da API."""
    if (
        request.path.startswith('/api/')
        and request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}
        and response.status_code < 400
    ):
        persistir_estado()
    return response


@app.route('/')
def login_page():
    """Tela de login/cadastro."""
    inicializar_dados_demo()
    return render_template('login.html')


@app.route('/cadastro')
def cadastro_page():
    """Tela dedicada de cadastro."""
    inicializar_dados_demo()
    return render_template('cadastro.html')


@app.route('/app')
def app_default():
    """Rota padrão da área autenticada."""
    return redirect(url_for('app_screen', pagina='inicio'))


@app.route('/app/<pagina>')
def app_screen(pagina):
    """Renderiza as telas separadas da aplicação."""
    if pagina not in PAGINAS_APP:
        return redirect(url_for('app_default'))
    inicializar_dados_demo()
    return render_template('app.html', pagina=pagina)


@app.route('/api/auth/register', methods=['POST'])
def auth_register():
    dados = obter_json_requisicao()
    resultado = UsuarioController.registrar_conta(
        dados.get('nome'),
        dados.get('email'),
        dados.get('senha'),
    )
    return resposta_api(resultado, 201 if resultado['sucesso'] else 400)


@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    dados = obter_json_requisicao()
    resultado = UsuarioController.login(
        dados.get('email'),
        dados.get('senha'),
    )
    return resposta_api(resultado, 200 if resultado['sucesso'] else 401)


@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    dados = obter_json_requisicao()
    token = dados.get('token') or token_da_requisicao()
    resultado = UsuarioController.logout(token)
    return resposta_api(resultado, 200 if resultado['sucesso'] else 401)


@app.route('/api/auth/me', methods=['GET'])
@require_auth
def auth_me():
    return resposta_api({'sucesso': True, 'usuario': g.auth})


@app.route('/api/me/painel', methods=['GET'])
@require_auth
def me_painel():
    inicializar_dados_demo()
    resultado = UsuarioController.obter_painel_hibrido(g.auth_token)
    return resposta_api(resultado)


@app.route('/api/me/perfil/foto', methods=['POST'])
@require_auth
def me_foto_perfil():
    dados = obter_json_requisicao()
    resultado = UsuarioController.atualizar_foto_perfil(
        g.auth_token,
        dados.get('foto_perfil'),
    )
    return resposta_api(resultado, 200 if resultado['sucesso'] else 400)


@app.route('/api/me/catalogo', methods=['GET'])
@require_auth
def me_catalogo():
    inicializar_dados_demo()
    resultado = HistoriaController.listar_historias(
        busca=request.args.get('q', ''),
        genero=request.args.get('genero', ''),
        ordem=request.args.get('ordem', 'destaques'),
        leitor_id=g.auth['leitor_id'],
    )
    return resposta_api(resultado)


@app.route('/api/me/historias/<historia_id>', methods=['GET'])
@require_auth
def me_obter_historia(historia_id):
    inicializar_dados_demo()
    resultado = HistoriaController.obter_historia(historia_id, leitor_id=g.auth['leitor_id'])
    return resposta_api(resultado)


@app.route('/api/me/historias/<historia_id>/capitulos/<capitulo_id>', methods=['GET'])
@require_auth
def me_obter_capitulo(historia_id, capitulo_id):
    inicializar_dados_demo()
    resultado = HistoriaController.obter_capitulo(
        historia_id,
        capitulo_id,
        usuario_id=g.auth['leitor_id'],
    )
    return resposta_api(resultado)


@app.route('/api/me/biblioteca', methods=['GET'])
@require_auth
def me_biblioteca():
    inicializar_dados_demo()
    resultado = UsuarioController.obter_biblioteca(g.auth['leitor_id'])
    return resposta_api(resultado)


@app.route('/api/me/biblioteca', methods=['POST'])
@require_auth
def me_salvar_biblioteca():
    dados = obter_json_requisicao()
    resultado = UsuarioController.salvar_na_biblioteca(
        g.auth_token,
        dados.get('historia_id'),
        dados.get('categoria'),
    )
    return resposta_api(resultado, 201 if resultado['sucesso'] else 400)


@app.route('/api/me/progresso', methods=['POST'])
@require_auth
def me_progresso():
    dados = obter_json_requisicao()
    resultado = UsuarioController.atualizar_progresso_por_token(
        g.auth_token,
        dados.get('historia_id'),
        dados.get('percentual'),
        dados.get('capitulo_id'),
    )
    return resposta_api(resultado, 201 if resultado['sucesso'] else 400)


@app.route('/api/me/avaliar', methods=['POST'])
@require_auth
def me_avaliar():
    dados = obter_json_requisicao()
    resultado = UsuarioController.avaliar_historia_por_token(
        g.auth_token,
        dados.get('historia_id'),
        dados.get('nota'),
    )
    return resposta_api(resultado, 201 if resultado['sucesso'] else 400)


@app.route('/api/me/comentar', methods=['POST'])
@require_auth
def me_comentar():
    dados = obter_json_requisicao()
    resultado = UsuarioController.comentar_capitulo_por_token(
        g.auth_token,
        dados.get('historia_id'),
        dados.get('capitulo_id'),
        dados.get('conteudo'),
    )
    return resposta_api(resultado, 201 if resultado['sucesso'] else 400)


@app.route('/api/me/comentar', methods=['PUT'])
@require_auth
def me_editar_comentario():
    dados = obter_json_requisicao()
    resultado = UsuarioController.editar_comentario_por_token(
        g.auth_token,
        dados.get('historia_id'),
        dados.get('capitulo_id'),
        dados.get('comentario_id'),
        dados.get('conteudo'),
    )
    return resposta_api(resultado, 200 if resultado['sucesso'] else 400)


@app.route('/api/me/comentar', methods=['DELETE'])
@require_auth
def me_excluir_comentario():
    dados = obter_json_requisicao()
    resultado = UsuarioController.excluir_comentario_por_token(
        g.auth_token,
        dados.get('historia_id'),
        dados.get('capitulo_id'),
        dados.get('comentario_id'),
    )
    return resposta_api(resultado, 200 if resultado['sucesso'] else 400)


@app.route('/api/me/destaques', methods=['POST'])
@require_auth
def me_destacar_trecho():
    dados = obter_json_requisicao()
    resultado = UsuarioController.destacar_trecho_por_token(
        g.auth_token,
        dados.get('historia_id'),
        dados.get('capitulo_id'),
        dados.get('trecho'),
    )
    return resposta_api(resultado, 201 if resultado['sucesso'] else 400)


@app.route('/api/me/destaques', methods=['DELETE'])
@require_auth
def me_remover_destaque():
    dados = obter_json_requisicao()
    resultado = UsuarioController.remover_destaque_por_token(
        g.auth_token,
        dados.get('historia_id'),
        dados.get('capitulo_id'),
        dados.get('trecho'),
    )
    return resposta_api(resultado, 200 if resultado['sucesso'] else 400)


@app.route('/api/me/tempo-leitura', methods=['POST'])
@require_auth
def me_tempo_leitura():
    dados = obter_json_requisicao()
    resultado = UsuarioController.registrar_tempo_leitura_por_token(
        g.auth_token,
        dados.get('historia_id'),
        dados.get('capitulo_id'),
        dados.get('pagina_global'),
        dados.get('segundos'),
        sessao_id=dados.get('sessao_id') or dados.get('session_id'),
    )
    return resposta_api(resultado, 201 if resultado['sucesso'] else 400)


@app.route('/api/me/autoria/historias', methods=['GET'])
@require_auth
def me_autoria_historias():
    inicializar_dados_demo()
    resultado = UsuarioController.listar_minhas_historias(g.auth_token)
    return resposta_api(resultado)


@app.route('/api/me/autoria/epub-metadata', methods=['POST'])
@require_auth
def me_autoria_epub_metadata():
    dados = obter_json_requisicao()
    resultado = UsuarioController.consultar_metadados_epub_por_token(
        g.auth_token,
        dados.get('epub'),
    )
    return resposta_api(resultado, 200 if resultado.get('sucesso') else 400)


@app.route('/api/me/autoria/historias', methods=['POST'])
@require_auth
def me_autoria_publicar():
    dados = obter_json_requisicao()
    resultado = UsuarioController.publicar_historia(
        g.auth_token,
        dados.get('titulo'),
        dados.get('sinopse'),
        dados.get('genero'),
        dados.get('capa'),
        epub_data=dados.get('epub'),
        preview_video=dados.get('preview'),
    )
    return resposta_api(resultado, 201 if resultado['sucesso'] else 400)


@app.route('/api/me/autoria/historias/<historia_id>', methods=['PUT'])
@require_auth
def me_autoria_editar_historia(historia_id):
    dados = obter_json_requisicao()
    resultado = UsuarioController.editar_historia_por_token(
        g.auth_token,
        historia_id,
        dados.get('titulo'),
        dados.get('sinopse'),
        dados.get('genero'),
        dados.get('capa') if 'capa' in dados else None,
    )
    return resposta_api(resultado, 200 if resultado['sucesso'] else 400)


@app.route('/api/me/autoria/historias/<historia_id>/capitulos', methods=['POST'])
@require_auth
def me_autoria_capitulo(historia_id):
    dados = obter_json_requisicao()
    resultado = UsuarioController.adicionar_capitulo_por_token(
        g.auth_token,
        historia_id,
        dados.get('titulo'),
        dados.get('conteudo'),
    )
    return resposta_api(resultado, 201 if resultado['sucesso'] else 400)


@app.route('/api/me/autoria/historias/<historia_id>/capitulos/<capitulo_id>', methods=['PUT'])
@require_auth
def me_autoria_editar_capitulo(historia_id, capitulo_id):
    dados = obter_json_requisicao()
    resultado = UsuarioController.editar_capitulo_por_token(
        g.auth_token,
        historia_id,
        capitulo_id,
        dados.get('titulo'),
        dados.get('conteudo'),
    )
    return resposta_api(resultado, 200 if resultado['sucesso'] else 400)


@app.route('/api/me/autoria/historias/<historia_id>/capitulos/<capitulo_id>', methods=['DELETE'])
@require_auth
def me_autoria_excluir_capitulo(historia_id, capitulo_id):
    resultado = UsuarioController.excluir_capitulo_por_token(
        g.auth_token,
        historia_id,
        capitulo_id,
    )
    return resposta_api(resultado, 200 if resultado['sucesso'] else 400)


@app.route('/api/status', methods=['GET'])
def status():
    """Status da API."""
    inicializar_dados_demo()
    persistencia = obter_status_persistencia()
    return resposta_api({
        'status': 'online',
        'aplicacao': 'StoryFlow Hibrido',
        'versao': '4.0.0',
        'timestamp': datetime.now().isoformat(),
        'historias': len(historias_db),
        'usuarios': len(usuarios_db),
        'contas': len(contas_db),
        'persistencia': persistencia,
    })


@app.route('/api/teste/dados', methods=['GET'])
def dados_teste():
    """Garante os dados demo do sistema."""
    inicializar_dados_demo()
    return resposta_api({
        'sucesso': True,
        'mensagem': 'Dados demo carregados',
        'historias_total': len(historias_db),
        'usuarios_total': len(usuarios_db),
        'contas_total': len(contas_db),
    })


@app.errorhandler(404)
def nao_encontrado(error):
    """Tratador de erro 404."""
    return jsonify({
        'sucesso': False,
        'erro': 'Recurso não encontrado',
        'codigo': 404
    }), 404


@app.errorhandler(500)
def erro_servidor(error):
    """Tratador de erro 500."""
    return jsonify({
        'sucesso': False,
        'erro': 'Erro interno do servidor',
        'codigo': 500
    }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5219)
