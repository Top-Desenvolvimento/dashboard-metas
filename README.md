# 📊 Dashboard de Metas - Top Estética Bucal

Dashboard automatizado para acompanhamento de metas das 9 unidades da Top Estética Bucal.

## 🚀 Funcionalidades

- ✅ Coleta automática de dados a cada hora
- 📈 Metas financeiras (Ortodontia e Clínico Geral)
- 🦷 Metas de serviços (Profilaxia e Restauração)
- ⭐ Avaliações do Google
- 📊 Dashboard interativo atualizado em tempo real
- 🤖 Totalmente automatizado via GitHub Actions
- 🗂️ Histórico mensal com seletor de mês
- 🏷️ Destaque visual para metas batidas (≥ 100% em algum segmento)
- 📥 Exportação mensal em PPTX

## 🏙️ Unidades Monitoradas

1. Caxias do Sul
2. Farroupilha
3. Bento Gonçalves
4. Encantado
5. Soledade
6. Garibaldi
7. Veranópolis
8. São Sebastião do Caí
9. Flores da Cunha

## ⚙️ Configuração no GitHub

### Passo 1: Configurar Secrets

No GitHub, vá em **Settings → Secrets and variables → Actions** e adicione:

- `LOGIN_USER`: usuário para login no sistema (valor: `MANUS`)
- `LOGIN_PASS`: senha para login no sistema (valor: `MANUS2026`)

### Passo 2: Habilitar GitHub Actions

1. Vá em **Settings → Actions → General**
2. Em "Actions permissions", selecione **Allow all actions and reusable workflows**
3. Em "Workflow permissions", selecione **Read and write permissions**
4. Marque **Allow GitHub Actions to create and approve pull requests**
5. Clique em **Save**

### Passo 3: Habilitar GitHub Pages

1. Vá em **Settings → Pages**
2. Em "Source", selecione **Deploy from a branch**
3. Em "Branch", selecione **gh-pages** e pasta **/ (root)**
4. Clique em **Save**

### Passo 4: Executar pela primeira vez

1. Vá em **Actions**
2. Selecione o workflow **"Atualizar Dashboard - A cada hora"**
3. Clique em **Run workflow → Run workflow**

Aguarde alguns minutos e seu dashboard estará disponível em:
```
https://Top-Desenvolvimento.github.io/dashboard-metas/
```

## 📅 Agendamento

O dashboard é atualizado automaticamente:
- **A cada hora** (de hora em hora, 24/7)
- Também pode ser executado **manualmente** via GitHub Actions

## 📁 Estrutura do Projeto

```
dashboard-metas/
├── .github/
│   └── workflows/
│       └── update-dashboard.yml    # Workflow de automação
├── data/
│   ├── metas_atual.json           # Dados atuais (JSON)
│   ├── historico_metas.csv        # Histórico completo
│   └── metas_top_estetica.xlsx    # Planilha formatada
├── docs/
│   └── index.html                 # Dashboard (GitHub Pages)
├── extract_metas.py               # Script de coleta
├── generate_dashboard.py          # Gerador de HTML
├── requirements.txt               # Dependências Python
└── README.md                      # Este arquivo
```

## 🔧 Desenvolvimento Local

Para testar localmente:

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
export LOGIN_USER="MANUS"
export LOGIN_PASS="MANUS2026"

# Executar coleta
python3 extract_metas.py

# Gerar dashboard
python3 generate_dashboard.py

# Visualizar
open docs/index.html
```

## 📊 Dados Coletados

### Metas Financeiras
- Ortodontia (valor em R$)
- Clínico Geral (valor em R$)

### Metas de Serviços
- Profilaxia (quantidade)
- Restauração (quantidade)

### Avaliações Google
- Total de avaliações atuais
- Novas avaliações desde o início da meta
- Valores iniciais por cidade (baseline mensal editável)

## 🛠️ Admin (baseline mensal do Google)

Para editar o baseline do mês (valor “inicial” das avaliações por cidade), use:

- `docs/admin.html`

Ela permite baixar um `google_baselines.json` atualizado para você substituir em `data/google_baselines.json` (ou subir para o repositório, se estiver usando Pages).

## 📥 Exportação (PPTX)

O arquivo é gerado em:

- `data/exports/YYYY-MM/dashboard_metas_YYYY-MM_latest.pptx`
- e também em `docs/exports/YYYY-MM/dashboard_metas_YYYY-MM_latest.pptx` (para download no site)

## 🪟 Automação no Windows (sem “créditos”)

Se você quer que rode no seu Windows sem GitHub Actions, veja:

- `WINDOWS_TASK_SCHEDULER.md`

## 🛠️ Tecnologias

- **Python 3.11** - Coleta e processamento
- **Selenium** - Automação web
- **Pandas** - Manipulação de dados
- **GitHub Actions** - Automação CI/CD
- **GitHub Pages** - Hospedagem

## 📝 Logs e Monitoramento

Acesse **Actions** no GitHub para ver:
- Status de cada execução
- Logs detalhados de coleta
- Histórico de atualizações

## ⚠️ Troubleshooting

### Dashboard não atualiza
- Verifique se os Secrets estão configurados corretamente
- Confira os logs em Actions
- Verifique se GitHub Pages está ativo

### Erro de login
- Confirme usuário e senha nos Secrets
- Verifique se o sistema está acessível

### Chrome/ChromeDriver error
- O workflow instala automaticamente
- Logs em Actions mostrarão detalhes

## 🤝 Suporte

Para problemas ou dúvidas:
1. Verifique os logs em **Actions**
2. Revise as configurações em **Settings**
3. Contate o administrador do sistema

## 📄 Licença

Uso interno - Top Estética Bucal

---

**Última atualização:** Fevereiro 2026
**Desenvolvido com** ❤️ **e automação**
