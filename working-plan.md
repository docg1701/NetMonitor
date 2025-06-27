# Plano de Trabalho: monitor_net-web

**Versão:** 1.0
**Última Atualização:** 2025-06-26

## 1. Visão Geral e Objetivos (The "Why")

O objetivo do projeto 'monitor_net-web' é evoluir a atual ferramenta de linha de comando para uma aplicação web acessível e amigável. A motivação principal é superar as restrições da interface CLI, tornando o monitoramento de latência de rede disponível para um público mais amplo, incluindo usuários não-técnicos. A nova interface web será projetada para ser visualmente atraente, leve e responsiva, garantindo uma experiência de uso fluida em qualquer dispositivo, desde desktops a celulares. O problema central que se resolve é a barreira de entrada da ferramenta atual, oferecendo uma solução intuitiva que não exige familiaridade com o terminal.

Como indicadores de sucesso, definimos:
1.  Acessibilidade Universal: A interface é plenamente funcional em navegadores modernos (Chrome, Firefox, Safari) em desktops e dispositivos móveis.
2.  Experiência Intuitiva: Um novo usuário consegue iniciar um monitoramento com, no máximo, 2 cliques, sem necessidade de ler um manual.
3.  Visualização Clara: O gráfico de latência em tempo real é o elemento central da página e atualiza de forma clara e contínua, assim como na versão CLI.

## 2. Escopo do Projeto

### 2.1. Funcionalidades Incluídas (In-Scope)

* Um campo para o usuário digitar o host que deseja monitorar.
* Um botão de "Iniciar/Parar" o monitoramento.
* A visualização do gráfico de latência em tempo real.
* Uma área para exibir as estatísticas básicas (latência atual, média, mín, máx).

### 2.2. Funcionalidades Excluídas (Out-of-Scope)

* Salvar o histórico de monitoramentos de vários dias para comparação.

## 3. Equipe e Partes Interessadas (The "Who")

| Papel | Nome | Contato |
| :--- | :--- | :--- |
| Dono do Produto (PO) | docg1701 | GitHub |
| Líder Técnico (Tech Lead) | docg1701 | GitHub |
| Desenvolvedor(a) | Gemini-CLI | N/A |

## 4. Arquitetura e Pilha Tecnológica (The "How")

* Frontend: HTML5, CSS3, JavaScript (Vanilla). Será usada uma biblioteca de gráficos como `Chart.js`.
* Backend: Python 3. O script `monitor_net.py` será o núcleo. Usaremos a biblioteca Eel para criar a ponte entre o Python e a interface web.
* Banco de Dados: N/A (Não aplicável).
* Infraestrutura/Cloud: Aplicação Desktop Local.
* Autenticação: N/A (Não aplicável).
* Outros Serviços/Ferramentas: PyInstaller para empacotar o projeto em um executável de fácil distribuição.

## 5. Módulos e Funcionalidades Detalhadas (The "What")

-   [ ] Módulo 1: Estrutura e Ponto de Entrada
    -   [ ] Configurar dependências do projeto
        -   Adicionar `eel` ao `pyproject.toml` para a comunicação da interface.
        -   Adicionar `pyinstaller` como uma dependência de desenvolvimento para empacotamento.
    -   [ ] Refatorar o ponto de entrada `main()` em `monitor_net.py`
        -   Adicionar análise de argumentos para detectar uma flag como `--cli` ou `--terminal`.
        -   Se a flag `--cli` estiver presente, o programa deve executar a lógica da interface de terminal existente.
        -   Se nenhuma flag for passada, o programa deve iniciar a interface web com Eel como padrão.
    -   [ ] Garantir que o script `netmonitor` funcione corretamente
        -   O comando `netmonitor` gerado pelo `pyproject.toml` deve executar a nova lógica do ponto de entrada.

-   [ ] Módulo 2: Backend (Lógica com Eel)
    -   [ ] Expor funções Python para o JavaScript via Eel
        -   Criar uma função Python, exposta com `@eel.expose`, para que o frontend possa solicitar o início/parada do monitoramento.
        -   Criar uma função que o frontend possa chamar para passar o nome do host a ser monitorado.
    -   [ ] Implementar o envio de dados em tempo real para o frontend
        -   Adaptar o loop de monitoramento para, a cada medição de latência, enviar os dados (latência, estatísticas) para uma função JavaScript no frontend.

-   [ ] Módulo 3: Frontend (Interface Web em HTML/CSS/JS)
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

-   [ ] Módulo 4: Empacotamento
    -   [ ] Configurar o PyInstaller para criar o executável
        -   Criar um script de build ou um arquivo `.spec` que instrua o PyInstaller a agrupar o script Python junto com a pasta do frontend (contendo HTML, CSS, JS e a biblioteca de gráfico) em um único executável.

## 6. Cronograma de Entregas (Milestones)

| Fase / Sprint | Módulo(s) Foco | Data de Conclusão Estimada |
| :--- | :--- | :--- |
| Fase 1: MVP | Módulos 1, 2 e 3 (Estrutura, Backend e Frontend) | 2025-07-06 |
| Fase 2 | Módulo 4 (Empacotamento) | 2025-07-11 |

## 7. Riscos e Planos de Mitigação

| Risco | Probabilidade (Baixa, Média, Alta) | Plano de Mitigação |
| :--- | :--- | :--- |
| A biblioteca Eel pode ter alguma limitação inesperada ou conflito. | Média | Pesquisar bibliotecas alternativas (como `pywebview`) como um plano B. |

## 8. Definição de "Pronto" (Definition of Done)

Uma tarefa ou funcionalidade é considerada "Pronta" quando todos os seguintes critérios são atendidos:
-   [ ] O código foi revisado pelo Líder Técnico (`docg1701`).
-   [ ] Testes unitários, se aplicáveis, foram implementados e estão passando.
-   [ ] A funcionalidade atende aos critérios de aceite definidos na sua issue.
-   [ ] A documentação relevante (como o `README.md`) foi atualizada para refletir as mudanças.
-   [ ] O código foi integrado à branch principal (ex: `main`).
