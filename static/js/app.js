const API_BASE = '/api';
const TOKEN_KEY = 'storyflow_token';
const PAGE = window.STORYFLOW_PAGE || 'inicio';
const READER_FONTS = new Set(['serif_classic', 'georgia', 'book', 'sans_clean']);
const READER_BACKGROUNDS = new Set(['paper_yellow', 'cream', 'off_white', 'sepia_dark', 'site_night']);
const READER_SPREAD_SEPARATOR = '\u001f';

const state = {
    page: PAGE,
    token: null,
    user: null,
    painel: null,
    biblioteca: null,
    minhasHistorias: [],
    catalogo: [],
    catalogoFiltros: {generos_disponiveis: []},
    historiaDetalhe: null,
    autoriaSelecionadaId: null,
    capituloEditandoId: null,
    capituloAtivo: null,
    readerPagination: {
        pages: [],
        currentPage: 0,
        wordsPerPage: 120,
        wordsPerSpread: 240,
        currentGlobalPage: 1,
        measurerEl: null,
    },
    readerSession: {
        id: null,
        startedAt: null,
        pageStartedAt: null,
        intervalId: null,
        autoSaveIntervalId: null,
        unsentSeconds: 0,
    },
    readerPrefs: {
        fontFamily: 'serif_classic',
        fontSize: 24,
        bgColor: 'paper_yellow',
    },
    filtros: {
        q: '',
        genero: '',
        ordem: 'destaques',
    },
    writer: {
        screen: 'book',
        chapterScreen: 'list',
        autoCoverFromEpub: null,
        epubMetadata: null,
    },
    debounce: null,
};

const el = {};

document.addEventListener('DOMContentLoaded', async () => {
    cacheElements();
    carregarPreferenciasLeitor();
    sincronizarControlesLeitor();
    bindGlobalEvents();
    if (!(await garantirSessao())) {
        return;
    }

    aplicarFiltrosDaURL();
    sincronizarInputsBusca();
    await carregarTela();
});

function cacheElements() {
    el.toast = document.getElementById('toast');
    el.logout = document.getElementById('logout-button');
    el.headerUserName = document.getElementById('header-user-name');
    el.globalSearch = document.getElementById('global-search');
    el.sidebarAvatar = document.getElementById('sidebar-avatar');
    el.sidebarAvatarLetter = document.getElementById('sidebar-avatar-letter');

    el.inicioDestaque = document.getElementById('inicio-destaque');
    el.inicioRecomendacoes = document.getElementById('inicio-recomendacoes');
    el.inicioContinuar = document.getElementById('inicio-continuar');
    el.inicioCategorias = document.getElementById('inicio-categorias');
    el.inicioEmAlta = document.getElementById('inicio-em-alta');

    el.historiasBusca = document.getElementById('historias-busca');
    el.historiasGenero = document.getElementById('historias-genero');
    el.historiasOrdem = document.getElementById('historias-ordem');
    el.historiasGrid = document.getElementById('historias-grid');
    el.historiaDetalhe = document.getElementById('historia-detalhe');

    el.sumTotal = document.getElementById('sum-total');
    el.sumLendo = document.getElementById('sum-lendo');
    el.sumFavoritos = document.getElementById('sum-favoritos');
    el.sumConcluidos = document.getElementById('sum-concluidos');
    el.bibliotecaCategorias = document.getElementById('biblioteca-categorias');
    el.bibliotecaProgresso = document.getElementById('biblioteca-progresso');

    el.formNovaHistoria = document.getElementById('nova-historia-form');
    el.formNovoCapitulo = document.getElementById('novo-capitulo-form');
    el.writerEditorModal = document.getElementById('writer-editor-modal');
    el.writerEditorBackdrop = document.getElementById('writer-editor-backdrop');
    el.writerEditorClose = document.getElementById('writer-editor-close');
    el.writerEditorTitle = document.getElementById('writer-editor-title');
    el.writerEditorMode = document.getElementById('writer-editor-mode');
    el.historiaEditId = document.getElementById('historia-edit-id');
    el.historiaSubmit = document.getElementById('historia-submit');
    el.writerModalChaptersList = document.getElementById('writer-modal-chapters-list');
    el.writerScreenBookBtn = document.getElementById('writer-screen-book-btn');
    el.writerScreenChaptersBtn = document.getElementById('writer-screen-chapters-btn');
    el.storyCoverPreview = document.getElementById('story-cover-preview');
    el.storyCoverInput = document.getElementById('story-cover-input');
    el.storyFileInput = document.getElementById('story-file-input');
    el.storyTitleInput = document.getElementById('story-title-input');
    el.storyGenreInput = document.getElementById('story-genre-input');
    el.storySynopsisInput = document.getElementById('story-synopsis');
    el.storyEpubMetaHint = document.getElementById('story-epub-meta-hint');
    el.writerChapterListBtn = document.getElementById('writer-chapter-list-btn');
    el.writerChapterEditorBtn = document.getElementById('writer-chapter-editor-btn');
    el.capituloHistoriaId = document.getElementById('capitulo-historia-id');
    el.capituloEditId = document.getElementById('capitulo-edit-id');
    el.capituloFormTitle = document.getElementById('capitulo-form-title');
    el.capituloFormHint = document.getElementById('capitulo-form-hint');
    el.capituloSubmit = document.getElementById('capitulo-submit');
    el.capituloBackList = document.getElementById('capitulo-back-list');
    el.capituloEditCancel = document.getElementById('capitulo-edit-cancel');
    el.autoriaHistorias = document.getElementById('autoria-historias');
    el.writerAddTopButton = document.querySelector('.writer-add-book-card');

    el.perfilNome = document.getElementById('perfil-nome');
    el.perfilEmail = document.getElementById('perfil-email');
    el.profileAvatar = document.getElementById('profile-avatar');
    el.profilePhotoForm = document.getElementById('profile-photo-form');
    el.profilePhotoInput = document.getElementById('profile-photo-input');
    el.profilePhotoRemove = document.getElementById('profile-photo-remove');
    el.voceStats = document.getElementById('voce-stats');
    el.voceProgresso = document.getElementById('voce-progresso');
    el.voceAutoria = document.getElementById('voce-autoria');

    el.readerModal = document.getElementById('reader-modal');
    el.readerCard = document.querySelector('.reader-card');
    el.readerBackdrop = document.getElementById('reader-modal-backdrop');
    el.readerClose = document.getElementById('reader-close');
    el.readerStoryName = document.getElementById('reader-story-name');
    el.readerChapterTitle = document.getElementById('reader-chapter-title');
    el.readerMeta = document.getElementById('reader-meta');
    el.readerContent = document.getElementById('reader-content');
    el.readerChapterSelect = document.getElementById('reader-chapter-select');
    el.readerTocList = document.getElementById('reader-toc-list');
    el.readerSidePanel = document.getElementById('reader-side-panel');
    el.readerPanelClose = document.getElementById('reader-panel-close');
    el.readerShowToc = document.getElementById('reader-show-toc');
    el.readerShowSettings = document.getElementById('reader-show-settings');
    el.readerProgressRange = document.getElementById('reader-progress-range');
    el.readerSampleBanner = document.getElementById('reader-sample-banner');
    el.readerSampleClose = document.getElementById('reader-sample-close');
    el.readerPredictedValue = document.getElementById('reader-predicted-value');
    el.readerBookTitleTop = document.getElementById('reader-book-title-top');
    el.readerPagePrev = document.getElementById('reader-page-prev');
    el.readerPageNext = document.getElementById('reader-page-next');
    el.readerPageCounter = document.getElementById('reader-page-counter');
    el.readerSessionTime = document.getElementById('reader-session-time');
    el.readerPageTime = document.getElementById('reader-page-time');
    el.readerChapterTime = document.getElementById('reader-chapter-time');
    el.readerBookTime = document.getElementById('reader-book-time');
    el.readerHighlight = document.getElementById('reader-highlight');
    el.readerMark = document.getElementById('reader-mark');
    el.readerFinish = document.getElementById('reader-finish');
    el.readerFontOptions = document.getElementById('reader-font-options');
    el.readerFontSize = document.getElementById('reader-font-size');
    el.readerFontSizeValue = document.getElementById('reader-font-size-value');
    el.readerBgOptions = document.getElementById('reader-bg-options');
    el.readerCommentsCount = document.getElementById('reader-comments-count');
    el.readerComments = document.getElementById('reader-comments');
    el.readerCommentForm = document.getElementById('reader-comment-form');
    el.readerCommentInput = document.getElementById('reader-comment-input');
    el.readerMarksCount = document.getElementById('reader-marks-count');
    el.readerMarksList = document.getElementById('reader-marks-list');
    el.readerSessionsCount = document.getElementById('reader-sessions-count');
    el.readerSessionsList = document.getElementById('reader-sessions-list');
}

function bindGlobalEvents() {
    el.logout?.addEventListener('click', encerrarSessao);

    // Clique no avatar abre seletor de arquivo para foto de perfil
    el.profileAvatar?.addEventListener('click', () => {
        if (el.profilePhotoInput) {
            el.profilePhotoInput.click();
        }
    });

    // Envio automático ao selecionar arquivo
    el.profilePhotoInput?.addEventListener('change', () => {
        if (el.profilePhotoForm) {
            el.profilePhotoForm.dispatchEvent(new Event('submit', {cancelable: true}));
        }
    });

    // Topbar: abrir editor de escrita com estilo de `btn-primary`
    el.writerAddTopButton?.addEventListener('click', (e) => {
        e.preventDefault();
        abrirEditorAutoria();
    });

    el.globalSearch?.addEventListener('input', (event) => {
        state.filtros.q = event.target.value.trim();
        sincronizarInputsBusca();

        if (!['inicio', 'historias'].includes(state.page)) {
            return;
        }
        clearTimeout(state.debounce);
        state.debounce = setTimeout(() => {
            carregarCatalogo().then(() => {
                if (state.page === 'inicio') {
                    renderInicio();
                } else {
                    renderHistorias();
                }
            }).catch(handleError);
        }, 280);
    });

    el.historiasBusca?.addEventListener('input', (event) => {
        state.filtros.q = event.target.value.trim();
        if (el.globalSearch) {
            el.globalSearch.value = state.filtros.q;
        }
        clearTimeout(state.debounce);
        state.debounce = setTimeout(async () => {
            try {
                await carregarCatalogo();
                renderHistorias();
            } catch (error) {
                handleError(error);
            }
        }, 280);
    });

    el.historiasGenero?.addEventListener('change', async (event) => {
        state.filtros.genero = event.target.value;
        await recarregarHistoriasComTratamento();
    });

    el.historiasOrdem?.addEventListener('change', async (event) => {
        state.filtros.ordem = event.target.value;
        await recarregarHistoriasComTratamento();
    });

    el.inicioDestaque?.addEventListener('click', handleStoryActionClick);
    el.inicioRecomendacoes?.addEventListener('click', handleStoryActionClick);
    el.inicioContinuar?.addEventListener('click', handleStoryActionClick);
    el.inicioCategorias?.addEventListener('click', handleStoryActionClick);
    el.inicioEmAlta?.addEventListener('click', handleStoryActionClick);
    el.historiasGrid?.addEventListener('click', handleStoryActionClick);
    el.historiaDetalhe?.addEventListener('click', handleStoryActionClick);
    el.bibliotecaCategorias?.addEventListener('click', handleStoryActionClick);
    el.bibliotecaProgresso?.addEventListener('click', handleStoryActionClick);
    el.voceProgresso?.addEventListener('click', handleStoryActionClick);
    el.voceAutoria?.addEventListener('click', handleStoryActionClick);
    el.autoriaHistorias?.addEventListener('click', handleStoryActionClick);
    el.writerModalChaptersList?.addEventListener('click', handleStoryActionClick);

    el.formNovaHistoria?.addEventListener('submit', publicarHistoria);
    el.formNovoCapitulo?.addEventListener('submit', publicarCapitulo);
    el.writerEditorBackdrop?.addEventListener('click', fecharEditorAutoria);
    el.writerEditorClose?.addEventListener('click', fecharEditorAutoria);
    el.writerScreenBookBtn?.addEventListener('click', () => definirTelaEditorAutoria('book'));
    el.writerScreenChaptersBtn?.addEventListener('click', () => definirTelaEditorAutoria('chapters'));
    el.writerChapterListBtn?.addEventListener('click', () => definirTelaCapitulos('list'));
    el.storyFileInput?.addEventListener('change', consultarMetadadosEpubSelecionado);
    el.storyCoverInput?.addEventListener('change', atualizarPreviewCapaSelecionada);
    el.capituloBackList?.addEventListener('click', () => limparEdicaoCapitulo(true));
    el.capituloEditCancel?.addEventListener('click', () => {
        limparEdicaoCapitulo(true);
    });
    el.formNovoCapitulo?.addEventListener('click', handleChapterFormatActionClick);
    el.capituloHistoriaId?.addEventListener('change', (event) => {
        abrirEditorAutoria(event.target.value);
        renderEscrever();
    });
    el.profilePhotoForm?.addEventListener('submit', enviarFotoPerfil);
    el.profilePhotoRemove?.addEventListener('click', removerFotoPerfil);

    el.readerBackdrop?.addEventListener('click', fecharLeitor);
    el.readerClose?.addEventListener('click', fecharLeitor);
    el.readerPagePrev?.addEventListener('click', navegarPaginaAnterior);
    el.readerPageNext?.addEventListener('click', navegarProximaPagina);
    el.readerShowToc?.addEventListener('click', () => alternarPainelLeitor('toc'));
    el.readerShowSettings?.addEventListener('click', () => alternarPainelLeitor('settings'));
    el.readerPanelClose?.addEventListener('click', () => {
        el.readerSidePanel?.classList.toggle('is-collapsed');
        if (el.readerSidePanel?.classList.contains('is-collapsed')) {
            el.readerShowToc?.classList.remove('is-active');
            el.readerShowSettings?.classList.remove('is-active');
        }
    });
    el.readerSampleClose?.addEventListener('click', () => {
        el.readerSampleBanner?.classList.add('hidden');
    });
    el.readerTocList?.addEventListener('click', async (event) => {
        const button = event.target.closest('[data-reader-chapter-id]');
        const storyId = state.capituloAtivo?.historia?.id;
        const chapterId = button?.dataset.readerChapterId;
        if (storyId && chapterId && chapterId !== state.capituloAtivo?.capitulo?.id) {
            await abrirCapitulo(storyId, chapterId);
        }
    });
    el.readerProgressRange?.addEventListener('change', async (event) => {
        await registrarTempoLeituraAtual();
        const alvo = Number(event.target.value || 1) - 1;
        state.readerPagination.currentPage = Math.max(0, Math.min((state.readerPagination.pages.length || 1) - 1, alvo));
        renderPaginaAtualLeitura();
    });
    el.readerChapterSelect?.addEventListener('change', async (event) => {
        const chapterId = event.target.value;
        const storyId = state.capituloAtivo?.historia?.id;
        if (storyId && chapterId && chapterId !== state.capituloAtivo?.capitulo?.id) {
            await abrirCapitulo(storyId, chapterId);
        }
    });
    el.readerFontSize?.addEventListener('input', onReaderPreferenceChanged);
    el.readerFontOptions?.addEventListener('click', handleReaderPreferenceOptionClick);
    el.readerBgOptions?.addEventListener('click', handleReaderPreferenceOptionClick);
    el.readerHighlight?.addEventListener('click', destacarSelecaoAtual);
    el.readerMarksList?.addEventListener('click', handleReaderMarksClick);
    el.readerCommentForm?.addEventListener('submit', comentarCapituloAtual);
    el.readerComments?.addEventListener('click', handleCommentActionClick);
    window.addEventListener('resize', handleResizeLeitor);
}

