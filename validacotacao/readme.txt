# Cotação de Frete Intelipost (Streamlit)

Aplicação web em **Streamlit** para cotação de frete via API da Intelipost, com interface moderna, suporte a múltiplos CEPs (texto e Excel) e análise de médias por transportadora e CEP destino. A API key é mantida apenas na sessão atual do navegador, não sendo salva em arquivos. [web:36][web:23]

## Funcionalidades

- Entrada de CEP de origem.
- Entrada de múltiplos CEPs de destino:
  - digitados (separados por vírgula, ponto e vírgula ou quebra de linha);
  - importados de planilha Excel (coluna A).
- Definição de peso e dimensões do produto (peso, largura, altura, comprimento) e valor da mercadoria.
- Chamada à API **`quote_by_product`** da Intelipost para cada CEP de destino.
- Exibição de todas as opções de frete retornadas:
  - transportadora;
  - prazo em dias úteis;
  - valor do frete.
- Cálculo de médias:
  - por transportadora (média de valor e de prazo);
  - por CEP de destino (média de valor e de prazo).
- Download das cotações em arquivo **Excel (.xlsx)**.
- Aba de execução com logs por CEP (status da chamada e possíveis erros).
- Área de debug exibindo o último payload enviado para a API.

## Arquivos principais

- `app_streamlit_intelipost.py`: código principal do app Streamlit.
- `requirements.txt`: dependências mínimas para execução. [web:23]

## Requisitos

- Python 3.10+ (recomendado).
- Pacotes listados em `requirements.txt`:
  - `streamlit`
  - `pandas`
  - `requests`
  - `openpyxl` (para leitura/gravação de Excel com o pandas) [web:27]

## Instalação e uso local

1. Clone este repositório ou copie os arquivos para uma pasta local.

2. (Opcional, mas recomendado) Crie e ative um ambiente virtual:

   ```bash
   python -m venv .venv
   # Linux / MacOS
   source .venv/bin/activate
   # Windows
   .venv\Scripts\activate
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Execute o aplicativo Streamlit:

   ```bash
   streamlit run app_streamlit_intelipost.py
   ```

   O comando `streamlit run` inicia a aplicação e, se o arquivo for informado, abre aquele script como app. [web:38]

5. Abra o navegador em `http://localhost:8501` (ou o endereço mostrado no terminal).

## Como usar a aplicação

1. **Configurar a API Key**

   - Na barra lateral, informe sua **API Key Intelipost**.
   - A chave é armazenada em memória na sessão (`st.session_state`) e vale apenas para a aba/sessão atual.
   - Nenhum arquivo de configuração é criado para guardar a chave.

2. **Preencher os dados da cotação**

   - Informe o **CEP de origem**.
   - Informe um ou mais **CEPs de destino**:
     - digitando no campo de texto (separados por vírgula, ponto e vírgula ou quebra de linha); ou
     - enviando um arquivo Excel com os CEPs na **coluna A**.
   - Preencha:
     - **Peso (kg)**
     - **Largura (cm)**
     - **Altura (cm)**
     - **Comprimento (cm)**
     - **Valor do item (R$)**

3. **Gerar cotações**

   - Clique em **“🚀 Cotar fretes”**.
   - A aplicação chamará a API da Intelipost para cada CEP de destino, exibindo barra de progresso e mensagens de status.
   - Em caso de erro HTTP ou exceção, o app mostra mensagem na tela e registra a informação na aba de execução.

4. **Visualizar resultados**

   - **Aba “Cotações”**:
     - Tabela com todas as opções de frete (CEP destino, transportadora, prazo em dias úteis e valor do frete).
     - Botão **“💾 Baixar Excel”** para exportar o resultado atual em `.xlsx`.
   - **Aba “Médias por transportadora”**:
     - Tabela com média de valor de frete, média de prazo e quantidade de opções por transportadora.
     - Gráfico de barras com o valor médio por transportadora.
   - **Aba “Médias por CEP”**:
     - Tabela com média de valor de frete, média de prazo e quantidade de opções por CEP de destino.
     - Gráfico de barras com o valor médio por CEP.
   - **Aba “Execução”**:
     - Logs por CEP (status da chamada, quantidade de opções retornadas, etc.).
     - Área de debug com o último payload enviado para a API, útil para troubleshooting.

5. **Limpar resultados**

   - Use o botão **“🧹 Limpar resultados”** na área principal para apagar as cotações e logs da sessão atual.

## Notas sobre segurança da API Key

- A API key é digitada pelo usuário na barra lateral.
- A chave **não é armazenada em disco** nem em banco de dados.
- Ela é mantida em `st.session_state`, que é específico da sessão/aba e existe apenas enquanto o app estiver aberto naquela conexão. [web:11][web:12]
- Ao recarregar a página, fechar a aba ou encerrar a sessão, a API key é perdida (será necessário digitá-la novamente).

## Deploy (opcional)

Você pode implantar este app em qualquer ambiente compatível com Streamlit. [web:25][web:47]

### Streamlit Community Cloud

1. Suba o código para um repositório no GitHub com:
   - `app_streamlit_intelipost.py`
   - `requirements.txt`
   - `README.md`
2. Crie um novo app em:
   https://share.streamlit.io
3. Aponte para o repositório e o arquivo `app_streamlit_intelipost.py` como entrypoint.
4. O serviço instalará as dependências com base no `requirements.txt`. [web:23][web:25]

### Outras opções

- Servidor próprio (VM, Docker, etc.), desde que:
  - Python e as libs de `requirements.txt` estejam instalados;
  - o comando de inicialização seja algo como:

  ```bash
  streamlit run app_streamlit_intelipost.py --server.headless true
  ```

## Licença

Defina aqui a licença do projeto (por exemplo, MIT, Apache 2.0, uso interno, etc.).