# Guia de manutencao - Gestor de Fretes

Este documento descreve a estrutura atual da aplicacao, o fluxo de dados e os pontos que devem ser conferidos durante futuras manutencoes.

## 1. Como executar

O projeto usa Flask, Flask-SQLAlchemy e SQLite. O ambiente virtual ja existente deve ser usado para evitar que o Python global fique sem as dependencias.

```powershell
.\venv\Scripts\Activate.ps1
python run.py
```

O `run.py` chama `create_app()` e inicia o servidor Flask em modo debug. O modo debug e util durante o desenvolvimento, mas nao deve ser usado em um servidor publico.

## 2. Mapa dos arquivos

- `run.py`: ponto de entrada do servidor local.
- `app/__init__.py`: factory Flask, configuracoes, registro dos blueprints e inicializacao do banco.
- `app/database.py`: instancia compartilhada do SQLAlchemy.
- `app/models.py`: tabelas, colunas e relacionamentos do dominio.
- `app/routes/main.py`: dashboard e quadro Kanban.
- `app/routes/cadastros.py`: empresas, transportadoras, fornecedores e APIs de edicao.
- `app/routes/pedidos.py`: pedidos, cotacoes atuais, datas, entrega, ocorrencias e anexos.
- `app/routes/cotacoes.py`: fluxo antigo de cotacoes mantido por compatibilidade.
- `app/templates/base.html`: layout, menu lateral, carregamento AJAX e interceptacao de formularios.
- `app/templates/dashboard/kanban.html`: colunas do Kanban e modais de operacao.
- `app/templates/pedidos/novo.html`: formulario de criacao de pedido.
- `app/templates/pedidos/detalhes.html`: fragmento do fluxo antigo de cotacoes.
- `app/templates/cadastros/*.html`: telas de cadastro, listagem e edicao.
- `instance/gestor.db`: banco SQLite local. A pasta esta ignorada pelo Git.

## 3. Inicializacao da aplicacao

1. `create_app()` cria o objeto Flask.
2. A URI `sqlite:///gestor.db` aponta para o banco da instancia Flask.
3. `db.init_app(app)` conecta o SQLAlchemy ao Flask.
4. Os blueprints sao importados e registrados.
5. Dentro do contexto da aplicacao, `db.create_all()` cria tabelas ausentes.
6. `_atualizar_schema()` adiciona colunas novas ao banco antigo.

A atualizacao de schema e intencionalmente simples: ela somente adiciona colunas. Se for necessario renomear, remover ou transformar dados, deve ser adotada uma ferramenta de migracao versionada, como Flask-Migrate/Alembic.

## 4. Modelo de dados

### Cadastros

`Empresa`, `Fornecedor` e `Transportadora` possuem razao social, CNPJ, endereco, contato e telefone. O CNPJ e armazenado sem mascara. A aplicacao hoje verifica duplicidade na rota, mas ainda nao possui `UNIQUE` no banco.

### Pedido

`Pedido` e o registro central. Seus campos principais sao:

- identificacao: `numero_pedido_compra`;
- valores e carga: `valor_mercadoria`, `volumes`, `peso_kg` e dimensoes;
- fluxo: `status`, `data_coleta`, `data_entrega`;
- resultado: `data_confirmacao_entrega` e `observacao_ocorrencia`;
- vinculos: `empresa_id`, `fornecedor_id`, `cotacoes` e `anexos`.

### CotacaoFrete

Uma cotacao pertence a um pedido e pode apontar para uma transportadora. `aprovada=True` identifica a cotacao vencedora no fluxo atual. `observacao` guarda a justificativa quando uma cotacao mais cara e escolhida.

### Anexo

`Anexo` guarda os metadados no banco. O arquivo real fica em `app/static/uploads`. A exclusao em cascade remove o registro, mas nao remove automaticamente o arquivo fisico.

## 5. Estados do Kanban

Os status usados pelo fluxo atual sao exatamente estes valores em minusculas:

```text
em_cotacao -> aguardando_coleta -> em_transito -> entregue
                                      |              ^
                                      v              |
                                  ocorrencia -------+
                                      |
                                      +-- nova entrega posterior -> em_transito
```

- `em_cotacao`: pedido criado, ainda recebendo propostas.
- `aguardando_coleta`: existe uma cotacao aprovada e datas definidas.
- `em_transito`: a data de coleta chegou; a promocao ocorre quando o dashboard e acessado.
- `entregue`: entrega confirmada.
- `ocorrencia`: problema registrado. O pedido pode ser confirmado como entregue ou ter uma nova data de entrega informada; se a nova data for posterior a anterior, ele retorna para `em_transito`.

A promocao para `em_transito` nao ocorre em tarefa agendada. Se ninguem acessar o dashboard, o status permanece temporariamente em `aguardando_coleta`.

## 6. Endpoints principais

### Dashboard

