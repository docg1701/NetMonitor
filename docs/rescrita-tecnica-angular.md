# Arquivo: brief_technical_angular.md

## 1. Visão Geral do Projeto
**Nome:** NetMonitor Enterprise (Modernização)
**Objetivo:** Reconstruir a ferramenta de monitoramento de rede `monitor_net.py` como uma aplicação nativa multiplataforma (Android, Linux, Windows), priorizando estabilidade extrema, manutenção a longo prazo e zero dependências quebradas.
**Filosofia:** "The Boring Stack". Fugir do hype. Usar apenas tecnologias padronizadas, com "baterias inclusas" e tipagem estrita para eliminar ambiguidade e alucinações de IA.

## 2. Tech Stack: "Estabilidade Corporativa"

### 2.1 Framework Core (Frontend & Lógica)
* **Framework:** **Angular (Versão Stable Recente - v17+)**.
    * *Arquitetura:* **Standalone Components** (obrigatório). Nada de `NgModules` complexos.
    * *Linguagem:* **TypeScript** (Strict Mode ativado `strict: true`). Tipagem forte é mandatória para evitar erros de runtime e alucinações de parâmetros.
    * *Estilo:* **SCSS** modular com variáveis do Ionic.
* **UI Library:** **Ionic Framework (v7+)**.
    * *Justificativa:* Componentes de UI nativos (`<ion-header>`, `<ion-content>`, `<ion-card>`) pré-estilizados e responsivos. O modelo NÃO deve escrever CSS de layout manual, deve usar o Grid e Utilitários do Ionic para garantir consistência visual imediata.

### 2.2 Runtime & Build System
* **Mobile (Android):** **Capacitor (v5+)**.
    * *Função:* Container nativo para rodar o app web no Android.
    * *Configuração:* Gerar projeto Android Studio padrão (`android/`).
* **Desktop (Linux & Windows):** **Electron (LTS)**.
    * *Estratégia:* O Electron deve atuar apenas como um "wrapper" leve que carrega o `index.html` gerado pelo build de produção do Angular (`dist/` ou `www/`).
    * *Empacotamento:* **electron-builder**.
    * *Formatos:* `.AppImage` (Linux Universal) e `.exe` (Windows).

### 2.3 Bibliotecas Auxiliares (Allowlist)
* **Gráficos:** `ng2-charts` (wrapper oficial Angular) + `chart.js`.
* **Rede:** `HttpClient` (Nativo do Angular). **Proibido** usar Axios ou Fetch puro para manter a consistência do interceptor e tipagem do Angular.

## 3. Arquitetura da Aplicação

### 3.1 Estrutura de Pastas (Padrão Angular CLI)
```text
src/
├── app/
│   ├── models/
│   │   └── ping-result.interface.ts  # Interface estrita (timestamp: Date, latencyMs: number, status: 'ok'|'error')
│   ├── services/
│   │   └── monitor.service.ts        # Singleton. Contém a lógica de "Ping HTTP" e o Subject RxJS.
│   ├── home/
│   │   ├── home.page.ts              # Componente Standalone (Lógica da View).
│   │   ├── home.page.html            # Template com componentes Ionic.
│   │   └── home.page.scss            # Estilos locais.
│   └── app.component.ts              # Root.
├── electron/
│   └── main.js                       # Processo principal do Electron (Janela, Menu, Tray).
├── capacitor.config.ts               # Configuração Mobile.
└── angular.json
```

## 4. Lógica de Migração (Python -> TypeScript)

### 4.1 O Problema do Ping (Solução Cross-Platform)
O comando `ping` (ICMP) exige permissões de root no Android e varia entre distros Linux.
**Solução Obrigatória:** Implementar "Ping HTTP/TCP" (Head Request).
* **Mecanismo:** O `MonitorService` deve disparar requisições `HEAD` (ou `GET` leve com `observe: 'response'`) para o alvo (ex: `http://google.com` ou o IP alvo porta 80).
* **Cálculo:** `Latência = (Tempo Resposta - Tempo Início)`.
* **Vantagem:** Funciona **identicamente** no Android (via Capacitor), no Linux e no Windows sem permissões especiais, sem hacks de `child_process` e sem dependências nativas quebradas.

### 4.2 Serviço de Monitoramento (`monitor.service.ts`)
O modelo deve implementar:
1.  **State Management:** Usar `BehaviorSubject<PingResult[]>` para manter o histórico dos últimos 50 pings. Não usar Redux/NgRx.
2.  **Loop:** Usar o operador `timer` ou `interval` do **RxJS** para o polling. Isso garante cancelamento limpo (`unsubscribe`) e previne vazamento de memória.
3.  **Tratamento de Erro:** Se a requisição HTTP falhar (timeout/erro rede), registrar como "Perda de Pacote" (latência null ou flag de erro) e emitir o estado, sem quebrar a aplicação.

## 5. Instruções de Interface (UI/UX)
* **Tema:** Dark Mode obrigatório (padrão do Ionic).
* **Layout:**
    * **Topo:** Header com Título "NetMonitor" e Status (Online/Offline usando `ion-badge`).
    * **Centro:** Gráfico de Linha (`Chart.js`) ocupando a maior parte da tela.
    * **Abaixo:** Grid de Cards (`ion-card`) com estatísticas resumidas: Latência Atual, Média, Mín, Máx, Jitter.
    * **Rodapé:** Botão de ação (`ion-button` expand="block") para Iniciar/Parar.

## 6. Passo a Passo para o Agente (Action Plan)

1.  **Scaffolding:** Gerar o comando exato: `ionic start netmonitor blank --type=angular --capacitor`.
2.  **Lógica:** Escrever o `monitor.service.ts` importando `HttpClientModule`. Implementar a função `measureLatency(url: string)` usando `Date.now()`.
3.  **UI:** Escrever o `home.page.html` usando apenas tags do Ionic (`<ion-grid>`, `<ion-row>`, `<ion-col>`).
4.  **Desktop:** Criar o arquivo `electron/main.js` básico que carrega o arquivo `index.html` da pasta `www/` (ou `dist/`).
5.  **Scripts:** Adicionar ao `package.json`:
    * `"electron:start": "ng build && electron ."`
    * `"android:run": "ionic cap run android"`

## 7. Critérios de Aceite (DoR)
* O código deve compilar em modo estrito (`strict: true`) sem erros de tipagem.
* A lógica de rede deve ser puramente baseada em `HttpClient` (Web API), sem dependências de Node.js, para garantir funcionamento no Android.
* O app deve rodar no Android (via Capacitor) e no Desktop (via Electron) compartilhando 100% da lógica de negócio.