async function garantirSessao() {
    state.token = localStorage.getItem(TOKEN_KEY);
    if (!state.token) {
        redirecionarLogin();
        return false;
    }

    try {
        const response = await api('/auth/me');
        state.user = response.usuario;
        atualizarIdentidadeUI();
        return true;
    } catch (error) {
        redirecionarLogin();
        return false;
    }
}

function aplicarFiltrosDaURL() {
    const params = new URLSearchParams(window.location.search);
    state.filtros.q = params.get('q') || state.filtros.q;
    state.filtros.genero = params.get('genero') || state.filtros.genero;
    state.filtros.ordem = params.get('ordem') || state.filtros.ordem;
}

function sincronizarInputsBusca() {
    if (el.globalSearch) {
        el.globalSearch.value = state.filtros.q;
    }
    if (el.historiasBusca) {
        el.historiasBusca.value = state.filtros.q;
    }
}

async function carregarTela() {
    switch (state.page) {
        case 'inicio':
            await Promise.all([carregarPainel(), carregarCatalogo()]);
            renderInicio();
            break;
        case 'historias':
            await carregarCatalogo();
            renderHistorias();
            await selecionarHistoriaInicial();
            break;
        case 'biblioteca':
            await Promise.all([carregarBiblioteca(), carregarPainel()]);
            renderBiblioteca();
            break;
        case 'escrever':
            await carregarAutoria();
            renderEscrever();
            break;
        case 'voce':
            await carregarPainel();
            renderVoce();
            break;
        default:
            await carregarPainel();
            break;
    }
}

async function carregarPainel() {
    const response = await api('/me/painel');
    state.painel = response;
    state.minhasHistorias = response.autoria?.historias || [];
    state.biblioteca = response.leitura?.biblioteca || null;
    if (response.conta) {
        state.user = {...(state.user || {}), ...response.conta};
        atualizarIdentidadeUI();
    }
}

async function carregarCatalogo() {
    const response = await api('/me/catalogo', {
        query: {
            q: state.filtros.q,
            genero: state.filtros.genero,
            ordem: state.filtros.ordem,
        },
    });
    state.catalogo = response.historias || [];
    state.catalogoFiltros = response.filtros || {generos_disponiveis: []};
}

async function carregarBiblioteca() {
    const response = await api('/me/biblioteca');
    state.biblioteca = response.biblioteca || {};
}

async function carregarAutoria() {
    const response = await api('/me/autoria/historias');
    state.minhasHistorias = response.historias || [];
}

function renderInicio() {
    renderInicioDestaque();
    renderInicioRecomendacoes();
    renderInicioContinuar();
    renderInicioCategorias();
    renderInicioEmAlta();
}

function renderInicioDestaque() {
    if (!el.inicioDestaque) {
        return;
    }
    const destaque = state.catalogo[0];
    if (!destaque) {
        el.inicioDestaque.innerHTML = `<p class="placeholder">Nenhuma história encontrada no momento.</p>`;
        return;
    }

    const chapterId = destaque.progresso_leitor?.capitulo_id || destaque.capitulo_inicial_id;
    el.inicioDestaque.innerHTML = `
        <p class="chip">Em alta</p>
        <h2>${escapeHtml(destaque.titulo)}</h2>
        <p class="muted">${escapeHtml(destaque.sinopse)}</p>
        <p class="meta-line">${escapeHtml(destaque.autor || 'Autor desconhecido')} · ${escapeHtml(destaque.genero || 'Leitura')}</p>
        <div class="inline-actions">
            <button class="btn-ghost" data-action="abrir-historia" data-story-id="${destaque.id}" type="button">Ler agora</button>
            <button class="btn-primary" data-action="abrir-capitulo" data-story-id="${destaque.id}" data-chapter-id="${chapterId || ''}" type="button">
                ${destaque.progresso_leitor ? 'Continuar' : 'Ler agora'}
            </button>
            <button class="btn-ghost" data-action="salvar-historia" data-story-id="${destaque.id}" data-categoria="lendo" type="button">Salvar</button>
        </div>
    `;
}

function renderInicioRecomendacoes() {
    if (!el.inicioRecomendacoes) {
        return;
    }
    const recomendadas = (state.painel?.leitura?.recomendacoes || []).filter((story) => {
        const semAvaliacao = Number(story?.total_avaliacoes || 0) === 0;
        const curtida = Number(story?.minha_avaliacao || 0) >= 4;
        return semAvaliacao || curtida;
    });
    if (!recomendadas.length) {
        el.inicioRecomendacoes.innerHTML = `
            <h3>Recomendados para você</h3>
            <p class="placeholder">Sem recomendações por enquanto. Continue lendo para personalizar.</p>
        `;
        return;
    }

    el.inicioRecomendacoes.innerHTML = `
        <h3>Recomendados para você</h3>
        <div class="stack-list">
            ${recomendadas.slice(0, 3).map((story) => `
                <article class="compact-story">
                    <div>
                        <strong>${escapeHtml(story.titulo)}</strong>
                        <p class="muted">${escapeHtml(story.autor || 'Autor')} · ${escapeHtml(story.genero || 'Leitura')}</p>
                    </div>
                    <button class="btn-ghost" data-action="abrir-historia" data-story-id="${story.id}" type="button">Ler</button>
                </article>
            `).join('')}
        </div>
    `;
}

function renderInicioContinuar() {
    if (!el.inicioContinuar) {
        return;
    }
    const progresso = state.painel?.leitura?.progresso || [];
    if (!progresso.length) {
        el.inicioContinuar.innerHTML = `<p class="placeholder">Você ainda não iniciou nenhuma leitura.</p>`;
        return;
    }
    const item = progresso[0];
    const chapterId = item.capitulo_id || item.historia.capitulo_inicial_id;
    el.inicioContinuar.innerHTML = `
        <div class="player-row">
            <div>
                <strong>${escapeHtml(item.historia.titulo)}</strong>
                <p class="muted">${escapeHtml(item.capitulo_titulo || 'Capítulo inicial')}</p>
            </div>
            <button class="btn-primary" data-action="abrir-capitulo" data-story-id="${item.historia.id}" data-chapter-id="${chapterId || ''}" type="button">
                Continuar leitura
            </button>
        </div>
        <div class="progress">
            <span style="width:${item.percentual}%"></span>
        </div>
        <p class="muted">${item.percentual}% concluído</p>
    `;
}

function renderInicioCategorias() {
    if (!el.inicioCategorias) {
        return;
    }
    const generos = [...new Set((state.catalogo || []).map((story) => story.genero).filter(Boolean))];
    el.inicioCategorias.innerHTML = generos.length
        ? generos.map((genero) => `<button class="chip" data-action="filtrar-genero" data-genero="${escapeHtml(genero)}" type="button">${escapeHtml(genero)}</button>`).join('')
        : `<span class="placeholder">Sem gêneros disponíveis.</span>`;
}

function renderInicioEmAlta() {
    if (!el.inicioEmAlta) {
        return;
    }
    // Algoritmo de recomendação com pesos por gênero e probabilidades
    const maxItems = 8;
    const included = new Set();
    const output = [];

    // 1) Sempre prioriza itens de "continuar lendo"
    const progresso = (state.painel?.leitura?.progresso || []);
    for (const p of progresso) {
        const historia = p.historia;
        if (historia && !included.has(historia.id)) {
            included.add(historia.id);
            output.push(historia);
            if (output.length >= maxItems) break;
        }
    }

    // 2) Calcula pontuação por gênero com base nas avaliações do usuário
    const genreScores = {};
    const sources = [...(state.catalogo || []), ...(state.minhasHistorias || [])];
    for (const s of sources) {
        if (!s || !s.genero) continue;
        const g = String(s.genero);
        const nota = Number(s?.minha_avaliacao || 0);
        genreScores[g] = genreScores[g] || 0;
        if (nota >= 5) {
            genreScores[g] += 6.0;
        } else if (nota >= 4) {
            genreScores[g] += 3.0;
        } else if (nota <= 2 && nota > 0) {
            genreScores[g] -= 10.0;
        }
    }

    // 3) Gera candidatos com score combinado
    const candidates = (state.catalogo || []).filter((s) => s && !included.has(s.id));
    const scored = candidates.map((s) => {
        const media = Number(s.media_avaliacoes || 0);
        const total = Number(s.total_avaliacoes || 0);
        const genero = s.genero || '';
        let score = 0;
        // sinais públicos: média e volume ajudam
        score += media * 1.2;
        score += Math.log(1 + total) * 0.6;
        // boost por gênero preferido
        if (genreScores[genero]) score += genreScores[genero] * 1.2;
        // boost se o próprio leitor avaliou com 'amei' ou 'gostei'
        const minha = Number(s?.minha_avaliacao || 0);
        if (minha >= 5) score += 10; // garantir presença na home
        else if (minha >= 4) score += 4; // preferir
        else if (minha > 0 && minha <= 2) score -= 12; // penaliza forte

        return {story: s, score};
    });

    if (!scored.length && !output.length) {
        el.inicioEmAlta.innerHTML = `<p class="placeholder">Sem histórias em alta agora.</p>`;
        return;
    }

    // 4) Normaliza scores em probabilidades via softmax (exp) e ordena
    const exps = scored.map((c) => Math.exp(Math.max(-20, Math.min(20, c.score))));
    const sumExp = exps.reduce((a, b) => a + b, 0) || 1;
    const scoredWithProb = scored.map((c, i) => {
        const prob = exps[i] / sumExp;
        // anexa probabilidade percentual ao objeto de história para possível exibição
        c.story.recommendation_probability = Math.round(prob * 100);
        return {...c, prob};
    });

    // Ordena por probabilidade (decrescente) e inclui até preencher o máximo
    scoredWithProb.sort((a, b) => b.prob - a.prob);
    for (const item of scoredWithProb) {
        if (output.length >= maxItems) break;
        if (!item.story || included.has(item.story.id)) continue;
        // regras adicionais: se o usuário marcou 'não gostei' (minha_avaliacao <=2) omitimos frequentemente
        const minha = Number(item.story?.minha_avaliacao || 0);
        if (minha > 0 && minha <= 2) {
            // chance muito baixa — ignora a menos que ainda faltem itens
            if (output.length + 2 < maxItems) continue;
        }
        included.add(item.story.id);
        output.push(item.story);
    }

    // 5) Garanta que qualquer livro com 'gostei' ou 'amei' esteja visível se houver espaço
    for (const s of candidates) {
        if (output.length >= maxItems) break;
        const minha = Number(s?.minha_avaliacao || 0);
        if ((minha >= 4) && !included.has(s.id)) {
            included.add(s.id);
            output.push(s);
        }
    }

    el.inicioEmAlta.innerHTML = output.map((story) => {
        // garante que exista a propriedade de probabilidade
        if (typeof story.recommendation_probability === 'undefined') story.recommendation_probability = 0;
        return renderStoryCard(story);
    }).join('');
}

function renderHistorias() {
    if (!el.historiasGrid) {
        return;
    }
    renderFiltrosHistorias();
    el.historiasGrid.innerHTML = state.catalogo.length
        ? state.catalogo.map((story) => renderStoryCard(story)).join('')
        : `<p class="placeholder">Nenhuma história encontrada com os filtros atuais.</p>`;
}

function renderFiltrosHistorias() {
    if (!el.historiasGenero || !el.historiasOrdem) {
        return;
    }
    const generos = state.catalogoFiltros.generos_disponiveis || [];
    el.historiasGenero.innerHTML = `
        <option value="">Todos os gêneros</option>
        ${generos.map((g) => `<option value="${escapeHtml(g)}">${escapeHtml(g)}</option>`).join('')}
    `;
    el.historiasGenero.value = state.filtros.genero;
    el.historiasOrdem.value = state.filtros.ordem;
}

async function selecionarHistoriaInicial() {
    if (!el.historiaDetalhe) {
        return;
    }
    const params = new URLSearchParams(window.location.search);
    const requested = params.get('story');
    const first = state.catalogo[0]?.id;
    const storyId = requested || first;
    if (!storyId) {
        el.historiaDetalhe.innerHTML = `<p class="placeholder">Selecione uma história para ver capítulos e ler.</p>`;
        return;
    }
    await selecionarHistoria(storyId);
}

async function selecionarHistoria(storyId) {
    const response = await api(`/me/historias/${encodeURIComponent(storyId)}`);
    state.historiaDetalhe = response.historia;
    atualizarQueryHistoria(storyId);
    renderDetalheHistoria();
}

function renderDetalheHistoria() {
    if (!el.historiaDetalhe) {
        return;
    }
    const story = state.historiaDetalhe;
    if (!story) {
        el.historiaDetalhe.innerHTML = `<p class="placeholder">Selecione uma história para visualizar detalhes.</p>`;
        return;
    }

    const progresso = story.progresso_leitor?.percentual;
    const sentimentoSelecionado = notaParaSentimento(story.minha_avaliacao);
    el.historiaDetalhe.innerHTML = `
        <p class="chip">${escapeHtml(story.genero || 'Leitura')}</p>
        <h3>${escapeHtml(story.titulo)}</h3>
        <p class="muted">por ${escapeHtml(story.autor || 'Autor desconhecido')}</p>
        <p class="muted">${escapeHtml(story.sinopse)}</p>
        <p class="meta-line">${story.total_capitulos} capítulos · nota ${Number(story.media_avaliacoes || 0).toFixed(1)} (${Number(story.total_avaliacoes || 0)} avaliações)</p>
        ${typeof progresso === 'number' ? `<p class="muted">Seu progresso: ${progresso}%</p>` : ''}
        <div class="inline-actions">
            <button class="btn-primary" data-action="abrir-capitulo" data-story-id="${story.id}" data-chapter-id="${story.progresso_leitor?.capitulo_id || story.capitulo_inicial_id || ''}" type="button">Ler</button>
            <button class="btn-ghost" data-action="salvar-historia" data-story-id="${story.id}" data-categoria="favoritos" type="button">Favoritar</button>
        </div>
        <div class="rating-range-card">
            <label class="muted">Sua avaliação</label>
            <div class="story-sentiment-group" role="group" aria-label="Avaliar história">
                <button
                    type="button"
                    class="story-sentiment-btn ${sentimentoSelecionado === 'amei' ? 'is-active' : ''}"
                    data-action="avaliar-sentimento"
                    data-story-id="${story.id}"
                    data-sentimento-voto="amei"
                >
                    Amei
                </button>
                <button
                    type="button"
                    class="story-sentiment-btn ${sentimentoSelecionado === 'gostei' ? 'is-active' : ''}"
                    data-action="avaliar-sentimento"
                    data-story-id="${story.id}"
                    data-sentimento-voto="gostei"
                >
                    Gostei
                </button>
                <button
                    type="button"
                    class="story-sentiment-btn ${sentimentoSelecionado === 'nao_gostei' ? 'is-active' : ''}"
                    data-action="avaliar-sentimento"
                    data-story-id="${story.id}"
                    data-sentimento-voto="nao_gostei"
                >
                    Não gostei
                </button>
            </div>
        </div>
        <div class="stack-list">
            ${(story.capitulos || []).map((chapter) => `
                <button class="list-button" data-action="abrir-capitulo" data-story-id="${story.id}" data-chapter-id="${chapter.id}" type="button">
                    <div>
                        <strong>${chapter.ordem}. ${escapeHtml(chapter.titulo)}</strong>
                        <p class="muted">${chapter.tempo_estimado_minutos} min · ${chapter.comentarios} comentários</p>
                    </div>
                    <span>Ler</span>
                </button>
            `).join('')}
        </div>
    `;
    const initialRating = (typeof story.minha_avaliacao === 'number' && story.minha_avaliacao > 0)
        ? Number(story.minha_avaliacao)
        : 4;
    atualizarSeletorAvaliacao(initialRating, {storyId: story.id});
}

