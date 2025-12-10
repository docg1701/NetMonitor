# Post-MVP Roadmap

Este documento descreve as funcionalidades planejadas para implementação após o MVP do NetMonitor.

## Visão Geral

O app atual será reorganizado em uma estrutura de abas para melhor organização e usabilidade:

1. **Aba Monitor** - App atual de monitoramento
2. **Aba Configurações** - Parâmetros de monitoramento
3. **Aba Relatórios** - Gestão de dados e geração de relatórios

---

## 1. Aba Monitor (Principal)

Mantém a funcionalidade atual do app:
- Visualização em tempo real do status da conexão
- Gráfico de latência
- Indicadores de qualidade da rede

### 1.1 Novo: Cartão de Uptime

Exibe há quanto tempo o aplicativo está rodando (ex: "2h 34m 12s").

---

## 2. Aba Configurações

### 2.1 Configurações de Ping

| Configuração | Descrição | Valor Padrão |
|--------------|-----------|--------------|
| **Ping Target** | Endereço IP ou hostname para os testes de conectividade | `8.8.8.8` |
| **Intervalo entre Pings** | Tempo em segundos entre cada teste | `5s` |

### 2.2 Funcionalidades

- Validação de endereços IP/hostname
- Preview do target antes de salvar
- Opção de restaurar valores padrão
- Persistência das configurações

---

## 3. Aba Relatórios

### 3.1 Gestão de Dados

#### Informações Exibidas
- **Período armazenado**: Data/hora do primeiro e último registro
- **Total de registros**: Quantidade de pings armazenados
- **Espaço ocupado**: Tamanho do banco de dados em disco

#### Ações Disponíveis
- **Limpar Dados**: Remove todos os registros históricos (com confirmação)
- **Exportar Relatório**: Gera relatório completo para download

### 3.2 Relatório Completo para Reclamação Formal

O relatório exportado deve conter tudo necessário para fundamentar uma reclamação formal ou processo contra o provedor de internet.

#### 3.2.1 Conteúdo do Relatório

**Seção 1: Resumo Executivo**
- Período de análise
- Percentual de disponibilidade da conexão
- Tempo total de indisponibilidade
- Quantidade de quedas detectadas
- Latência média, mínima e máxima

**Seção 2: Análise Detalhada**
- Gráficos de latência ao longo do tempo
- Histograma de distribuição de latência
- Timeline de quedas de conexão
- Análise de horários de pico de problemas
- Comparativo com padrões aceitáveis de mercado

**Seção 3: Documentação Legal**
- Dados técnicos formatados como evidência
- Registro cronológico de todas as falhas
- Cálculo de SLA (Service Level Agreement) não cumprido
- Referências às normas da ANATEL

**Seção 4: Materiais para Reclamação**
- Texto base para reclamação em órgãos de defesa do consumidor (PROCON)
- Texto base para reclamação na ANATEL
- Prompts otimizados para ChatGPT gerar:
  - Carta formal de reclamação
  - Notificação extrajudicial
  - Petição para juizado especial
- Checklist de documentos necessários

#### 3.2.2 Formatos de Exportação

| Formato | Conteúdo |
|---------|----------|
| **PDF** | Relatório completo formatado para impressão |
| **CSV** | Dados brutos para análise própria |
| **JSON** | Dados estruturados para integração |

#### 3.2.3 Gráficos Incluídos

1. **Gráfico de Linha**: Latência ao longo do tempo
2. **Gráfico de Barras**: Quantidade de quedas por dia/semana
3. **Gráfico de Pizza**: Distribuição de qualidade (Ótimo/Bom/Ruim/Offline)
4. **Heatmap**: Horários com mais problemas (dia da semana x hora)
5. **Timeline**: Visualização de eventos de queda

---

## Considerações Técnicas

### Armazenamento
- Implementar rotação automática de logs antigos
- Compressão de dados históricos
- Limite configurável de retenção

### Performance
- Lazy loading dos gráficos na aba de relatórios
- Geração assíncrona de relatórios grandes
- Cache de cálculos estatísticos

### UX
- Indicador de progresso durante geração de relatório
- Preview do relatório antes de exportar
- Notificação quando relatório estiver pronto

---

## Priorização Sugerida

1. **Fase 1**: Estrutura de abas + Configurações básicas
2. **Fase 2**: Gestão de dados (visualização + limpeza)
3. **Fase 3**: Relatório básico (PDF com estatísticas)
4. **Fase 4**: Relatório avançado (gráficos + materiais para reclamação)
5. **Fase 5**: Prompts para IA e documentos legais

---

## Referências

- [Regulamento Geral de Direitos do Consumidor de Telecomunicações - ANATEL](https://www.anatel.gov.br)
- [Código de Defesa do Consumidor - Lei 8.078/90](http://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm)
