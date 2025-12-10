# Post-MVP Roadmap

Este documento descreve as funcionalidades planejadas para implementação após o MVP do NetMonitor.

## Visão Geral

O app será organizado em uma estrutura de abas:

1. **Aba Monitor** - Monitoramento em tempo real (atual)
2. **Aba Configurações** - Parâmetros de monitoramento
3. **Aba Relatórios** - Gestão de dados e exportação

---

## Fases de Implementação

### Fase 1: Persistência com SQLite

**Objetivo:** Armazenar dados de ping para análise posterior.

#### Tecnologias

| Plataforma | Pacote | Versão |
|------------|--------|--------|
| Tauri (Desktop) | `@tauri-apps/plugin-sql` | 2.3.x |
| Tauri (Rust) | `tauri-plugin-sql` | 2.3.1 |
| Capacitor (Mobile) | `@capacitor-community/sqlite` | 7.x |

#### Schema do Banco

```sql
CREATE TABLE pings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    latency_ms REAL,
    success INTEGER NOT NULL,
    target TEXT NOT NULL
);

CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX idx_pings_timestamp ON pings(timestamp);
```

#### Instalação

**Tauri (Cargo.toml):**
```toml
[dependencies]
tauri-plugin-sql = { version = "2", features = ["sqlite"] }
```

**Capacitor:**
```bash
npm install @capacitor-community/sqlite@^7.0.0
npx cap sync
```

---

### Fase 2: Aba Configurações

#### Configurações de Monitoramento

| Configuração | Descrição | Padrão |
|--------------|-----------|--------|
| Ping Target | IP ou hostname para testes | `8.8.8.8` |
| Intervalo | Segundos entre pings | `5` |

#### Dados do Usuário (para relatório)

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| Nome completo | Titular da conexão | João da Silva |
| Documento | CPF ou CNPJ | 123.456.789-00 |
| Endereço | Local da conexão | Rua X, 123 - Cidade/UF |

#### Dados da Conexão (para relatório)

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| Operadora | Nome do provedor | Vivo Fibra |
| Plano | Nome do plano contratado | Fibra 300 Mbps |
| Velocidade | Mbps contratados | 300 |
| Tipo | Fibra, Cabo, DSL, etc. | Fibra Óptica |

**Funcionalidades:**
- Validação de IP/hostname e CPF
- Persistência no SQLite
- Restaurar valores padrão
- Campos opcionais não bloqueiam uso do app

---

### Fase 3: Aba Relatórios

#### Estatísticas Exibidas
- Período de monitoramento (início/fim)
- Total de pings realizados
- Uptime (%)
- Latência média/mínima/máxima
- Número de quedas detectadas
- Tempo total offline

#### Ações
- **Limpar Dados** - Remove todos os registros (com confirmação)
- **Exportar para IA** - Gera JSON + prompt otimizado

---

## Exportação para IA (LLMs)

Em vez de gerar relatórios PDF complexos no app, exportamos dados estruturados + prompt para que ChatGPT, Claude ou Gemini gerem os gráficos e documentos.

### Formato de Exportação

```json
{
  "app": "NetMonitor",
  "version": "1.x.x",
  "export_date": "2025-12-10T10:00:00Z",

  "user_info": {
    "name": "João da Silva",
    "document": "CPF: 123.456.789-00",
    "address": "Rua Example, 123 - Bairro - Cidade/UF",
    "coordinates": {
      "latitude": -23.5505,
      "longitude": -46.6333,
      "accuracy_meters": 10
    }
  },

  "connection_info": {
    "provider": "Operadora XYZ",
    "plan": "Fibra 300 Mbps",
    "contract_speed_mbps": 300,
    "public_ip": "189.45.123.67",
    "ip_collected_at": "2025-12-10T10:00:00Z",
    "connection_type": "Fibra Óptica"
  },

  "period": {
    "start": "2025-12-01T00:00:00Z",
    "end": "2025-12-10T10:00:00Z"
  },

  "summary": {
    "total_pings": 15234,
    "successful": 14987,
    "failed": 247,
    "uptime_percent": 98.38,
    "avg_latency_ms": 45.2,
    "min_latency_ms": 12,
    "max_latency_ms": 890,
    "total_downtime_minutes": 23.5
  },

  "outages": [
    {
      "start": "2025-12-05T14:23:00Z",
      "end": "2025-12-05T14:28:12Z",
      "duration_minutes": 5.2,
      "public_ip_before": "189.45.123.67",
      "public_ip_after": "189.45.124.12"
    }
  ],

  "hourly_summary": [
    {"hour": "2025-12-10T00:00:00Z", "avg_latency": 42.1, "success_rate": 100},
    {"hour": "2025-12-10T01:00:00Z", "avg_latency": 38.5, "success_rate": 98.3}
  ]
}
```