function renderBiblioteca() {
    if (!state.biblioteca || !el.bibliotecaCategorias) {
        return;
    }
    el.sumTotal.textContent = String(state.biblioteca.total || 0);
    el.sumLendo.textContent = String(state.biblioteca.lendo || 0);
    el.sumFavoritos.textContent = String(state.biblioteca.favoritos || 0);
    el.sumConcluidos.textContent = String(state.biblioteca.concluidos || 0);
    const categorias = state.biblioteca.categorias || {};
    const ordem = ['Lendo', 'Favoritos', 'Pausados', 'Concluídos'];
    el.bibliotecaCategorias.innerHTML = ordem.map((nome) => {
        const historias = categorias[nome] || [];
        return `
            <section class="shelf-card">
                <div class="section-head">
                    <h3>${nome}</h3>
                    <span class="chip">${historias.length}</span>
                </div>
                <div class="stack-list">
                    ${historias.length ? historias.map((story) => {
                        const tempoTotal = story?.tempo_leitura?.total_segundos || 0;
                        const palavras = story?.total_palavras || 0;
                        const palavrasPorPagina = calcularPalavrasPorPagina();
                        const paginasEstimadas = Math.max(1, Math.ceil(palavras / Math.max(1, palavrasPorPagina)));
                        const tempoPorPagina = paginasEstimadas ? Math.round((tempoTotal || 0) / paginasEstimadas) : 0;
                        return `
                        <button class="list-button" data-action="abrir-historia" data-story-id="${story.id}" type="button">
                            <div class="mini-cover">${renderStoryCover(story)}</div>
                            <div>
                                <strong>${escapeHtml(story.titulo)}</strong>
                                <p class="muted">${escapeHtml(story.autor || 'Autor')}</p>
                                ${tempoTotal ? `<p class="muted">Tempo gasto: ${formatarTempo(tempoTotal)} · ${tempoPorPagina ? `~${formatarTempo(tempoPorPagina)}/página` : ''}</p>` : ''}
                            </div>
                            <span>Ler</span>
                        </button>`;
                    }).join('') : `<p class="placeholder">Sem histórias nesta categoria.</p>`}
                </div>
            </section>
        `;
    }).join('');

    const progresso = state.painel?.leitura?.progresso || [];
    el.bibliotecaProgresso.innerHTML = progresso.length
        ? progresso.map((item) => {
            const tempoTotal = item.historia?.tempo_leitura?.total_segundos || item.tempo_segundos || 0;
            const palavras = item.historia?.total_palavras || 0;
            const palavrasPorPagina = calcularPalavrasPorPagina();
            const paginasEstimadas = Math.max(1, Math.ceil(palavras / Math.max(1, palavrasPorPagina)));
            const tempoPorPagina = paginasEstimadas ? Math.round((tempoTotal || 0) / paginasEstimadas) : 0;
            return `
            <article class="compact-story">
                <div>
                    <div class="mini-cover">${renderStoryCover(item.historia)}</div>
                    <strong>${escapeHtml(item.historia.titulo)}</strong>
                    <p class="muted">${escapeHtml(item.capitulo_titulo || 'Capítulo inicial')}</p>
                    <div class="progress"><span style="width:${item.percentual}%"></span></div>
                    ${tempoTotal ? `<p class="muted">Tempo gasto: ${formatarTempo(tempoTotal)} · ${tempoPorPagina ? `~${formatarTempo(tempoPorPagina)}/página` : ''}</p>` : ''}
                </div>
                <button class="btn-ghost" data-action="abrir-capitulo" data-story-id="${item.historia.id}" data-chapter-id="${item.capitulo_id || item.historia.capitulo_inicial_id || ''}" type="button">Continuar</button>
            </article>
        `;
        }).join('')
        : `<p class="placeholder">Você ainda não tem leituras em andamento.</p>`;
}

function renderEscrever() {
    if (!el.autoriaHistorias) {
        return;
    }
    const historias = state.minhasHistorias || [];
    const livros = historias.map((story) => `
        <article class="writer-book-card ${story.id === state.autoriaSelecionadaId ? 'is-selected' : ''}">
            <button class="writer-book-cover" data-action="selecionar-escrita" data-story-id="${escapeAttribute(story.id)}" type="button" aria-label="Editar ${escapeAttribute(story.titulo)}">
                ${renderStoryCover(story)}
            </button>
            <div class="writer-book-info">
                <strong>${escapeHtml(story.titulo)}</strong>
                <span>${story.total_capitulos} capítulos · ${escapeHtml(story.genero || 'Geral')}</span>
            </div>
        </article>
    `).join('');

    el.autoriaHistorias.innerHTML = `
        <button class="writer-add-book-card" data-action="nova-historia" type="button" aria-label="Adicionar novo livro">
            <span>+</span>
            <strong>Novo livro</strong>
        </button>
        ${livros || `<p class="placeholder writer-empty-state">Sua biblioteca de criação está vazia.</p>`}
    `;

    if (el.capituloHistoriaId) {
        el.capituloHistoriaId.innerHTML = historias.length
            ? historias.map((story) => `<option value="${escapeAttribute(story.id)}">${escapeHtml(story.titulo)}</option>`).join('')
            : `<option value="">Nenhuma história publicada</option>`;
    }
    sincronizarFormularioCapituloAutoria();
}

function ehLivroImportadoPorEpub(story) {
    return Boolean(story?.tem_epub);
}

function definirTelaEditorAutoria(screen) {
    if (!el.writerEditorModal || !['book', 'chapters'].includes(screen)) {
        return;
    }
    if (screen === 'chapters' && !obterHistoriaAutoriaSelecionada()) {
        showToast('Crie o livro primeiro para abrir a tela de capítulos.', true);
        return;
    }

    state.writer.screen = screen;
    const telas = el.writerEditorModal.querySelectorAll('[data-writer-screen]');
    telas.forEach((item) => {
        const ativa = item.dataset.writerScreen === screen;
        item.classList.toggle('is-active', ativa);
    });

    const tabLivroAtiva = screen === 'book';
    el.writerScreenBookBtn?.classList.toggle('is-active', tabLivroAtiva);
    el.writerScreenBookBtn?.setAttribute('aria-selected', tabLivroAtiva ? 'true' : 'false');
    el.writerScreenChaptersBtn?.classList.toggle('is-active', !tabLivroAtiva);
    el.writerScreenChaptersBtn?.setAttribute('aria-selected', tabLivroAtiva ? 'false' : 'true');
    sincronizarTabsCriacao(obterHistoriaAutoriaSelecionada());
    if (el.writerEditorMode) {
        el.writerEditorMode.textContent = tabLivroAtiva ? 'Tela 1 de 2: livro' : 'Tela 2 de 2: capítulos';
    }
    if (screen === 'chapters') {
        definirTelaCapitulos(state.writer.chapterScreen || 'list');
    }
}

function definirTelaCapitulos(screen) {
    if (!['list', 'editor'].includes(screen)) {
        return;
    }
    if (screen === 'editor' && !obterHistoriaAutoriaSelecionada()) {
        showToast('Crie o livro antes de escrever capítulos.', true);
        return;
    }
    const historia = obterHistoriaAutoriaSelecionada();
    if (screen === 'editor' && historia && el.capituloHistoriaId) {
        el.capituloHistoriaId.value = historia.id;
    }
    state.writer.chapterScreen = screen;

    const telas = document.querySelectorAll('[data-writer-chapter-screen]');
    telas.forEach((item) => {
        item.classList.toggle('is-active', item.dataset.writerChapterScreen === screen);
    });

    const ativaLista = screen === 'list';
    el.writerChapterListBtn?.classList.toggle('is-active', ativaLista);
    el.writerChapterListBtn?.setAttribute('aria-selected', ativaLista ? 'true' : 'false');
    el.writerChapterEditorBtn?.classList.toggle('is-active', !ativaLista);
    el.writerChapterEditorBtn?.setAttribute('aria-selected', ativaLista ? 'false' : 'true');
    sincronizarFormularioCapituloAutoria();
}

function atualizarPreviewCapa(src, mensagem = 'Adicionar capa do livro') {
    if (!el.storyCoverPreview) {
        return;
    }
    if (src) {
        el.storyCoverPreview.innerHTML = `<img src="${escapeAttribute(src)}" alt="Prévia da capa" class="writer-cover-preview-image">`;
        return;
    }
    el.storyCoverPreview.innerHTML = `
        ${escapeHtml(mensagem)}
        <div class="upload-hint">Clique para selecionar a imagem</div>
    `;
}

async function atualizarPreviewCapaSelecionada() {
    const coverFile = el.storyCoverInput?.files?.[0];
    if (!coverFile) {
        atualizarPreviewCapa(state.writer.autoCoverFromEpub);
        return;
    }
    state.writer.autoCoverFromEpub = null;
    const dataUrl = await lerArquivoComoDataURL(coverFile);
    atualizarPreviewCapa(dataUrl, 'Capa selecionada');
}

async function consultarMetadadosEpubSelecionado() {
    const epubFile = el.storyFileInput?.files?.[0];
    if (!epubFile) {
        state.writer.epubMetadata = null;
        if (el.storyEpubMetaHint) {
            el.storyEpubMetaHint.textContent = 'Se faltarem dados, o sistema usa os metadados do EPUB automaticamente.';
        }
        return;
    }

    const tiposPermitidosEpub = new Set(['application/epub+zip', 'application/octet-stream']);
    const nome = String(epubFile.name || '').toLowerCase();
    if (!tiposPermitidosEpub.has(epubFile.type) && !nome.endsWith('.epub')) {
        showToast('Formato de EPUB inválido. Use arquivo .epub.', true);
        return;
    }
    if (epubFile.size > 20 * 1024 * 1024) {
        showToast('EPUB muito grande. Use até 20MB.', true);
        return;
    }

    try {
        const dataUrl = await lerArquivoComoDataURL(epubFile);
        const response = await api('/me/autoria/epub-metadata', {
            method: 'POST',
            body: {epub: dataUrl},
        });
        const meta = response.metadados || {};
        state.writer.epubMetadata = meta;

        if (el.storyTitleInput && !el.storyTitleInput.value.trim() && meta.titulo) {
            el.storyTitleInput.value = meta.titulo;
        }
        if (el.storySynopsisInput && !el.storySynopsisInput.value.trim() && meta.sinopse) {
            el.storySynopsisInput.value = meta.sinopse;
        }
        if (el.storyGenreInput && !el.storyGenreInput.value.trim() && meta.genero) {
            el.storyGenreInput.value = meta.genero;
        }
        if (!el.storyCoverInput?.files?.length && meta.capa) {
            state.writer.autoCoverFromEpub = meta.capa;
            atualizarPreviewCapa(meta.capa, 'Capa do EPUB aplicada');
        }
        if (el.storyEpubMetaHint) {
            const totalCapitulos = Number(meta.total_capitulos || 0);
            el.storyEpubMetaHint.textContent = totalCapitulos
                ? `Metadados lidos com sucesso. ${totalCapitulos} capítulos detectados no EPUB.`
                : 'Metadados lidos. O EPUB não trouxe capítulos válidos.';
        }
        showToast(response.mensagem || 'Metadados do EPUB carregados.');
    } catch (error) {
        state.writer.epubMetadata = null;
        handleError(error);
    }
}

function renderPainelCapitulosAutoria(story) {
    const capitulos = story.capitulos || [];
    const bloqueadoPorEpub = ehLivroImportadoPorEpub(story);
    if (!el.writerModalChaptersList) {
        return;
    }
    el.writerModalChaptersList.innerHTML = `
        <div class="writer-chapter-list-head">
            <strong>${capitulos.length} capítulos</strong>
            ${bloqueadoPorEpub
                ? `<span class="chip">EPUB importado</span>`
                : `<button class="btn-primary" data-action="novo-capitulo-autoria" data-story-id="${escapeAttribute(story.id)}" type="button">+ Capítulo</button>`}
        </div>
        ${bloqueadoPorEpub ? `<p class="muted">Livro criado por EPUB: apenas edição dos capítulos existentes.</p>` : ''}
        ${capitulos.length ? capitulos.map((chapter) => `
            <article class="writer-chapter-item">
                <div>
                    <strong>${chapter.ordem}. ${escapeHtml(chapter.titulo)}</strong>
                    <p class="muted">${chapter.total_palavras || 0} palavras</p>
                </div>
                <div class="inline-actions">
                    <button class="btn-ghost" data-action="editar-capitulo-autoria" data-story-id="${escapeAttribute(story.id)}" data-chapter-id="${escapeAttribute(chapter.id)}" type="button">Editar</button>
                    <button class="btn-ghost" data-action="excluir-capitulo-autoria" data-story-id="${escapeAttribute(story.id)}" data-chapter-id="${escapeAttribute(chapter.id)}" type="button">Excluir</button>
                </div>
            </article>
        `).join('') : `<p class="placeholder">Este livro ainda não tem capítulos.</p>`}
    `;
}

function obterHistoriaAutoriaSelecionada() {
    const historias = state.minhasHistorias || [];
    if (!historias.length) {
        state.autoriaSelecionadaId = null;
        return null;
    }
    const selecionada = historias.find((story) => story.id === state.autoriaSelecionadaId);
    return selecionada || null;
}

function sincronizarTabsCriacao(historia) {
    const habilitarCapitulos = Boolean(historia);
    if (el.writerScreenChaptersBtn) {
        el.writerScreenChaptersBtn.classList.toggle('hidden', !habilitarCapitulos);
        el.writerScreenChaptersBtn.disabled = !habilitarCapitulos;
        el.writerScreenChaptersBtn.setAttribute('aria-selected', habilitarCapitulos && state.writer.screen === 'chapters' ? 'true' : 'false');
    }
    if (el.writerScreenBookBtn) {
        el.writerScreenBookBtn.setAttribute('aria-selected', state.writer.screen === 'book' ? 'true' : 'false');
    }
}

