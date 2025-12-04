# Relatório de Migração: Electron para Tauri

**Data:** 04/12/2025
**Autor:** Codebase Investigator & Architect Agent
**Assunto:** Redução drástica do tamanho do executável Desktop e otimização de recursos.

## 1. O Problema Atual
O aplicativo "NetMonitor", em sua versão Desktop para Linux, gerou um executável (`.AppImage`) de **132 MB**.
Este tamanho é desproporcional para a complexidade da aplicação (monitoramento simples de latência via HTTP).

### A Causa (Análise Técnica)
A arquitetura atual utiliza **Electron**. O Electron funciona empacotando dois componentes pesados junto com a sua aplicação:
1.  **Chromium:** Um navegador web completo (o motor do Google Chrome).
2.  **Node.js:** Um ambiente de execução JavaScript completo.

Independentemente de o seu código ter 1KB ou 1GB, o Electron adiciona uma "taxa base" de aproximadamente **100MB a 120MB** ao executável final apenas para existir.

## 2. A Solução Proposta: Tauri
**Tauri** é um framework moderno para construir binários pequenos e rápidos para as principais plataformas de desktop.

### Como funciona
Diferente do Electron, o Tauri **não empacota um navegador**. Ele utiliza a biblioteca de renderização web nativa do sistema operacional do usuário:
*   **Linux:** WebKitGTK (usado pelo GNOME/Epiphany).
*   **Windows:** WebView2 (usado pelo Edge/Windows 10/11).
*   **macOS:** WebKit (usado pelo Safari).

### Comparativo Direto

| Característica | Electron (Atual) | Tauri (Proposto) | Diferença |
| :--- | :--- | :--- | :--- |
| **Tamanho do Instalador** | ~132 MB | **~10 MB a 15 MB** | **Redução de ~90%** |
| **Uso de Memória (RAM)** | Alto (~200MB+) | Médio/Baixo | Mais eficiente |
| **Backend** | Node.js (JavaScript) | Rust | Rust é mais seguro e performático |
| **Segurança** | Média | Alta (Sandboxed por padrão) | Melhor isolamento |
| **Multiplataforma** | Sim | Sim | Igual |

## 3. Impacto no Projeto NetMonitor

### O que MUDARÁ
*   **Build System:** O processo de build para Desktop deixará de usar `electron-builder` e passará a usar `cargo tauri build`.
*   **Dependência de Compilação:** Será necessário ter o compilador da linguagem **Rust** instalado no ambiente de desenvolvimento (CI/CD ou máquina local).
*   **Configuração:** Arquivos de configuração do Electron (`electron/main.js`) serão descartados em favor do `src-tauri/tauri.conf.json`.

### O que NÃO MUDARÁ
*   **Código Frontend:** O código Angular (`src/app/*`), Ionic, gráficos (`chart.js`) e lógica de serviço (`HttpClient`) permanecem **intactos**. O Tauri apenas "serve" esse conteúdo.
*   **Android:** A versão Android continuará usando **Capacitor**. O Tauri substituirá apenas a camada Desktop (Electron).

## 4. Plano de Migração

1.  **Preparação do Ambiente:** Instalar Rust e dependências do sistema (bibliotecas GTK no Linux).
2.  **Inicialização:** Rodar `npm install @tauri-apps/cli` e `npx tauri init` na raiz do projeto.
3.  **Configuração:** Apontar o Tauri para a pasta `www` (onde o Angular gera o build).
4.  **Remoção do Electron:** Desinstalar dependências `electron` e `electron-builder`.
5.  **Build:** Compilar a nova versão e validar o tamanho e funcionalidade.

## 5. Conclusão
A migração para Tauri é a decisão técnica mais correta para utilitários leves como o NetMonitor. Ela elimina o "bloatware" (inchaço) do executável, respeita os recursos da máquina do usuário e mantém a mesma experiência de uso visual.

**Recomendação:** APROVADA.
