#!/bin/bash

# =================================================================
# Script para Criar Issues do Projeto 'monitor_net-web'
# Gerado por: Gerente de Issues (Gemini)
# Data: 2025-06-26
# =================================================================

# --- Configuração ---
# Define a URL do repositório onde as issues serão criadas.
REPO="docg1701/monitor_net"

# --- Criação das Issues ---

echo "Iniciando a criação de issues no repositório: $REPO"
echo "----------------------------------------------------"

# Issue 1: Módulo 1
gh issue create \
    --repo "$REPO" \
    --title "Módulo 1: Estrutura e Ponto de Entrada" \
    --body-file - \
    --assignee "docg1701" \
    --label "epic,setup,refactor,cli" <<'EOF'
-   [ ] Configurar dependências do projeto
    -   Adicionar `eel` ao `pyproject.toml` para a comunicação da interface.
    -   Adicionar `pyinstaller` como uma dependência de desenvolvimento para empacotamento.
-   [ ] Refatorar o ponto de entrada `main()` em `monitor_net.py`
    -   Adicionar análise de argumentos para detectar uma flag como `--cli` ou `--terminal`.
    -   Se a flag `--cli` estiver presente, o programa deve executar a lógica da interface de terminal existente.
    -   Se nenhuma flag for passada, o programa deve iniciar a interface web com Eel como padrão.
-   [ ] Garantir que o script `netmonitor` funcione corretamente
    -   O comando `netmonitor` gerado pelo `pyproject.toml` deve executar a nova lógica do ponto de entrada.
EOF
echo "✅ Issue 'Módulo 1' criada."

# Issue 2: Módulo 2
gh issue create \
    --repo "$REPO" \
    --title "Módulo 2: Backend (Lógica com Eel)" \
    --body-file - \
    --assignee "docg1701" \
    --label "epic,backend,python" <<'EOF'
-   [ ] Expor funções Python para o JavaScript via Eel
    -   Criar uma função Python, exposta com `@eel.expose`, para que o frontend possa solicitar o início/parada do monitoramento.
    -   Criar uma função que o frontend possa chamar para passar o nome do host a ser monitorado.
-   [ ] Implementar o envio de dados em tempo real para o frontend
    -   Adaptar o loop de monitoramento para, a cada medição de latência, enviar os dados (latência, estatísticas) para uma função JavaScript no frontend.
EOF
echo "✅ Issue 'Módulo 2' criada."

# Issue 3: Módulo 3
gh issue create \
    --repo "$REPO" \
    --title "Módulo 3: Frontend (Interface Web em HTML/CSS/JS)" \
    --body-file - \
    --assignee "docg1701" \
    --label "epic,frontend,ui,javascript" <<'EOF'
-   [ ] Desenvolver o arquivo `index.html`
    -   Criar a estrutura da página com uma área para o gráfico, uma seção para as estatísticas, um campo de texto para o host e os botões "Iniciar" e "Parar".
-   [ ] Desenvolver o arquivo `style.css`
    -   Criar um estilo visual limpo, leve e responsivo que se adapte bem a telas de desktop e de celular.
-   [ ] Desenvolver o arquivo `main.js`
    -   Implementar a lógica dos botões para chamar as funções Python expostas (`eel.start_monitoring`, `eel.stop_monitoring`).
    -   Criar uma função JavaScript exposta com `@eel.expose` para receber os dados de latência enviados pelo Python.
    -   Atualizar o gráfico e os textos das estatísticas na tela cada vez que novos dados são recebidos.
-   [ ] Integrar uma biblioteca de gráficos JavaScript
    -   Escolher e configurar uma biblioteca (ex: Chart.js) para renderizar o gráfico de latência em tempo real.
EOF
echo "✅ Issue 'Módulo 3' criada."

# Issue 4: Módulo 4
gh issue create \
    --repo "$REPO" \
    --title "Módulo 4: Empacotamento" \
    --body-file - \
    --assignee "docg1701" \
    --label "epic,deployment,packaging" <<'EOF'
-   [ ] Configurar o PyInstaller para criar o executável
    -   Criar um script de build ou um arquivo `.spec` que instrua o PyInstaller a agrupar o script Python junto com a pasta do frontend (contendo HTML, CSS, JS e a biblioteca de gráfico) em um único executável.
EOF
echo "✅ Issue 'Módulo 4' criada."

echo "----------------------------------------------------"
echo "🎉 Processo concluído!"