- `GET /` e `GET /kanban`: renderizam o Kanban.
- `GET /kanban?empresa_id=<id>`: filtra os pedidos de uma empresa.

### Cadastros

- `GET|POST /cadastros/empresas`
- `GET|POST /cadastros/transportadoras`
- `GET|POST /cadastros/fornecedores`
- `GET /cadastros/verificar-cnpj?cnpj=...&tipo=...`
- `GET /cadastros/api/<tipo>/<id>`
- `POST /cadastros/api/<tipo>/atualizar/<id>`

As rotas POST aceitam formulario normal e, quando identificadas como AJAX/JSON, devolvem JSON para o frontend atualizar a tabela sem recarregar a pagina.

### Pedidos e cotacoes atuais

- `GET|POST /pedidos/novo`: exibe ou cria pedido com status `em_cotacao`.
- `POST /pedidos/salvar`: alias usado por formularios antigos.
- `POST /pedidos/<id>/incluir_cotacao`: cria proposta.
- `GET /pedidos/<id>/cotacoes`: retorna dados para o modal.
- `POST /pedidos/cotacoes/<id>/selecionar_vencedora`: aprova proposta e exige justificativa se ela nao for a menor.
- `POST /pedidos/<id>/datas`: salva coleta e entrega.
- `POST /pedidos/<id>/confirmar-entrega`: confirma entrega ou registra ocorrencia.
- `POST /pedidos/cotacoes/<id>/reverter_vencedora`: reabre o pedido para cotacao.
- `POST /pedidos/<id>/excluir`: remove pedido e registros relacionados.

### Anexos

- `GET|POST /pedidos/<id>/anexos`: lista ou salva anexos.
- `GET /pedidos/uploads/<filename>`: serve arquivo salvo.

Extensoes permitidas atualmente: PDF, PNG, JPG, JPEG, XML, ZIP, DOC e DOCX.

## 7. Como o frontend funciona

`base.html` e o shell da aplicacao. Os links laterais chamam `carregarTela()`, que faz `fetch` com o cabecalho `X-Requested-With: XMLHttpRequest` e injeta o HTML recebido em `#conteudo-principal`. Scripts presentes no fragmento sao recriados para voltar a funcionar depois da injecao.

`kanban.html` exibe os pedidos por status e concentra os modais de cotacao, anexos e confirmacao de entrega. O JavaScript chama as APIs de `pedidos.py` e recarrega o dashboard apos operacoes que alteram o banco.

Os templates de cadastro repetem uma estrutura semelhante: formulario, validacao de CNPJ, consulta de CEP via ViaCEP, envio AJAX e modal de edicao.

## 8. Pontos de atencao para manutencao

1. Existem dois fluxos de cotacao. O atual esta em `routes/pedidos.py`; o legado esta em `routes/cotacoes.py` e `templates/pedidos/detalhes.html`. O legado usa referencias a `vencedora`, enquanto o modelo atual usa `aprovada`, e tambem usa status com maiusculas. Antes de reutiliza-lo, alinhe esses nomes.
2. O menu possui link para `/relatorios`, mas ainda nao existe blueprint/rota de relatorios.
3. Os KPIs de economia e valor medio ainda sao enviados como `0,00` pelo dashboard.
4. Nao ha autenticacao, autorizacao ou protecao CSRF.
5. `SECRET_KEY` esta fixa no codigo e `run.py` liga `debug=True`.
6. Uploads nao possuem limite de tamanho, validacao de conteudo ou controle de acesso por usuario.
7. Valores inseridos com `innerHTML` no JavaScript devem ser tratados com cuidado para evitar XSS se dados externos forem armazenados.
8. Conversoes diretas com `float()` e `int()` podem gerar erro 500 quando a entrada nao e numerica.
9. A transicao automatica depende do acesso ao dashboard; um worker agendado seria necessario para atualizacao independente de usuario.
10. Nao ha suite de testes no repositorio. Os primeiros testes recomendados cobrem criacao de pedido, duplicidade de CNPJ, selecao de cotacao, datas, entrega, ocorrencia e upload.

## 9. Rotina recomendada antes de alterar

1. Identifique se a mudanca pertence ao modelo, rota, template ou JavaScript.
2. Confira os nomes de campos em `models.py` e no schema existente.
3. Verifique se a requisicao e normal ou AJAX e preserve o formato de resposta esperado.
4. Mantenha os status em minusculas conforme a tabela desta documentacao.
5. Execute a compilacao Python e teste as rotas com `app.test_client()`.
6. Para mudancas de banco, teste com uma copia do `instance/gestor.db`.
7. Verifique tambem o fluxo legado antes de remover qualquer rota ou template relacionado a cotacoes.

## 10. Validacao atual

A aplicacao foi validada com:

```powershell
.\venv\Scripts\python.exe -m compileall -q app run.py
```

Tambem foram testadas as rotas HTML principais e respostas 404 das APIs para registros inexistentes usando o cliente de testes do Flask.
