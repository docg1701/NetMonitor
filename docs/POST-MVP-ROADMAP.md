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

#### País/Região

| Opção | Órgão de Reclamação | Legislação |
|-------|---------------------|------------|
| 🇧🇷 Brasil | ANATEL, PROCON | CDC, Marco Civil |
| 🇺🇸 Estados Unidos | FCC, State Attorney General | FCC Rules, State Consumer Laws |
| 🇪🇺 União Europeia | National Telecom Authority | EECC, GDPR |
| 🇬🇧 Reino Unido | Ofcom, Ombudsman Services | Communications Act 2003 |

#### Dados do Usuário (para relatório)

| Campo | Brasil | EUA | UE | UK |
|-------|--------|-----|----|----|
| Nome completo | ✓ | ✓ | ✓ | ✓ |
| Documento | CPF/CNPJ | SSN (opcional) | National ID | NIN (opcional) |
| Endereço | Rua, Cidade/UF | Street, City, State, ZIP | Street, City, Postal Code | Street, City, Postcode |
| Telefone | +55 | +1 | +XX | +44 |

#### Dados da Conexão (para relatório)

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| Operadora | Nome do provedor | Vivo / Comcast / BT / Orange |
| Plano | Nome do plano contratado | Fibra 300 Mbps |
| Velocidade | Mbps contratados | 300 |
| Tipo | Fibra, Cabo, DSL, etc. | Fibra Óptica |
| Número do contrato | Identificador do serviço | Opcional |

**Funcionalidades:**
- Seleção de país altera campos e validações
- Validação de documentos por país (CPF, etc.)
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

  "region": {
    "country_code": "BR",
    "country_name": "Brasil",
    "regulatory_body": "ANATEL",
    "consumer_protection": "PROCON",
    "applicable_law": "Código de Defesa do Consumidor, Marco Civil da Internet"
  },

  "user_info": {
    "name": "João da Silva",
    "document_type": "CPF",
    "document_number": "123.456.789-00",
    "phone": "+55 11 99999-9999",
    "address": {
      "street": "Rua Example, 123",
      "neighborhood": "Bairro",
      "city": "São Paulo",
      "state": "SP",
      "postal_code": "01234-567",
      "country": "Brasil"
    },
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
    "contract_number": "123456789",
    "public_ip": "189.45.123.67",
    "ip_collected_at": "2025-12-10T10:00:00Z",
    "connection_type": "Fiber"
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

You are an expert in telecommunications and consumer rights.

Analyze the internet connection monitoring data in the attached
JSON file. Note the "region" field to determine applicable laws
and regulatory bodies.

Generate:

1. **Technical Report** with charts:
   - Line chart: latency over time
   - Bar chart: outages per day
   - Statistical summary

2. **SLA Analysis**:
   - Compare against acceptable standards (99.5% uptime, <100ms)
   - Identify quality violations
   - Calculate total downtime

3. **Complaint Documents** (if issues found):

   FOR BRAZIL (BR):
   - Texto para reclamação no PROCON
   - Texto para reclamação na ANATEL
   - Notificação extrajudicial

   FOR USA (US):
   - FCC complaint text
   - State Attorney General complaint
   - Demand letter to provider

   FOR EU:
   - National Telecom Authority complaint
   - Consumer protection complaint (per country)
   - GDPR data request (if applicable)

   FOR UK (GB):
   - Ofcom complaint text
   - Ombudsman Services complaint
   - Letter before action

Use the user and connection data in the file to personalize
all generated documents. Write documents in the user's language
based on their country.

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

---

## Documentação Pública

O tutorial de uso com IA e o prompt serão publicados no repositório:

| Arquivo | Idioma | Conteúdo |
|---------|--------|----------|
| `docs/AI-EXPORT-GUIDE.md` | 🇬🇧 English | Guide for US, EU, UK users |
| `docs/AI-EXPORT-GUIDE.pt-BR.md` | 🇧🇷 Português | Guia para usuários brasileiros |

O app exporta o tutorial no idioma correspondente ao país selecionado:
- **Brasil** → Português brasileiro
- **EUA, UE, UK** → Inglês

Isso permite que usuários consultem as instruções sem precisar exportar dados primeiro.

---

## Referências

### Técnicas
- [Tauri SQL Plugin](https://v2.tauri.app/plugin/sql/)
- [Capacitor SQLite](https://github.com/capacitor-community/sqlite)

### Legislação por Região

**Brasil:**
- [ANATEL - Regulamentos](https://www.anatel.gov.br)
- [Código de Defesa do Consumidor](http://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm)

**Estados Unidos:**
- [FCC Consumer Complaints](https://consumercomplaints.fcc.gov)
- [FCC Rules on Internet Service](https://www.fcc.gov/consumers/guides)

**União Europeia:**
- [EECC - European Electronic Communications Code](https://digital-strategy.ec.europa.eu/en/policies/connectivity)
- [BEREC - Consumer Rights](https://www.berec.europa.eu)

**Reino Unido:**
- [Ofcom - Complaints](https://www.ofcom.org.uk/complaints)
- [Communications Act 2003](https://www.legislation.gov.uk/ukpga/2003/21)