### Dados do Usuário e Conexão

#### Informações Coletadas

| Dado | Origem | Obrigatório |
|------|--------|-------------|
| Nome completo | Input do usuário | Sim |
| CPF/Documento | Input do usuário | Sim |
| Endereço | Input do usuário | Sim |
| Coordenadas GPS | Geolocation API (mobile) | Não |
| Nome da operadora | Input do usuário | Sim |
| Plano contratado | Input do usuário | Sim |
| Velocidade contratada | Input do usuário | Sim |
| IP público | API externa (ipify.org) | Automático |

#### Coleta de IP Público

O app consulta periodicamente o IP público para:
- Registrar mudanças de IP (útil para identificar reconexões)
- Documentar o IP no momento de cada queda
- Provar que a conexão é do endereço declarado

**API sugerida:**
```typescript
// Gratuita, sem limite, HTTPS
const response = await fetch('https://api.ipify.org?format=json');
const { ip } = await response.json();
```

#### Geolocalização (Mobile)

No Android, solicitar permissão de localização para:
- Confirmar que o monitoramento é do endereço declarado
- Adicionar coordenadas GPS ao relatório (prova técnica)

```typescript
// Capacitor Geolocation
import { Geolocation } from '@capacitor/geolocation';
const position = await Geolocation.getCurrentPosition();
```

### Fluxo do Usuário

1. Abre aba Relatórios
2. Clica em "Exportar para IA"
3. App gera 2 arquivos para download:
   - `netmonitor_dados.json` (dados de monitoramento)
   - `netmonitor_prompt.txt` (prompt + instruções)
4. Usuário acessa ChatGPT/Claude/Gemini
5. Anexa o arquivo JSON
6. Cola o prompt
7. IA gera relatório completo com gráficos e documentos

### Arquivos Exportados

#### 1. `netmonitor_dados.json`
Contém todos os dados de monitoramento em formato JSON (estrutura mostrada acima).

#### 2. `netmonitor_prompt.txt`
Contém as instruções e o prompt para a IA:

```
═══════════════════════════════════════════════════════════════
              NETMONITOR - EXPORTAÇÃO PARA IA
═══════════════════════════════════════════════════════════════

COMO USAR:

1. Acesse um chatbot de IA:
   • ChatGPT Plus: https://chat.openai.com (GPT-4 recomendado)
   • Claude Pro: https://claude.ai
   • Gemini Advanced: https://gemini.google.com

2. Inicie uma nova conversa

3. ANEXE o arquivo "netmonitor_dados.json"

4. COLE o prompt abaixo e envie:

═══════════════════════════════════════════════════════════════
                         PROMPT
═══════════════════════════════════════════════════════════════

Você é um especialista em telecomunicações e direito do
consumidor brasileiro.

Analise os dados de monitoramento de conexão de internet
no arquivo JSON anexado e gere:

1. **Relatório Técnico** com gráficos:
   - Gráfico de linha: latência ao longo do tempo
   - Gráfico de barras: quedas por dia
   - Resumo estatístico formatado

2. **Análise de SLA**:
   - Compare com padrões aceitáveis (99.5% uptime, <100ms)
   - Identifique violações de qualidade
   - Calcule tempo total de indisponibilidade

3. **Documentos para Reclamação** (se aplicável):
   - Texto para reclamação no PROCON
   - Texto para reclamação na ANATEL
   - Modelo de notificação extrajudicial

Use os dados do usuário e da conexão presentes no arquivo
para personalizar os documentos gerados.

═══════════════════════════════════════════════════════════════
```

---

### Fase 4: Melhorias de UX

#### Cartão de Uptime
Na tela principal, exibir há quanto tempo o app está monitorando:
```
Monitorando há: 2h 34m 12s
```

> **Nota:** O app só monitora enquanto está em primeiro plano (tela ativa).
> Não há serviço em background nem notificações push.

---

### Fase 5: Futuro (Opcional)

- Widget de status para home screen
- Histórico visual simples de quedas
- Temas claro/escuro

---

## Referências

- [Tauri SQL Plugin](https://v2.tauri.app/plugin/sql/)
- [Capacitor SQLite](https://github.com/capacitor-community/sqlite)
- [Regulamento ANATEL](https://www.anatel.gov.br)
- [Código de Defesa do Consumidor](http://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm)