function abrirEditorAutoria(storyId = null, options = {}) {
    state.autoriaSelecionadaId = storyId || null;
    state.capituloEditandoId = null;
    const historia = obterHistoriaAutoriaSelecionada();
    const telaInicial = options.screen || (historia ? 'chapters' : 'book');
    state.writer.chapterScreen = options.chapterScreen || (historia ? 'list' : 'editor');

    if (el.formNovaHistoria) {
        el.formNovaHistoria.reset();
    }
    if (el.formNovoCapitulo) {
        el.formNovoCapitulo.reset();
    }
    if (el.storyCoverInput) {
        el.storyCoverInput.value = '';
    }
    if (el.storyFileInput) {
        el.storyFileInput.value = '';
    }
    state.writer.autoCoverFromEpub = null;
    state.writer.epubMetadata = null;
    atualizarPreviewCapa(historia?.capa || null);
    if (el.historiaEditId) {
        el.historiaEditId.value = historia?.id || '';
    }

    if (historia && el.formNovaHistoria) {
        if (el.formNovaHistoria.elements && el.formNovaHistoria.elements.titulo) {
            el.formNovaHistoria.elements.titulo.value = historia.titulo || '';
        }
        if (el.formNovaHistoria.elements && el.formNovaHistoria.elements.genero) {
            el.formNovaHistoria.elements.genero.value = historia.genero || '';
        }
        if (el.formNovaHistoria.elements && el.formNovaHistoria.elements.sinopse) {
            el.formNovaHistoria.elements.sinopse.value = historia.sinopse || '';
        }
    }
    if (el.storyEpubMetaHint) {
        el.storyEpubMetaHint.textContent = 'Se faltarem dados, o sistema usa os metadados do EPUB automaticamente.';
    }

    if (el.writerEditorTitle) {
        el.writerEditorTitle.textContent = historia ? historia.titulo : 'Novo livro';
    }
    if (el.writerEditorMode) {
        el.writerEditorMode.textContent = historia ? 'Tela 2 de 2: capítulos' : 'Tela 1 de 2: livro';
    }
    if (el.historiaSubmit) {
        el.historiaSubmit.textContent = historia ? 'Salvar dados do livro' : 'Criar livro';
    }

    if (historia) {
        renderPainelCapitulosAutoria(historia);
        if (el.formNovoCapitulo) {
            el.formNovoCapitulo.reset();
        }
        state.capituloEditandoId = null;
        if (el.capituloHistoriaId) {
            el.capituloHistoriaId.value = historia.id;
        }
        sincronizarFormularioCapituloAutoria();
    } else {
        renderPainelCapitulosAutoriaVazio();
        sincronizarFormularioCapituloAutoria();
    }

    el.writerEditorModal?.classList.remove('hidden');
    el.writerEditorModal?.setAttribute('aria-hidden', 'false');
    sincronizarTabsCriacao(historia);
    definirTelaEditorAutoria(telaInicial);
    if (state.writer.screen === 'book') {
        el.formNovaHistoria?.elements?.titulo?.focus();
    }
    renderEscrever();
}

function fecharEditorAutoria() {
    el.writerEditorModal?.classList.add('hidden');
    el.writerEditorModal?.setAttribute('aria-hidden', 'true');
    state.capituloEditandoId = null;
    state.writer.autoCoverFromEpub = null;
    state.writer.epubMetadata = null;
    state.writer.screen = 'book';
    state.writer.chapterScreen = 'list';
    renderEscrever();
}

function renderPainelCapitulosAutoriaVazio() {
    if (el.writerModalChaptersList) {
        el.writerModalChaptersList.innerHTML = `<p class="placeholder">Crie o livro na tela "Livro" para liberar capítulos.</p>`;
    }
}

function sincronizarFormularioCapituloAutoria() {
    const historia = obterHistoriaAutoriaSelecionada();
    const editando = Boolean(state.capituloEditandoId);
    const bloqueadoPorEpub = Boolean(historia && ehLivroImportadoPorEpub(historia) && !editando);
    const tituloInput = el.formNovoCapitulo?.elements?.titulo;
    const conteudoInput = el.formNovoCapitulo?.elements?.conteudo;

    if (el.capituloHistoriaId) {
        el.capituloHistoriaId.disabled = !historia;
        if (historia) {
            el.capituloHistoriaId.value = historia.id;
        }
    }
    if (el.capituloEditId) {
        el.capituloEditId.value = state.capituloEditandoId || '';
    }
    if (el.capituloFormTitle) {
        el.capituloFormTitle.textContent = historia
            ? (editando ? 'Editar capítulo' : `Capítulos de ${historia.titulo}`)
            : 'Capítulos';
    }
    if (el.capituloFormHint) {
        if (!historia) {
            el.capituloFormHint.textContent = 'Crie o livro na tela "Livro" para liberar os capítulos.';
        } else if (bloqueadoPorEpub) {
            el.capituloFormHint.textContent = 'Este livro veio de EPUB: você pode editar capítulos existentes, mas não criar novos.';
        } else if (editando) {
            el.capituloFormHint.textContent = 'Altere o título ou conteúdo e salve.';
        } else {
            el.capituloFormHint.textContent = 'Adicione um capítulo novo ou escolha um existente para editar.';
        }
    }
    if (el.capituloSubmit) {
        el.capituloSubmit.textContent = editando ? 'Salvar capítulo' : 'Adicionar capítulo';
        el.capituloSubmit.disabled = !historia || bloqueadoPorEpub;
    }
    if (el.capituloBackList) {
        el.capituloBackList.disabled = !historia;
    }
    if (el.capituloEditCancel) {
        el.capituloEditCancel.classList.toggle('hidden', !editando);
    }
    if (tituloInput) {
        tituloInput.disabled = !historia || bloqueadoPorEpub;
    }
    if (conteudoInput) {
        conteudoInput.disabled = !historia || bloqueadoPorEpub;
    }
}

function prepararNovoCapitulo(storyId, rolar = false) {
    const historia = (state.minhasHistorias || []).find((story) => story.id === storyId);
    if (historia && ehLivroImportadoPorEpub(historia)) {
        showToast('Livro importado por EPUB permite apenas edição dos capítulos existentes.', true);
        return;
    }
    state.autoriaSelecionadaId = storyId;
    state.capituloEditandoId = null;
    if (el.formNovoCapitulo) {
        el.formNovoCapitulo.reset();
    }
    if (el.capituloEditId) {
        el.capituloEditId.value = '';
    }
    if (el.capituloHistoriaId) {
        el.capituloHistoriaId.value = storyId;
    }
    definirTelaCapitulos('editor');
    sincronizarFormularioCapituloAutoria();
    if (rolar) {
        el.formNovoCapitulo?.scrollIntoView({behavior: 'smooth', block: 'center'});
        el.formNovoCapitulo?.elements?.titulo?.focus();
    }
}

function preencherEdicaoCapitulo(storyId, chapterId) {
    const historia = (state.minhasHistorias || []).find((story) => story.id === storyId);
    const capitulo = historia?.capitulos?.find((chapter) => chapter.id === chapterId);
    if (!historia || !capitulo || !el.formNovoCapitulo) {
        showToast('Não foi possível carregar o capítulo para edição.', true);
        return;
    }

    state.autoriaSelecionadaId = storyId;
    state.capituloEditandoId = chapterId;
    el.formNovoCapitulo.elements.historia_id.value = storyId;
    el.formNovoCapitulo.elements.capitulo_id.value = chapterId;
    el.formNovoCapitulo.elements.titulo.value = capitulo.titulo || '';
    el.formNovoCapitulo.elements.conteudo.value = capitulo.conteudo || '';
    definirTelaEditorAutoria('chapters');
    definirTelaCapitulos('editor');
    sincronizarFormularioCapituloAutoria();
    el.formNovoCapitulo.scrollIntoView({behavior: 'smooth', block: 'center'});
    el.formNovoCapitulo.elements.titulo.focus();
}

function limparEdicaoCapitulo(rolar = false) {
    const storyId = state.autoriaSelecionadaId || el.capituloHistoriaId?.value || '';
    state.capituloEditandoId = null;
    if (el.formNovoCapitulo) {
        el.formNovoCapitulo.reset();
    }
    if (el.capituloEditId) {
        el.capituloEditId.value = '';
    }
    if (el.capituloHistoriaId && storyId) {
        el.capituloHistoriaId.value = storyId;
    }
    definirTelaCapitulos('list');
    sincronizarFormularioCapituloAutoria();
    if (rolar) {
        el.writerModalChaptersList?.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    }
}

function handleChapterFormatActionClick(event) {
    const button = event.target.closest('[data-action="formatar-capitulo"]');
    if (!button) {
        return;
    }
    const format = String(button.dataset.format || '');
    aplicarFormatacaoNoEditorCapitulo(format);
}

function aplicarFormatacaoNoEditorCapitulo(format) {
    const textarea = el.formNovoCapitulo?.elements?.conteudo;
    if (!textarea || textarea.disabled) {
        return;
    }

    const inicio = Number(textarea.selectionStart || 0);
    const fim = Number(textarea.selectionEnd || 0);
    const selecionado = textarea.value.slice(inicio, fim);

    const formatos = {
        bold: ['**', '**'],
        italic: ['*', '*'],
        subtitle: ['## ', ''],
        quote: ['> ', ''],
        list: ['- ', ''],
    };
    const alvo = formatos[format];
    if (!alvo) {
        return;
    }

    const [prefixo, sufixo] = alvo;
    const textoBase = selecionado || 'texto';
    const substituto = `${prefixo}${textoBase}${sufixo}`;
    textarea.setRangeText(substituto, inicio, fim, 'end');
    const cursorInicio = inicio + prefixo.length;
    const cursorFim = cursorInicio + textoBase.length;
    textarea.focus();
    textarea.setSelectionRange(cursorInicio, cursorFim);
}

async function excluirCapituloAutoria(storyId, chapterId) {
    if (!storyId || !chapterId) {
        showToast('Capítulo inválido para exclusão.', true);
        return;
    }
    const confirmar = confirm('Deseja realmente excluir este capítulo?');
    if (!confirmar) {
        return;
    }

    const response = await api(
        `/me/autoria/historias/${encodeURIComponent(storyId)}/capitulos/${encodeURIComponent(chapterId)}`,
        {method: 'DELETE'},
    );
    showToast(response.mensagem || 'Capítulo excluído com sucesso.');
    if (state.capituloEditandoId === chapterId) {
        state.capituloEditandoId = null;
    }
    state.autoriaSelecionadaId = storyId;
    await carregarAutoria();
    renderEscrever();
    abrirEditorAutoria(storyId, {screen: 'chapters', chapterScreen: 'list'});
}

function renderVoce() {
    if (!state.painel) {
        return;
    }
    const leitura = state.painel.leitura || {};
    const autoria = state.painel.autoria || {};

    if (el.voceStats) {
        const marcacoes = leitura.marcacoes || [];
        el.voceStats.innerHTML = `
            <h3>Seu resumo</h3>
            <p class="muted">${escapeHtml(leitura.leitor?.painel || '')}</p>
            <div class="summary-cards compact">
                <div class="summary-item"><span>Leituras ativas</span><strong>${(leitura.progresso || []).length}</strong></div>
                <div class="summary-item"><span>Na biblioteca</span><strong>${leitura.biblioteca?.total || 0}</strong></div>
                <div class="summary-item"><span>Publicadas</span><strong>${autoria.total || 0}</strong></div>
            </div>
            <div class="profile-quotes">
                <h4>Citações marcadas</h4>
                ${marcacoes.length ? marcacoes.slice(0, 6).map((item) => {
                    const capa = item.historia_capa || item.capa || item.historia?.capa || '';
                    const data = item.data || item.data_marcacao || '';
                    return `
                    <article class="mark-feed-item">
                        <div class="mark-thumb">${capa ? `<img src="${escapeAttribute(capa)}" alt="capa"/>` : `<div class="cover cover-placeholder small"></div>`}</div>
                        <div>
                            <div class="mark-head">
                                <strong>${escapeHtml(item.usuario || 'Você')}</strong>
                                <small class="muted">${escapeHtml(data)}</small>
                            </div>
                            <p>“${escapeHtml(item.trecho)}”</p>
                            <div class="inline-actions">
                                <button class="btn-ghost" data-action="comentar-marcacao" data-marcacao-id="${escapeAttribute(item.id || '')}" type="button">Comentar</button>
                            </div>
                        </div>
                    </article>`;
                }).join('') : `<p class="placeholder">As partes que você marcar aparecerão aqui.</p>`}
            </div>
        `;
    }

    if (el.voceProgresso) {
        const progresso = leitura.progresso || [];
        el.voceProgresso.innerHTML = progresso.length
            ? progresso.map((item) => `
                <article class="story-row">
                    <div>
                        <strong>${escapeHtml(item.historia.titulo)}</strong>
                        <p class="muted">${escapeHtml(item.capitulo_titulo || 'Capítulo inicial')}</p>
                        <div class="progress"><span style="width:${item.percentual}%"></span></div>
                    </div>
                    <button class="btn-ghost" data-action="abrir-capitulo" data-story-id="${item.historia.id}" data-chapter-id="${item.capitulo_id || item.historia.capitulo_inicial_id || ''}" type="button">Continuar</button>
                </article>
            `).join('')
            : `<p class="placeholder">Nenhuma leitura ativa no momento.</p>`;
    }

    if (el.voceAutoria) {
        const historias = autoria.historias || [];
        el.voceAutoria.innerHTML = historias.length
            ? historias.map((story) => `
                <article class="story-row">
                    <div>
                        <strong>${escapeHtml(story.titulo)}</strong>
                        <p class="muted">${escapeHtml(story.sinopse)}</p>
                    </div>
                    <button class="btn-ghost" data-action="abrir-historia" data-story-id="${story.id}" type="button">Ler</button>
                </article>
            `).join('')
            : `<p class="placeholder">Você ainda não publicou histórias.</p>`;
    }
}

function sentimentoParaNota(sentimento) {
    const valor = String(sentimento || '').trim();
    if (valor === 'amei') {
        return 5;
    }
    if (valor === 'gostei') {
        return 4;
    }
    if (valor === 'nao_gostei') {
        return 1;
    }
    return 0;
}

function notaParaSentimento(nota) {
    const valor = Number(nota || 0);
    if (valor >= 5) {
        return 'amei';
    }
    if (valor >= 3) {
        return 'gostei';
    }
    if (valor > 0) {
        return 'nao_gostei';
    }
    return '';
}

