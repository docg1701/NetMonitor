#!/bin/bash

# =================================================================
# Script para Criar Etiquetas do Projeto 'monitor_net-web'
# Gerado por: Gerente de Issues (Gemini)
# Data: 2025-06-26
# =================================================================

# --- Configuração ---
REPO="docg1701/monitor_net"

echo "Iniciando a criação de etiquetas no repositório: $REPO"
echo "----------------------------------------------------"

# --- Criação das Etiquetas ---
gh label create "epic" --repo "$REPO" --color "3A2066" --description "Uma issue grande que agrupa várias tarefas menores (um módulo)."
gh label create "setup" --repo "$REPO" --color "7057ff" --description "Tarefas relacionadas à configuração inicial do projeto ou ambiente."
gh label create "refactor" --repo "$REPO" --color "f0e442" --description "Melhora de código existente sem alterar a funcionalidade externa."
gh label create "cli" --repo "$REPO" --color "5319e7" --description "Relacionado à interface de linha de comando (Command Line Interface)."
gh label create "backend" --repo "$REPO" --color "f96213" --description "Tarefas relacionadas à lógica do servidor (Python/Eel)."
gh label create "python" --repo "$REPO" --color "3776AB" --description "Código ou tarefas específicas da linguagem Python."
gh label create "frontend" --repo "$REPO" --color "1386f9" --description "Tarefas relacionadas à interface do usuário (HTML/CSS/JS)."
gh label create "ui" --repo "$REPO" --color "d876e3" --description "Relacionado ao design e experiência visual da interface."
gh label create "javascript" --repo "$REPO" --color "F7DF1E" --description "Código ou tarefas específicas da linguagem JavaScript."
gh label create "deployment" --repo "$REPO" --color "006b75" --description "Tarefas relacionadas ao empacotamento e distribuição da aplicação."
gh label create "packaging" --repo "$REPO" --color "006b75" --description "Sinônimo para 'deployment'."

echo "----------------------------------------------------"
echo "🎉 Etiquetas criadas com sucesso!"
