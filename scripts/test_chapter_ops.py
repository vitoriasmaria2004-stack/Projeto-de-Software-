from app.controllers.usuario_controller import UsuarioController, usuarios_db, contas_db, sessoes_db
from app.controllers.historia_controller import HistoriaController, historias_db

# Registrar conta
resp = UsuarioController.registrar_conta('Tester', 'tester@example.com', 'senha123')
print('registrar_conta:', resp)
if not resp.get('sucesso'):
    raise SystemExit('Não registrou conta')

conta = resp.get('conta')
token = resp.get('token')
print('token:', token)

# Criar história
criar = UsuarioController.publicar_historia(token, 'Livro de Teste', 'Sinopse teste', 'Teste', None)
print('publicar_historia:', criar)
if not criar.get('sucesso'):
    raise SystemExit('Não criou história')

historia_id = criar.get('id') or criar.get('historia', {}).get('id')
print('historia_id:', historia_id)

# Adicionar capítulo
add = UsuarioController.adicionar_capitulo_por_token(token, historia_id, 'Cap 1', 'Conteúdo inicial')
print('adicionar_capitulo:', add)
cap_id = add.get('id')

# Editar capítulo
edit = UsuarioController.editar_capitulo_por_token(token, historia_id, cap_id, 'Cap 1 editado', 'Conteúdo editado')
print('editar_capitulo:', edit)

# Tentar editar com dados vazios (deve falhar)
edit_fail = UsuarioController.editar_capitulo_por_token(token, historia_id, cap_id, '', '')
print('editar_capitulo falha esperada:', edit_fail)

# Excluir capítulo
delete = UsuarioController.excluir_capitulo_por_token(token, historia_id, cap_id)
print('excluir_capitulo:', delete)

# Verificar que capítulo foi removido
historia = historias_db.get(historia_id)
print('capitulos finais:', [c.titulo for c in historia.capitulos])