function renderStoryCard(story) {
    const cardClass = state.page === 'inicio' ? 'story-home-card' : '';
    const sentimentoSelecionado = notaParaSentimento(story.minha_avaliacao);
    return `
        <article class="writer-book-card ${cardClass} story-discovery-card ${story.id === state.autoriaSelecionadaId ? 'is-selected' : ''}" data-story-id="${escapeAttribute(story.id)}">
            <div class="writer-book-cover-wrap">
                <button class="writer-book-cover" data-action="abrir-historia" data-story-id="${escapeAttribute(story.id)}" type="button" aria-label="Abrir ${escapeAttribute(story.titulo)}">
                    ${renderStoryCover(story)}
                </button>
                <div class="story-hover-actions" aria-label="Ações rápidas">
                    <button class="story-quick-btn" data-action="salvar-historia" data-story-id="${escapeAttribute(story.id)}" data-categoria="favoritos" type="button">Favoritar</button>
                    <button class="story-quick-btn ${sentimentoSelecionado === 'amei' ? 'is-active' : ''}" data-action="avaliar-sentimento" data-story-id="${escapeAttribute(story.id)}" data-sentimento-voto="amei" type="button">Amei</button>
                    <button class="story-quick-btn ${sentimentoSelecionado === 'gostei' ? 'is-active' : ''}" data-action="avaliar-sentimento" data-story-id="${escapeAttribute(story.id)}" data-sentimento-voto="gostei" type="button">Gostei</button>
                    <button class="story-quick-btn ${sentimentoSelecionado === 'nao_gostei' ? 'is-active' : ''}" data-action="avaliar-sentimento" data-story-id="${escapeAttribute(story.id)}" data-sentimento-voto="nao_gostei" type="button">Não gostei</button>
                </div>
            </div>
            <div class="writer-book-info">
                <strong>${escapeHtml(story.titulo)}</strong>
                <span>${story.total_capitulos} capítulos · ${escapeHtml(story.genero || 'Geral')}</span>
                <div class="rating-badge" aria-hidden="false" role="button" tabindex="0" data-action="abrir-historia" data-story-id="${escapeAttribute(story.id)}">
                    <span class="rating-avg">${Number(story.media_avaliacoes || 0).toFixed(1)}</span>
                    <span class="rating-count">(${Number(story.total_avaliacoes || 0)})</span>
                </div>
            </div>
        </article>
    `;
}

function renderStoryCover(story) {
    if (story?.capa) {
        return `<img class="cover cover-image" src="${escapeAttribute(story.capa)}" alt="Capa de ${escapeAttribute(story.titulo || 'história')}">`;
    }
    return `<div class="cover cover-placeholder" style="background: linear-gradient(135deg, ${story.tema?.accent || '#6387f7'}, #202734);"></div>`;
}

async function recarregarHistoriasComTratamento() {
    try {
        await carregarCatalogo();
        renderHistorias();
        await selecionarHistoriaInicial();
    } catch (error) {
        handleError(error);
    }
}

function obterHistoriaPorIdLocal(storyId) {
    const colecoes = [
        ...(state.catalogo || []),
        ...(state.minhasHistorias || []),
        ...((state.painel?.leitura?.progresso || []).map((item) => item.historia).filter(Boolean)),
        ...((state.painel?.leitura?.recomendacoes || []).filter(Boolean)),
    ];

    if (state.historiaDetalhe) {
        colecoes.push(state.historiaDetalhe);
    }

    const categorias = state.biblioteca?.categorias || {};
    for (const lista of Object.values(categorias)) {
        if (Array.isArray(lista)) {
            colecoes.push(...lista);
        }
    }

    return colecoes.find((story) => story && story.id === storyId) || null;
}

async function abrirHistoriaNoLeitor(storyId) {
    const historiaLocal = obterHistoriaPorIdLocal(storyId);
    let chapterId = historiaLocal?.progresso_leitor?.capitulo_id || historiaLocal?.capitulo_inicial_id;

    if (!chapterId) {
        const detalhe = await api(`/me/historias/${encodeURIComponent(storyId)}`);
        const historia = detalhe.historia;
        chapterId = historia?.progresso_leitor?.capitulo_id
            || historia?.capitulo_inicial_id
            || historia?.capitulos?.[0]?.id;
        if (state.page === 'historias') {
            state.historiaDetalhe = historia;
            renderDetalheHistoria();
        }
    }

    if (!chapterId) {
        showToast('Esta história ainda não possui capítulo para leitura.', true);
        return;
    }

    await abrirCapitulo(storyId, chapterId);
}

async function handleStoryActionClick(event) {
    // hover effects are handled by mouseover/mouseout listeners; clicks should be handled below

    const button = event.target.closest('[data-action]');

    if (!button) {
        return;
    }
    const action = button.dataset.action;
    const storyId = button.dataset.storyId;

    try {
        if (action === 'filtrar-genero') {
            state.filtros.genero = button.dataset.genero || '';
            state.filtros.q = '';
            sincronizarInputsBusca();
            await carregarCatalogo();
            if (state.page === 'inicio') {
                renderInicio();
            }
            return;
        }

        if (action === 'nova-historia') {
            abrirEditorAutoria(null, {screen: 'book'});
            return;
        }

        if (action === 'abrir-historia') {
            await abrirHistoriaNoLeitor(storyId);
            return;
        }

        if (action === 'selecionar-historia') {
            if (state.page !== 'historias') {
                window.location.href = `/app/historias?story=${encodeURIComponent(storyId)}`;
                return;
            }
            await selecionarHistoria(storyId);
            return;
        }

        if (action === 'selecionar-escrita') {
            abrirEditorAutoria(storyId, {screen: 'chapters'});
            return;
        }

        if (action === 'novo-capitulo-autoria') {
            prepararNovoCapitulo(storyId, true);
            showToast('Pronto para adicionar um novo capítulo.');
            return;
        }

        if (action === 'editar-capitulo-autoria') {
            state.autoriaSelecionadaId = storyId;
            preencherEdicaoCapitulo(storyId, button.dataset.chapterId);
            return;
        }

        if (action === 'excluir-capitulo-autoria') {
            await excluirCapituloAutoria(storyId, button.dataset.chapterId);
            return;
        }

        if (action === 'salvar-historia') {
            await salvarHistoria(storyId, button.dataset.categoria || 'lendo');
            return;
        }

        if (action === 'avaliar-historia') {
            await avaliarHistoria(storyId, Number(button.dataset.nota || 0));
            return;
        }

        if (action === 'avaliar-sentimento') {
            const nota = sentimentoParaNota(button.dataset.sentimentoVoto);
            if (!nota) {
                showToast('Avaliação inválida.', true);
                return;
            }
            await avaliarHistoria(storyId, nota);
            return;
        }

        if (action === 'abrir-capitulo') {
            const chapterId = button.dataset.chapterId;
            if (!chapterId) {
                showToast('Esta história ainda não possui capítulo para leitura.', true);
                return;
            }
            await abrirCapitulo(storyId, chapterId);
            return;
        }
    } catch (error) {
        handleError(error);
    }
}

async function publicarHistoria(event) {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(el.formNovaHistoria).entries());
    try {
        const editando = Boolean(payload.historia_id);
        const coverFile = el.storyCoverInput?.files?.[0];
        if (coverFile) {
            const tiposPermitidos = new Set(['image/png', 'image/jpeg', 'image/webp']);
            if (!tiposPermitidos.has(coverFile.type)) {
                showToast('Formato de capa inválido. Use PNG, JPG ou WEBP.', true);
                return;
            }
            if (coverFile.size > 2 * 1024 * 1024) {
                showToast('Capa muito grande. Use até 2MB.', true);
                return;
            }
            payload.capa = await lerArquivoComoDataURL(coverFile);
        } else if (!editando && state.writer.autoCoverFromEpub) {
            payload.capa = state.writer.autoCoverFromEpub;
        }
        // suporte a EPUB
        const epubFile = el.storyFileInput?.files?.[0];
        if (epubFile) {
            const tiposPermitidosEpub = new Set(['application/epub+zip', 'application/octet-stream']);
            const name = String(epubFile.name || '').toLowerCase();
            if (!tiposPermitidosEpub.has(epubFile.type) && !name.endsWith('.epub')) {
                showToast('Formato de arquivo EPUB inválido. Use .epub.', true);
                return;
            }
            if (epubFile.size > 20 * 1024 * 1024) {
                showToast('EPUB muito grande. Use até 20MB.', true);
                return;
            }
            payload.epub = await lerArquivoComoDataURL(epubFile);
        }

        const endpoint = editando
            ? `/me/autoria/historias/${encodeURIComponent(payload.historia_id)}`
            : '/me/autoria/historias';
        const response = await api(endpoint, {method: editando ? 'PUT' : 'POST', body: payload});
        const criadoViaEpub = Boolean(response.tem_epub || payload.epub);
        el.formNovaHistoria.reset();
        if (el.storyCoverInput) {
            el.storyCoverInput.value = '';
        }
        if (el.storyFileInput) {
            el.storyFileInput.value = '';
        }
        state.writer.autoCoverFromEpub = null;
        state.writer.epubMetadata = null;
        atualizarPreviewCapa(null);
        await carregarAutoria();
        state.autoriaSelecionadaId = response.historia?.id || response.id || payload.historia_id || null;
        state.capituloEditandoId = null;
        renderEscrever();
        abrirEditorAutoria(state.autoriaSelecionadaId, {screen: 'chapters'});
        if (editando) {
            showToast(response.mensagem || 'Livro atualizado com sucesso.');
        } else if (criadoViaEpub) {
            showToast('Livro criado por EPUB. Capítulos importados e liberados apenas para edição.');
        } else {
            showToast('Livro criado. Agora vá para a tela de capítulos para começar a escrever.');
        }
    } catch (error) {
        handleError(error);
    }
}

async function publicarCapitulo(event) {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(el.formNovoCapitulo).entries());
    if (!payload.historia_id) {
        showToast('Selecione uma história antes de adicionar capítulo.', true);
        return;
    }
    try {
        const editando = Boolean(payload.capitulo_id);
        const historiaSelecionada = (state.minhasHistorias || []).find((story) => story.id === payload.historia_id);
        if (!editando && historiaSelecionada && ehLivroImportadoPorEpub(historiaSelecionada)) {
            showToast('Livro importado por EPUB permite apenas edição dos capítulos existentes.', true);
            return;
        }
        const endpoint = editando
            ? `/me/autoria/historias/${encodeURIComponent(payload.historia_id)}/capitulos/${encodeURIComponent(payload.capitulo_id)}`
            : `/me/autoria/historias/${encodeURIComponent(payload.historia_id)}/capitulos`;
        const response = await api(endpoint, {
            method: editando ? 'PUT' : 'POST',
            body: {
                titulo: payload.titulo,
                conteudo: payload.conteudo,
            },
        });
        showToast(response.mensagem || (editando ? 'Capítulo atualizado com sucesso.' : 'Capítulo adicionado com sucesso.'));
        state.autoriaSelecionadaId = payload.historia_id;
        state.capituloEditandoId = null;
        el.formNovoCapitulo.reset();
        await carregarAutoria();
        renderEscrever();
        abrirEditorAutoria(state.autoriaSelecionadaId, {screen: 'chapters', chapterScreen: 'list'});
    } catch (error) {
        handleError(error);
    }
}

async function salvarHistoria(storyId, categoria) {
    const response = await api('/me/biblioteca', {
        method: 'POST',
        body: {
            historia_id: storyId,
            categoria: normalizarCategoria(categoria),
        },
    });
    showToast(response.mensagem || 'História salva na biblioteca.');
    await Promise.all([carregarPainel(), carregarBiblioteca()]);
    if (state.page === 'inicio') {
        renderInicio();
    } else if (state.page === 'biblioteca') {
        renderBiblioteca();
    } else if (state.page === 'voce') {
        renderVoce();
    }
}

async function avaliarHistoria(storyId, nota) {
    if (!nota || nota < 1 || nota > 5) {
        showToast('Nota inválida.', true);
        return;
    }
    const response = await api('/me/avaliar', {
        method: 'POST',
        body: {historia_id: storyId, nota},
    });
    showToast(response.mensagem || 'Avaliação registrada.');

    // Update only the affected story in state to avoid full reload
    try {
        const media = Number(response.media_atual || 0);
        const total = Number(response.total_avaliacoes || 0);

        // update catalog item
        const idx = state.catalogo.findIndex((s) => s.id === storyId);
        if (idx >= 0) {
            state.catalogo[idx].media_avaliacoes = media;
            state.catalogo[idx].total_avaliacoes = total;
            state.catalogo[idx].minha_avaliacao = nota;
        }

        // animate micro-feedback badge on the card if present
        try {
            const cardBadge = document.querySelector(`.writer-book-card[data-story-id="${storyId}"] .rating-badge`);
            if (cardBadge) {
                cardBadge.classList.remove('pulse');
                // reflow to restart animation
                // eslint-disable-next-line no-unused-expressions
                cardBadge.offsetWidth;
                cardBadge.classList.add('pulse');
                setTimeout(() => cardBadge.classList.remove('pulse'), 700);
                // update numbers in the badge
                const avgEl = cardBadge.querySelector('.rating-avg');
                const cntEl = cardBadge.querySelector('.rating-count');
                if (avgEl) avgEl.textContent = media.toFixed(1);
                if (cntEl) cntEl.textContent = `(${total})`;
            }
        } catch (e) {
            // ignore animation errors
        }

        // update detail view if open
        if (state.historiaDetalhe && state.historiaDetalhe.id === storyId) {
            state.historiaDetalhe.media_avaliacoes = media;
            state.historiaDetalhe.total_avaliacoes = total;
            state.historiaDetalhe.minha_avaliacao = nota;
            atualizarSeletorAvaliacao(nota, {storyId});
            renderDetalheHistoria();
        }

        // refresh lists that show média
        if (state.page === 'historias') {
            renderHistorias();
        } else if (state.page === 'inicio') {
            renderInicio();
        }
    } catch (e) {
        // fallback: reload catalog and detail
        await carregarCatalogo();
        try { await selecionarHistoria(storyId); } catch (err) {}
        if (state.page === 'historias') renderHistorias(); else renderDetalheHistoria();
    }
}

async function abrirCapitulo(storyId, chapterId, options = {}) {
    await registrarTempoLeituraAtual();
    const response = await api(`/me/historias/${encodeURIComponent(storyId)}/capitulos/${encodeURIComponent(chapterId)}`);
    const paginaInicial = options.paginaInicial || 'primeira';
    state.capituloAtivo = response;
    renderModalLeitura(paginaInicial);
    iniciarSessaoLeitura();
    el.readerModal?.classList.remove('hidden');
    el.readerModal?.setAttribute('aria-hidden', 'false');
}

function renderModalLeitura(paginaInicial = 'manter') {
    if (!state.capituloAtivo) {
        return;
    }
    const {historia, capitulo} = state.capituloAtivo;
    definirPainelLeitorInicial();
    if (el.readerStoryName) {
        el.readerStoryName.textContent = `${historia.titulo} · ${historia.autor || 'Autor'}`;
    }
    if (el.readerBookTitleTop) {
        el.readerBookTitleTop.textContent = historia.titulo || '';
    }
    if (el.readerChapterTitle) {
        el.readerChapterTitle.textContent = capitulo.titulo;
    }
    if (el.readerMeta) {
        el.readerMeta.textContent = `Capítulo ${capitulo.ordem}: ${capitulo.titulo}`;
    }
    renderReaderChapterSelect();
    sincronizarControlesLeitor();
    aplicarPaginacaoCapitulo(paginaInicial);
    if (el.readerCommentsCount) {
        el.readerCommentsCount.textContent = String((capitulo.comentarios_recentes || []).length);
    }
    if (el.readerComments) {
        el.readerComments.innerHTML = (capitulo.comentarios_recentes || []).length
            ? capitulo.comentarios_recentes.map((comment) => `
                <article class="comment-item">
                    <strong style="color:${escapeAttribute(corNomeUsuario(comment.usuario))};">${escapeHtml(comment.usuario)}</strong>
                    <p class="muted">${escapeHtml(comment.conteudo)}</p>
                    ${comment.usuario_id === state.user?.leitor_id ? `
                        <div class="inline-actions">
                            <button class="btn-ghost" data-action="edit-comment" data-comment-id="${comment.id}" type="button">Editar</button>
                            <button class="btn-ghost" data-action="delete-comment" data-comment-id="${comment.id}" type="button">Excluir</button>
                        </div>
                    ` : ''}
                </article>
            `).join('')
            : `<p class="placeholder">Seja o primeiro comentário neste capítulo.</p>`;
    }

    renderMarcacoesLeitor();
    // remover exibição de sessões de leitura (apenas manter tempo estimado para capítulo)
    if (el.readerSessionsList) el.readerSessionsList.innerHTML = '';
    if (el.readerSessionsCount) el.readerSessionsCount.textContent = '0';
    atualizarTempoPrevisto();
    atualizarTempoLeituraUI();
}

function renderReaderChapterSelect() {
    if (!state.capituloAtivo) {
        return;
    }

    const capitulos = state.capituloAtivo.historia?.capitulos || [];
    const capituloAtualId = state.capituloAtivo.capitulo?.id;
    if (el.readerChapterSelect) {
        el.readerChapterSelect.innerHTML = capitulos.length
            ? capitulos.map((chapter) => `
                <option value="${escapeAttribute(chapter.id)}" ${chapter.id === capituloAtualId ? 'selected' : ''}>
                    ${chapter.ordem}. ${escapeHtml(chapter.titulo)}
                </option>
            `).join('')
            : `<option value="">Sem capítulos</option>`;
        el.readerChapterSelect.disabled = !capitulos.length;
    }
    if (el.readerTocList) {
        el.readerTocList.innerHTML = '';
    }
}

function alternarPainelLeitor(panel) {
    if (!el.readerSidePanel || !['toc', 'settings'].includes(panel)) {
        return;
    }
    el.readerSidePanel.dataset.panel = panel;
    el.readerSidePanel.classList.remove('is-collapsed');
    el.readerShowToc?.classList.toggle('is-active', panel === 'toc');
    el.readerShowSettings?.classList.toggle('is-active', panel === 'settings');
}

function definirPainelLeitorInicial() {
    if (!el.readerSidePanel) {
        return;
    }
    el.readerSidePanel.dataset.panel = 'settings';
    el.readerSidePanel.classList.add('is-collapsed');
    el.readerShowToc?.classList.remove('is-active');
    el.readerShowSettings?.classList.remove('is-active');
}

function aplicarPaginacaoCapitulo(paginaInicial = 'manter') {
    if (!state.capituloAtivo) {
        return;
    }

    const conteudo = state.capituloAtivo.capitulo?.conteudo || '';
    const paginasNoSpread = leitorExibeDuasPaginas() ? 2 : 1;
    const paginasIndividuais = paginarTextoPorLayout(conteudo);
    state.readerPagination.pages = agruparPaginasEmSpreads(paginasIndividuais, paginasNoSpread);
    if (!state.readerPagination.pages.length) {
        state.readerPagination.pages = [`${READER_SPREAD_SEPARATOR}`];
    }

    const totalPalavras = extrairPalavrasTexto(conteudo).length;
    const totalSpreads = Math.max(1, state.readerPagination.pages.length);
    state.readerPagination.wordsPerSpread = Math.max(20, Math.round(totalPalavras / totalSpreads));
    state.readerPagination.wordsPerPage = Math.max(12, Math.round(state.readerPagination.wordsPerSpread / paginasNoSpread));

    if (paginaInicial === 'primeira') {
        state.readerPagination.currentPage = 0;
    } else if (paginaInicial === 'ultima') {
        state.readerPagination.currentPage = state.readerPagination.pages.length - 1;
    } else {
        state.readerPagination.currentPage = Math.min(
            state.readerPagination.currentPage,
            state.readerPagination.pages.length - 1,
        );
    }

    renderPaginaAtualLeitura();
}

function leitorExibeDuasPaginas() {
    return !window.matchMedia('(max-width: 980px)').matches;
}

function obterFamiliaFonteLeitor(chaveFonte) {
    if (chaveFonte === 'georgia') {
        return 'Georgia, "Times New Roman", serif';
    }
    if (chaveFonte === 'book') {
        return '"Baskerville", "Book Antiqua", "Garamond", serif';
    }
    if (chaveFonte === 'sans_clean') {
        return '"Avenir Next", "Segoe UI", "Helvetica Neue", Arial, sans-serif';
    }
    return '"Iowan Old Style", "Palatino Linotype", Georgia, serif';
}

function extrairPalavrasTexto(texto) {
    return String(texto || '')
        .trim()
        .split(/\s+/)
        .filter(Boolean);
}

function obterMetricasPaginaLeitor() {
    const stage = el.readerContent;
    if (!stage) {
        return null;
    }
    const larguraDisponivel = Math.max(320, Number(stage.clientWidth || 0) || Math.round(window.innerWidth * 0.72));
    const alturaDisponivel = Math.max(260, Number(stage.clientHeight || 0) || Math.round(window.innerHeight * 0.62));
    const paginasNoSpread = leitorExibeDuasPaginas() ? 2 : 1;
    const gap = paginasNoSpread === 2
        ? Math.max(12, Math.min(28, Math.round(larguraDisponivel * 0.022)))
        : 0;
    const larguraSpreadUtil = Math.max(200, larguraDisponivel - 24 - gap);
    const alturaSpreadUtil = Math.max(220, alturaDisponivel - 22);
    const larguraPagina = Math.max(170, Math.floor(larguraSpreadUtil / paginasNoSpread));
    const alturaPagina = Math.max(180, Math.floor(alturaSpreadUtil));

    return {
        larguraPagina,
        alturaPagina,
    };
}

function calcularPalavrasPorPagina() {
    const metricas = obterMetricasPaginaLeitor();
    const tamanhoFonte = Math.max(16, Number(state.readerPrefs.fontSize || 24));
    const alturaLinha = tamanhoFonte * 1.55;
    const larguraPagina = Math.max(170, metricas?.larguraPagina || 300);
    const alturaPagina = Math.max(180, metricas?.alturaPagina || 420);
    const linhasPorPagina = Math.max(5, Math.floor(alturaPagina / alturaLinha) - 1);
    const caracteresPorLinha = Math.max(16, Math.floor(larguraPagina / (tamanhoFonte * 0.52)));
    const palavrasPorLinha = caracteresPorLinha / 5.2;
    return Math.max(24, Math.min(280, Math.floor(linhasPorPagina * palavrasPorLinha)));
}

function paginarTextoPorPalavras(conteudo, palavrasPorPagina) {
    const palavras = extrairPalavrasTexto(conteudo);

    if (!palavras.length) {
        return [];
    }

    const paginas = [];
    for (let index = 0; index < palavras.length; index += palavrasPorPagina) {
        paginas.push(palavras.slice(index, index + palavrasPorPagina).join(' '));
    }
    return paginas;
}

function obterMedidorPagina() {
    if (state.readerPagination.measurerEl && document.body.contains(state.readerPagination.measurerEl)) {
        return state.readerPagination.measurerEl;
    }

    const medidor = document.createElement('article');
    medidor.className = 'reader-page reader-page-measurer';
    medidor.style.position = 'fixed';
    medidor.style.left = '-10000px';
    medidor.style.top = '0';
    medidor.style.zIndex = '-1';
    medidor.style.visibility = 'hidden';
    medidor.style.pointerEvents = 'none';
    medidor.style.overflow = 'hidden';
    medidor.style.contain = 'strict';
    document.body.appendChild(medidor);
    state.readerPagination.measurerEl = medidor;
    return medidor;
}

function atualizarMedidorPagina(medidor) {
    const metricas = obterMetricasPaginaLeitor();
    medidor.style.width = `${metricas?.larguraPagina || 300}px`;
    medidor.style.height = `${metricas?.alturaPagina || 420}px`;
    medidor.style.fontSize = `${Math.max(16, Number(state.readerPrefs.fontSize || 24))}px`;
    medidor.style.fontFamily = obterFamiliaFonteLeitor(state.readerPrefs.fontFamily);
    medidor.style.lineHeight = '1.55';
}

function trechoCabeNoMedidor(medidor, texto, incluirTitulo = false) {
    const titulo = escapeHtml(state.capituloAtivo?.capitulo?.titulo || 'Capítulo');
    medidor.innerHTML = `
        ${incluirTitulo ? `<h3>${titulo}</h3>` : ''}
        ${texto ? `<p class="reader-page-text">${escapeHtml(texto)}</p>` : ''}
    `;
    return medidor.scrollHeight <= medidor.clientHeight + 1;
}

function medirPalavrasQueCabem(palavras, inicio, medidor, incluirTitulo = false) {
    const restante = palavras.length - inicio;
    if (restante <= 0) {
        return 0;
    }

    let baixo = 1;
    let alto = restante;
    let melhor = 0;

    while (baixo <= alto) {
        const meio = Math.floor((baixo + alto) / 2);
        const texto = palavras.slice(inicio, inicio + meio).join(' ');
        if (trechoCabeNoMedidor(medidor, texto, incluirTitulo)) {
            melhor = meio;
            baixo = meio + 1;
        } else {
            alto = meio - 1;
        }
    }

    return Math.max(1, melhor);
}

function paginarTextoPorLayout(conteudo) {
    const palavras = extrairPalavrasTexto(conteudo);
    if (!palavras.length) {
        return [];
    }

    const medidor = obterMedidorPagina();
    atualizarMedidorPagina(medidor);
    const paginas = [];
    let indice = 0;
    let primeiraPagina = true;

    while (indice < palavras.length) {
        const quantidade = medirPalavrasQueCabem(palavras, indice, medidor, primeiraPagina);
        const qtdSegura = Math.max(1, Math.min(quantidade, palavras.length - indice));
        paginas.push(palavras.slice(indice, indice + qtdSegura).join(' '));
        indice += qtdSegura;
        primeiraPagina = false;
    }

    return paginas;
}

function agruparPaginasEmSpreads(paginas, paginasNoSpread) {
    if (!paginas.length) {
        return [];
    }
    if (paginasNoSpread <= 1) {
        return paginas.map((pagina) => `${pagina}${READER_SPREAD_SEPARATOR}`);
    }

    const spreads = [];
    for (let indice = 0; indice < paginas.length; indice += 2) {
        const esquerda = paginas[indice] || '';
        const direita = paginas[indice + 1] || '';
        spreads.push(`${esquerda}${READER_SPREAD_SEPARATOR}${direita}`);
    }
    return spreads;
}

function obterTotalPaginasDoCapitulo(totalPalavras, palavrasPorPagina) {
    const palavras = Math.max(0, Number(totalPalavras) || 0);
    const limite = Math.max(1, Number(palavrasPorPagina) || 200);
    return Math.max(1, Math.ceil(palavras / limite));
}

function calcularContadorGlobalLivro() {
    const paginasLocais = state.readerPagination.pages || [];
    const indiceLocal = state.readerPagination.currentPage || 0;
    const paginaLocalAtual = indiceLocal + 1;
    const totalPaginasLocais = paginasLocais.length || 1;
    const paginasNoSpread = leitorExibeDuasPaginas() ? 2 : 1;
    const palavrasPorSpread = state.readerPagination.wordsPerSpread
        || (calcularPalavrasPorPagina() * paginasNoSpread);
    const capitulosLivro = state.capituloAtivo?.historia?.capitulos;
    const capituloAtualId = state.capituloAtivo?.capitulo?.id;

    if (!Array.isArray(capitulosLivro) || !capitulosLivro.length || !capituloAtualId) {
        return {
            paginaAtual: paginaLocalAtual,
            totalPaginas: totalPaginasLocais,
        };
    }

    let paginasAntesDoCapituloAtual = 0;
    let totalPaginasLivro = 0;
    let capituloEncontrado = false;

    for (const capitulo of capitulosLivro) {
        const totalPaginasCapitulo = obterTotalPaginasDoCapitulo(capitulo.total_palavras, palavrasPorSpread);
        totalPaginasLivro += totalPaginasCapitulo;

        if (!capituloEncontrado) {
            if (capitulo.id === capituloAtualId) {
                capituloEncontrado = true;
            } else {
                paginasAntesDoCapituloAtual += totalPaginasCapitulo;
            }
        }
    }

    if (!capituloEncontrado) {
        return {
            paginaAtual: paginaLocalAtual,
            totalPaginas: Math.max(totalPaginasLocais, totalPaginasLivro),
        };
    }

    return {
        paginaAtual: Math.max(1, Math.min(totalPaginasLivro, paginasAntesDoCapituloAtual + paginaLocalAtual)),
        totalPaginas: Math.max(1, totalPaginasLivro),
    };
}

function obterDestaquesDaPagina(textoPagina) {
    const destaques = state.capituloAtivo?.capitulo?.destaques || {};
    const normalizarTexto = (valor) => String(valor || '').toLocaleLowerCase('pt-BR');
    const textoNormalizado = normalizarTexto(textoPagina);
    const meus = new Set((destaques.meus || []).map(normalizarTexto));
    const lista = [
        ...(destaques.recomendados || []).map((item) => ({...item, tipo: 'popular'})),
        ...(destaques.meus || []).map((trecho) => ({trecho, tipo: 'meu'})),
    ];

    return lista
        .filter((item) => item.trecho && textoNormalizado.includes(normalizarTexto(item.trecho)))
        .map((item) => ({
            ...item,
            tipo: meus.has(normalizarTexto(item.trecho)) ? 'meu' : item.tipo,
        }))
        .sort((a, b) => String(b.trecho).length - String(a.trecho).length);
}

function renderTextoComDestaques(texto, destaques) {
    // Primeiro escape do texto
    let base = escapeHtml(texto);
    if (!destaques || !destaques.length) {
        // aplica markdown inline quando não há destaques
        return renderMarkdownInline(base);
    }

    // Substitui trechos destacados por placeholders para não conflitar com markdown
    const placeholders = [];
    let idx = 0;
    for (const destaque of destaques) {
        const trecho = String(destaque.trecho || '');
        if (!trecho) continue;
        const classe = destaque.tipo === 'meu' ? 'reader-highlight-user' : 'reader-highlight-popular';
        const escapedTrecho = escapeHtml(trecho);
        const placeholder = `[[MARK_${idx}]]`;
        base = base.split(escapedTrecho).join(placeholder);
        placeholders.push({placeholder, html: `<mark class="${classe}">${escapedTrecho}</mark>`});
        idx += 1;
    }

    // Aplica markdown inline ao texto e restaura os highlights
    base = renderMarkdownInline(base);
    for (const ph of placeholders) {
        base = base.split(ph.placeholder).join(ph.html);
    }
    return base;
}

function renderMarcacoesLeitor() {
    if (!el.readerMarksList || !state.capituloAtivo) {
        return;
    }

    const destaques = state.capituloAtivo.capitulo?.destaques || {};
    const meus = destaques.meus || [];
    const recomendados = destaques.recomendados || [];
    const itens = [
        ...meus.map((trecho) => ({trecho, tipo: 'meu'})),
        ...recomendados
            .filter((item) => !meus.some((trecho) => String(trecho).toLocaleLowerCase('pt-BR') === String(item.trecho).toLocaleLowerCase('pt-BR')))
            .map((item) => ({...item, tipo: 'popular'})),
    ];

    if (el.readerMarksCount) {
        el.readerMarksCount.textContent = String(meus.length);
    }

    el.readerMarksList.innerHTML = itens.length
        ? itens.map((item) => `
            <article class="reader-mark-item">
                <div class="reader-mark-avatar">${escapeHtml((state.user?.nome || 'U').slice(0, 1).toUpperCase())}</div>
                <div>
                    <div class="reader-mark-head">
                        <strong>${item.tipo === 'meu' ? 'Você marcou' : 'Muito marcada'}</strong>
                        ${item.tipo === 'popular' ? `<span>${item.percentual || 60}% dos leitores</span>` : ''}
                    </div>
                    <p>${escapeHtml(item.trecho)}</p>
                    ${item.tipo === 'meu' ? `
                        <button class="mark-remove-btn" data-action="remove-highlight" data-highlight-text="${escapeAttribute(item.trecho)}" type="button">
                            Remover marcação
                        </button>
                    ` : ''}
                </div>
            </article>
        `).join('')
        : `<p class="placeholder">Os trechos destacados vão aparecer aqui.</p>`;
}

function renderPaginaAtualLeitura() {
    const paginas = state.readerPagination.pages || [];
    const indice = state.readerPagination.currentPage || 0;
    const total = paginas.length || 1;
    const spreadAtual = paginas[indice] || `${READER_SPREAD_SEPARATOR}`;
    const [textoEsquerda = '', textoDireita = ''] = String(spreadAtual).split(READER_SPREAD_SEPARATOR);
    const contadorLivro = calcularContadorGlobalLivro();
    const hasPrevChapter = Boolean(state.capituloAtivo?.navegacao?.anterior_id);
    const hasNextChapter = Boolean(state.capituloAtivo?.navegacao?.proximo_id);
    const hasGlobalPrev = indice > 0 || hasPrevChapter;
    const hasGlobalNext = indice < total - 1 || hasNextChapter;
    state.readerPagination.currentGlobalPage = contadorLivro.paginaAtual;

    const destaquesEsquerda = obterDestaquesDaPagina(textoEsquerda);
    const destaquesDireita = obterDestaquesDaPagina(textoDireita);
    aplicarPreferenciasVisuaisLeitor();
    const renderPagina = (texto, incluirTitulo = false, destaques = []) => `
        <article class="reader-page">
            ${incluirTitulo ? `<h3>${escapeHtml(state.capituloAtivo?.capitulo?.titulo || 'Capítulo')}</h3>` : ''}
            ${texto
                ? `<p class="reader-page-text">${renderTextoComDestaques(texto, destaques)}</p>`
                : (indice === 0 && incluirTitulo ? '<p>Este capítulo ainda não possui conteúdo.</p>' : '')}
        </article>
    `;

    el.readerContent.innerHTML = `
        <div class="reader-pages">
            <div class="reader-spread">
                ${renderPagina(textoEsquerda, indice === 0, destaquesEsquerda)}
                ${renderPagina(textoDireita, false, destaquesDireita)}
            </div>
        </div>
    `;

    if (el.readerPageCounter) {
        const percentual = Math.max(1, Math.round((contadorLivro.paginaAtual / contadorLivro.totalPaginas) * 100));
        el.readerPageCounter.textContent = `Local ${contadorLivro.paginaAtual} de ${contadorLivro.totalPaginas} • ${percentual}%`;
    }
    if (el.readerProgressRange) {
        el.readerProgressRange.max = String(total);
        el.readerProgressRange.value = String(indice + 1);
    }
    if (el.readerPagePrev) {
        el.readerPagePrev.disabled = !hasGlobalPrev;
    }
    if (el.readerPageNext) {
        el.readerPageNext.disabled = !hasGlobalNext;
    }
    renderMarcacoesLeitor();
    reiniciarTempoDaPagina();
    atualizarTempoLeituraUI();
}

async function navegarPaginaAnterior() {
    await registrarTempoLeituraAtual();
    if (state.readerPagination.currentPage > 0) {
        state.readerPagination.currentPage -= 1;
        renderPaginaAtualLeitura();
        return;
    }

    const anteriorId = state.capituloAtivo?.navegacao?.anterior_id;
    const historiaId = state.capituloAtivo?.historia?.id;
    if (!anteriorId || !historiaId) {
        return;
    }

    await abrirCapitulo(historiaId, anteriorId, {paginaInicial: 'ultima'});
}

async function navegarProximaPagina() {
    await registrarTempoLeituraAtual();
    const total = state.readerPagination.pages.length;
    if (state.readerPagination.currentPage < total - 1) {
        state.readerPagination.currentPage += 1;
        renderPaginaAtualLeitura();
        return;
    }

    const proximoId = state.capituloAtivo?.navegacao?.proximo_id;
    const historiaId = state.capituloAtivo?.historia?.id;
    if (!proximoId || !historiaId) {
        return;
    }

    await abrirCapitulo(historiaId, proximoId, {paginaInicial: 'primeira'});
}

function handleReaderPreferenceOptionClick(event) {
    const botaoFonte = event.target.closest('[data-reader-font]');
    if (botaoFonte && READER_FONTS.has(botaoFonte.dataset.readerFont || '')) {
        state.readerPrefs.fontFamily = botaoFonte.dataset.readerFont;
        onReaderPreferenceChanged();
        return;
    }

    const botaoFundo = event.target.closest('[data-reader-bg]');
    if (botaoFundo && READER_BACKGROUNDS.has(botaoFundo.dataset.readerBg || '')) {
        state.readerPrefs.bgColor = botaoFundo.dataset.readerBg;
        onReaderPreferenceChanged();
    }
}

function onReaderPreferenceChanged() {
    const fontSize = Number(el.readerFontSize?.value || state.readerPrefs.fontSize || 19);
    state.readerPrefs.fontSize = Math.max(16, Math.min(40, fontSize));

    if (el.readerFontSizeValue) {
        el.readerFontSizeValue.textContent = `${state.readerPrefs.fontSize}px`;
    }

    sincronizarControlesLeitor();
    aplicarPreferenciasVisuaisLeitor();
    salvarPreferenciasLeitor();
    aplicarPaginacaoCapitulo('manter');
}

function handleResizeLeitor() {
    if (!state.capituloAtivo || el.readerModal?.classList.contains('hidden')) {
        return;
    }
    clearTimeout(handleResizeLeitor.timer);
    handleResizeLeitor.timer = setTimeout(() => {
        aplicarPaginacaoCapitulo('manter');
    }, 140);
}

function carregarPreferenciasLeitor() {
    try {
        const raw = localStorage.getItem('storyflow_reader_prefs');
        if (!raw) {
            return;
        }
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === 'object') {
            if (typeof parsed.fontFamily === 'string' && READER_FONTS.has(parsed.fontFamily)) {
                state.readerPrefs.fontFamily = parsed.fontFamily;
            }
            if (typeof parsed.fontSize === 'number') {
                state.readerPrefs.fontSize = Math.max(16, Math.min(40, parsed.fontSize));
            }
            if (typeof parsed.bgColor === 'string' && READER_BACKGROUNDS.has(parsed.bgColor)) {
                state.readerPrefs.bgColor = parsed.bgColor;
            }
        }
    } catch (error) {
        // Preferências inválidas são ignoradas.
    }
}

function salvarPreferenciasLeitor() {
    localStorage.setItem('storyflow_reader_prefs', JSON.stringify(state.readerPrefs));
}

function sincronizarControlesLeitor() {
    if (el.readerFontSize) {
        el.readerFontSize.value = String(state.readerPrefs.fontSize);
    }
    if (el.readerFontSizeValue) {
        el.readerFontSizeValue.textContent = `${state.readerPrefs.fontSize}px`;
    }

    if (el.readerFontOptions) {
        const fontButtons = el.readerFontOptions.querySelectorAll('[data-reader-font]');
        fontButtons.forEach((button) => {
            const ativo = button.dataset.readerFont === state.readerPrefs.fontFamily;
            button.classList.toggle('is-active', ativo);
            button.setAttribute('aria-pressed', ativo ? 'true' : 'false');
        });
    }

    if (el.readerBgOptions) {
        const bgButtons = el.readerBgOptions.querySelectorAll('[data-reader-bg]');
        bgButtons.forEach((button) => {
            const ativo = button.dataset.readerBg === state.readerPrefs.bgColor;
            button.classList.toggle('is-active', ativo);
            button.setAttribute('aria-pressed', ativo ? 'true' : 'false');
        });
    }
}

function aplicarPreferenciasVisuaisLeitor() {
    if (!el.readerContent) {
        return;
    }
    el.readerContent.dataset.font = state.readerPrefs.fontFamily;
    el.readerContent.dataset.bg = state.readerPrefs.bgColor;
    el.readerContent.style.setProperty('--reader-font-size', `${state.readerPrefs.fontSize}px`);
    if (el.readerCard) {
        el.readerCard.dataset.bg = state.readerPrefs.bgColor;
    }
}

function iniciarSessaoLeitura() {
    const agora = Date.now();
    if (!state.readerSession.id) {
        state.readerSession.id = `sessao-${agora}-${Math.random().toString(36).slice(2, 10)}`;
    }
    if (!state.readerSession.startedAt) {
        state.readerSession.startedAt = agora;
    }
    state.readerSession.pageStartedAt = agora;
    if (!state.readerSession.intervalId) {
        state.readerSession.intervalId = window.setInterval(atualizarTempoLeituraUI, 1000);
    }
    if (!state.readerSession.autoSaveIntervalId) {
        state.readerSession.autoSaveIntervalId = window.setInterval(() => {
            salvarProgressoLeitura().catch(() => {});
        }, 15000);
    }
    atualizarTempoLeituraUI();
}

function reiniciarTempoDaPagina() {
    state.readerSession.pageStartedAt = Date.now();
}

function segundosDesde(timestamp) {
    if (!timestamp) {
        return 0;
    }
    return Math.max(0, Math.floor((Date.now() - timestamp) / 1000));
}

function formatarTempo(segundos) {
    const total = Math.max(0, Number(segundos) || 0);
    const minutos = Math.floor(total / 60);
    const resto = total % 60;
    return `${minutos}:${String(resto).padStart(2, '0')}`;
}

function obterTempoCapituloAtual() {
    const tempo = state.capituloAtivo?.tempo_leitura || state.capituloAtivo?.historia?.tempo_leitura;
    const capituloId = state.capituloAtivo?.capitulo?.id;
    const capitulo = tempo?.capitulos?.[capituloId];
    return Number(capitulo?.total_segundos || 0);
}

function obterTempoLivroAtual() {
    const tempo = state.capituloAtivo?.tempo_leitura || state.capituloAtivo?.historia?.tempo_leitura;
    return Number(tempo?.total_segundos || 0);
}

function obterSessoesLivroAtual() {
    const tempo = state.capituloAtivo?.tempo_leitura || state.capituloAtivo?.historia?.tempo_leitura;
    const sessoes = tempo?.sessoes;
    if (!sessoes || typeof sessoes !== 'object') {
        return [];
    }
    return Object.values(sessoes)
        .filter((sessao) => sessao && typeof sessao === 'object')
        .sort((a, b) => String(b.atualizada_em || '').localeCompare(String(a.atualizada_em || '')));
}

function renderSessoesLeitura() {
    if (!el.readerSessionsList || !el.readerSessionsCount) {
        return;
    }

    const sessoes = obterSessoesLivroAtual();
    el.readerSessionsCount.textContent = String(sessoes.length);

    if (!sessoes.length) {
        el.readerSessionsList.innerHTML = '<p class="placeholder">As sessões de leitura do livro aparecem aqui.</p>';
        return;
    }

    el.readerSessionsList.innerHTML = sessoes.slice(0, 6).map((sessao) => {
        const horario = formatarHorarioSessao(sessao.atualizada_em || sessao.iniciada_em);
        return `
            <article class="reader-session-item">
                <strong>${formatarTempo(sessao.total_segundos || 0)}</strong>
                <span>${escapeHtml(horario)}</span>
            </article>
        `;
    }).join('');
}

function formatarHorarioSessao(isoString) {
    if (!isoString) {
        return 'Agora';
    }
    const data = new Date(isoString);
    if (Number.isNaN(data.getTime())) {
        return 'Agora';
    }
    return data.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });
}

function atualizarTempoPrevisto() {
    if (!el.readerPredictedValue) {
        return;
    }
    const totalPaginas = Math.max(1, state.readerPagination.pages.length || 1);
    const paginaAtual = Math.max(1, (state.readerPagination.currentPage || 0) + 1);
    const restantes = Math.max(0, totalPaginas - paginaAtual);

    const tempoEstimadoCapitulo = Number(state.capituloAtivo?.capitulo?.tempo_estimado_minutos || 0) * 60;
    let mediaPorPagina = tempoEstimadoCapitulo
        ? Math.max(25, Math.round(tempoEstimadoCapitulo / totalPaginas))
        : 45;

    const tempoRealCapitulo = obterTempoCapituloAtual();
    if (tempoRealCapitulo > 0) {
        mediaPorPagina = Math.max(20, Math.round(tempoRealCapitulo / paginaAtual));
    }

    el.readerPredictedValue.textContent = formatarTempo(restantes * mediaPorPagina);
}

function atualizarTempoLeituraUI() {
    const paginaSegundos = segundosDesde(state.readerSession.pageStartedAt);
    const sessaoSegundos = segundosDesde(state.readerSession.startedAt);
    if (el.readerSessionTime) {
        el.readerSessionTime.textContent = formatarTempo(sessaoSegundos);
    }
    if (el.readerPageTime) {
        el.readerPageTime.textContent = formatarTempo(paginaSegundos);
    }
    if (el.readerChapterTime) {
        el.readerChapterTime.textContent = formatarTempo(obterTempoCapituloAtual() + paginaSegundos);
    }
    if (el.readerBookTime) {
        el.readerBookTime.textContent = formatarTempo(obterTempoLivroAtual() + paginaSegundos);
    }
    atualizarTempoPrevisto();
}

async function registrarTempoLeituraAtual() {
    if (!state.capituloAtivo || !state.readerSession.pageStartedAt) {
        return;
    }
    const segundos = segundosDesde(state.readerSession.pageStartedAt);
    if (segundos < 2) {
        reiniciarTempoDaPagina();
        return;
    }
    reiniciarTempoDaPagina();

    try {
        const response = await api('/me/tempo-leitura', {
            method: 'POST',
            body: {
                historia_id: state.capituloAtivo.historia.id,
                capitulo_id: state.capituloAtivo.capitulo.id,
                pagina_global: state.readerPagination.currentGlobalPage || 1,
                segundos,
                sessao_id: state.readerSession.id,
            },
        });
        if (response.tempo_leitura) {
            state.capituloAtivo.tempo_leitura = response.tempo_leitura;
        }
        renderSessoesLeitura();
        atualizarTempoLeituraUI();
    } catch (error) {
        state.readerSession.unsentSeconds += segundos;
    }
}

async function destacarSelecaoAtual() {
    if (!state.capituloAtivo) {
        return;
    }
    const selection = window.getSelection();
    const range = selection && selection.rangeCount ? selection.getRangeAt(0) : null;
    const origemValida = range && el.readerContent?.contains(range.commonAncestorContainer);
    if (!origemValida) {
        showToast('Selecione um trecho dentro da página de leitura.', true);
        return;
    }
    const trecho = selection ? String(selection.toString()).trim() : '';
    if (!trecho) {
        showToast('Selecione um trecho da página para destacar.', true);
        return;
    }

    try {
        const response = await api('/me/destaques', {
            method: 'POST',
            body: {
                historia_id: state.capituloAtivo.historia.id,
                capitulo_id: state.capituloAtivo.capitulo.id,
                trecho,
            },
        });
        if (response.destaques) {
            state.capituloAtivo.capitulo.destaques = response.destaques;
        }
        selection?.removeAllRanges();
        renderMarcacoesLeitor();
        renderPaginaAtualLeitura();
        showToast(response.mensagem || 'Trecho destacado.');
    } catch (error) {
        handleError(error);
    }
}

async function handleReaderMarksClick(event) {
    const button = event.target.closest('[data-action="remove-highlight"]');
    if (!button || !state.capituloAtivo) {
        return;
    }

    try {
        const response = await api('/me/destaques', {
            method: 'DELETE',
            body: {
                historia_id: state.capituloAtivo.historia.id,
                capitulo_id: state.capituloAtivo.capitulo.id,
                trecho: button.dataset.highlightText || '',
            },
        });
        if (response.destaques) {
            state.capituloAtivo.capitulo.destaques = response.destaques;
        }
        renderMarcacoesLeitor();
        renderPaginaAtualLeitura();
        showToast(response.mensagem || 'Marcação removida.');
    } catch (error) {
        handleError(error);
    }
}

async function fecharLeitor() {
    await registrarTempoLeituraAtual();
    if (state.readerSession.intervalId) {
        window.clearInterval(state.readerSession.intervalId);
    }
    if (state.readerSession.autoSaveIntervalId) {
        window.clearInterval(state.readerSession.autoSaveIntervalId);
    }
    state.readerSession = {
        id: null,
        startedAt: null,
        pageStartedAt: null,
        intervalId: null,
        autoSaveIntervalId: null,
        unsentSeconds: 0,
    };
    definirPainelLeitorInicial();
    el.readerModal?.classList.add('hidden');
    el.readerModal?.setAttribute('aria-hidden', 'true');
}

async function salvarProgressoLeitura(percentualForcado) {
    if (!state.capituloAtivo) {
        return;
    }

    const historiaId = state.capituloAtivo.historia.id;
    let percentual = percentualForcado;
    if (typeof percentual !== 'number') {
        const totalCapitulos = state.historiaDetalhe?.id === historiaId
            ? state.historiaDetalhe.total_capitulos
            : (state.catalogo.find((story) => story.id === historiaId)?.total_capitulos || state.capituloAtivo.capitulo.ordem);
        percentual = Math.min(100, Math.round((state.capituloAtivo.capitulo.ordem / Math.max(1, totalCapitulos)) * 100));
    }

    try {
        const response = await api('/me/progresso', {
            method: 'POST',
            body: {
                historia_id: historiaId,
                capitulo_id: state.capituloAtivo.capitulo.id,
                percentual,
            },
        });
        showToast(response.mensagem || 'Progresso atualizado.');
        await atualizarDadosPosLeitura(historiaId);
    } catch (error) {
        handleError(error);
    }
}

async function comentarCapituloAtual(event) {
    event.preventDefault();
    if (!state.capituloAtivo || !el.readerCommentInput.value.trim()) {
        return;
    }
    try {
        const response = await api('/me/comentar', {
            method: 'POST',
            body: {
                historia_id: state.capituloAtivo.historia.id,
                capitulo_id: state.capituloAtivo.capitulo.id,
                conteudo: el.readerCommentInput.value.trim(),
            },
        });
        showToast(response.mensagem || 'Comentário enviado.');
        el.readerCommentInput.value = '';
        await abrirCapitulo(
            state.capituloAtivo.historia.id,
            state.capituloAtivo.capitulo.id,
            {paginaInicial: 'manter'},
        );
    } catch (error) {
        handleError(error);
    }
}

async function handleCommentActionClick(event) {
    const button = event.target.closest('[data-action]');
    if (!button || !state.capituloAtivo) {
        return;
    }

    const action = button.dataset.action;
    if (!['edit-comment', 'delete-comment'].includes(action)) {
        return;
    }

    const comentarioId = button.dataset.commentId;
    const historiaId = state.capituloAtivo.historia.id;
    const capituloId = state.capituloAtivo.capitulo.id;
    const comentarioAtual = (state.capituloAtivo.capitulo.comentarios_recentes || [])
        .find((item) => item.id === comentarioId);

    if (!comentarioAtual) {
        showToast('Comentário não encontrado.', true);
        return;
    }

    try {
        if (action === 'edit-comment') {
            const novoConteudo = prompt('Editar comentário:', comentarioAtual.conteudo || '');
            if (novoConteudo === null) {
                return;
            }
            const conteudo = novoConteudo.trim();
            if (!conteudo) {
                showToast('Comentário não pode ficar vazio.', true);
                return;
            }

            const response = await api('/me/comentar', {
                method: 'PUT',
                body: {
                    historia_id: historiaId,
                    capitulo_id: capituloId,
                    comentario_id: comentarioId,
                    conteudo,
                },
            });

            const editado = response.comentario;
            if (editado) {
                state.capituloAtivo.capitulo.comentarios_recentes = (state.capituloAtivo.capitulo.comentarios_recentes || [])
                    .map((item) => item.id === comentarioId ? editado : item);
                renderModalLeitura();
            }
            showToast(response.mensagem || 'Comentário editado.');
            return;
        }

        if (action === 'delete-comment') {
            const confirmar = confirm('Deseja realmente excluir este comentário?');
            if (!confirmar) {
                return;
            }

            const response = await api('/me/comentar', {
                method: 'DELETE',
                body: {
                    historia_id: historiaId,
                    capitulo_id: capituloId,
                    comentario_id: comentarioId,
                },
            });

            state.capituloAtivo.capitulo.comentarios_recentes = (state.capituloAtivo.capitulo.comentarios_recentes || [])
                .filter((item) => item.id !== comentarioId);
            renderModalLeitura();
            showToast(response.mensagem || 'Comentário excluído.');
        }
    } catch (error) {
        handleError(error);
    }
}

async function atualizarDadosPosLeitura(historiaId) {
    const tarefas = [carregarPainel()];
    if (['inicio', 'historias'].includes(state.page)) {
        tarefas.push(carregarCatalogo());
    }
    if (state.page === 'biblioteca') {
        tarefas.push(carregarBiblioteca());
    }
    await Promise.all(tarefas);

    if (state.page === 'inicio') {
        renderInicio();
    }
    if (state.page === 'historias') {
        renderHistorias();
        if (state.historiaDetalhe?.id === historiaId) {
            await selecionarHistoria(historiaId);
        }
    }
    if (state.page === 'biblioteca') {
        renderBiblioteca();
    }
    if (state.page === 'voce') {
        renderVoce();
    }
}

async function encerrarSessao() {
    try {
        await api('/auth/logout', {
            method: 'POST',
            body: {token: state.token},
            auth: false,
        });
    } catch (error) {
        // Mesmo em erro de logout, seguimos com limpeza local da sessão.
    } finally {
        redirecionarLogin();
    }
}

async function enviarFotoPerfil(event) {
    event.preventDefault();
    const file = el.profilePhotoInput?.files?.[0];
    if (!file) {
        showToast('Selecione uma imagem para salvar no perfil.', true);
        return;
    }

    const tiposPermitidos = new Set(['image/png', 'image/jpeg', 'image/webp']);
    if (!tiposPermitidos.has(file.type)) {
        showToast('Formato inválido. Use PNG, JPG ou WEBP.', true);
        return;
    }
    if (file.size > 2 * 1024 * 1024) {
        showToast('Imagem muito grande. Use até 2MB.', true);
        return;
    }

    try {
        const dataUrl = await lerArquivoComoDataURL(file);
        const response = await api('/me/perfil/foto', {
            method: 'POST',
            body: {foto_perfil: dataUrl},
        });
        if (response.conta) {
            state.user = {...(state.user || {}), ...response.conta};
            atualizarIdentidadeUI();
        }
        showToast(response.mensagem || 'Foto de perfil atualizada.');
    } catch (error) {
        handleError(error);
    }
}

async function removerFotoPerfil() {
    try {
        const response = await api('/me/perfil/foto', {
            method: 'POST',
            body: {foto_perfil: ''},
        });
        if (response.conta) {
            state.user = {...(state.user || {}), ...response.conta};
            atualizarIdentidadeUI();
        }
        if (el.profilePhotoInput) {
            el.profilePhotoInput.value = '';
        }
        showToast(response.mensagem || 'Foto removida.');
    } catch (error) {
        handleError(error);
    }
}

function atualizarIdentidadeUI() {
    if (el.headerUserName) {
        el.headerUserName.textContent = state.user?.nome || 'Usuário';
    }
    if (el.perfilNome) {
        el.perfilNome.textContent = state.user?.nome || 'Usuário';
    }
    if (el.perfilEmail) {
        el.perfilEmail.textContent = state.user?.email || '-';
    }
    atualizarAvatarUI();
}

function atualizarAvatarUI() {
    const foto = String(state.user?.foto_perfil || '').trim();
    const inicial = obterInicialNome(state.user?.nome);

    if (el.sidebarAvatarLetter) {
        el.sidebarAvatarLetter.textContent = foto ? '' : inicial;
    }
    if (el.profileAvatar) {
        el.profileAvatar.textContent = foto ? '' : inicial;
    }

    for (const avatar of [el.sidebarAvatar, el.profileAvatar]) {
        if (!avatar) {
            continue;
        }
        if (foto) {
            avatar.classList.add('has-photo');
            avatar.style.backgroundImage = `url(${foto})`;
        } else {
            avatar.classList.remove('has-photo');
            avatar.style.backgroundImage = 'none';
        }
    }

    if (el.profilePhotoRemove) {
        el.profilePhotoRemove.classList.toggle('hidden', !foto);
    }
}

function obterInicialNome(nome) {
    const texto = String(nome || '').trim();
    if (!texto) {
        return 'U';
    }
    return texto[0].toUpperCase();
}

function lerArquivoComoDataURL(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ''));
        reader.onerror = () => reject(new Error('Não foi possível ler o arquivo.'));
        reader.readAsDataURL(file);
    });
}

function normalizarCategoria(categoria) {
    const valor = String(categoria || '').trim().toLowerCase();
    const mapa = {
        lendo: 'lendo',
        favoritos: 'favoritos',
        pausados: 'pausados',
        concluidos: 'concluidos',
        'concluídos': 'concluidos',
    };
    return mapa[valor] || 'lendo';
}

function atualizarQueryHistoria(storyId) {
    if (state.page !== 'historias') {
        return;
    }
    const params = new URLSearchParams(window.location.search);
    params.set('story', storyId);
    const query = params.toString();
    history.replaceState({}, '', `${window.location.pathname}${query ? `?${query}` : ''}`);
}

function redirecionarLogin() {
    localStorage.removeItem(TOKEN_KEY);
    window.location.href = '/';
}

function handleError(error) {
    showToast(error.message || 'Ocorreu um erro inesperado.', true);
}

async function api(path, options = {}) {
    const method = options.method || 'GET';
    const query = options.query || null;
    const headers = {'Accept': 'application/json'};
    let url = `${API_BASE}${path}`;

    if (query) {
        const params = new URLSearchParams();
        Object.entries(query).forEach(([key, value]) => {
            if (value !== undefined && value !== null && String(value).trim() !== '') {
                params.append(key, String(value));
            }
        });
        const queryText = params.toString();
        if (queryText) {
            url += `?${queryText}`;
        }
    }

    if (options.body !== undefined) {
        headers['Content-Type'] = 'application/json';
    }
    if (options.auth !== false) {
        headers.Authorization = `Bearer ${state.token}`;
    }

    const response = await fetch(url, {
        method,
        headers,
        body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.sucesso === false) {
        if (response.status === 401) {
            redirecionarLogin();
        }
        throw new Error(data.erro || 'Não foi possível concluir a operação.');
    }
    return data;
}

function showToast(message, error = false) {
    if (!el.toast) {
        return;
    }
    el.toast.textContent = message;
    el.toast.classList.remove('hidden', 'error');
    if (error) {
        el.toast.classList.add('error');
    }
    clearTimeout(showToast.timer);
    showToast.timer = setTimeout(() => {
        el.toast.classList.add('hidden');
    }, 2800);
}

function corNomeUsuario(nome) {
    const texto = String(nome || 'usuario');
    let hash = 0;
    for (let i = 0; i < texto.length; i += 1) {
        hash = ((hash << 5) - hash) + texto.charCodeAt(i);
        hash |= 0;
    }
    const hue = Math.abs(hash) % 360;
    return `hsl(${hue} 78% 70%)`;
}

function atualizarSeletorAvaliacao(nota, options = {}) {
    const valor = Math.max(1, Math.min(5, Number(nota || 1)));
    const sentimento = notaParaSentimento(valor);
    const storyId = String(options.storyId || '').trim();
    const seletor = storyId
        ? `[data-sentimento-voto][data-story-id="${storyId}"]`
        : '[data-sentimento-voto]';
    const botoesSentimento = document.querySelectorAll(seletor);
    botoesSentimento.forEach((botao) => {
        botao.classList.toggle('is-active', botao.dataset.sentimentoVoto === sentimento);
    });
    if (!options.preview && state.historiaDetalhe) {
        state.historiaDetalhe.minha_avaliacao = valor;
    }
}

function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

function escapeAttribute(value) {
    return escapeHtml(value);
}

// Render markdown básico (inline): **negrito** e *itálico*
function renderMarkdownInline(escapedText) {
    if (!escapedText) return '';
    let out = String(escapedText);
    try {
        // Negrito: **texto** -> <strong>
        out = out.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        // Itálico: *texto* -> <em> (após negrito para evitar conflito)
        out = out.replace(/\*(.+?)\*/g, '<em>$1</em>');
    } catch (e) {
        return escapedText;
    }
    return out;
}
