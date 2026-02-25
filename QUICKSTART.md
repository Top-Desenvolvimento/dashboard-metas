# ⚡ Início Rápido - Dashboard Automatizado

## 🎯 O que você tem agora

Um sistema completo de dashboard que:
- 🤖 **Atualiza sozinho a cada hora**
- 📊 Coleta dados das 9 cidades automaticamente
- 🌐 Publica online via GitHub Pages
- ✅ Não precisa mais abrir chat com Manus!

---

## 📦 Arquivos Principais

```
dashboard-metas/
├── 📄 SETUP.md                    ← COMECE POR AQUI! (guia completo)
├── 📄 README.md                   ← Documentação do projeto
├── 🐍 extract_metas.py            ← Coleta dados dos sistemas
├── 🐍 generate_dashboard.py       ← Gera o HTML do dashboard
├── 📋 requirements.txt            ← Dependências Python
├── 🧪 test_local.sh               ← Teste antes de subir
│
├── .github/workflows/
│   └── update-dashboard.yml       ← Automação GitHub Actions
│
├── data/
│   └── metas_atual.json          ← Dados (exemplo incluído)
│
└── docs/
    └── index.html                ← Dashboard (exemplo incluído)
```

---

## 🚀 Como Configurar (Resumo)

### 1️⃣ Faça Upload no GitHub
- Acesse: https://github.com/Top-Desenvolvimento/dashboard-metas
- Upload de TODOS os arquivos desta pasta

### 2️⃣ Configure Secrets
Settings → Secrets → Actions
- `LOGIN_USER` = `MANUS`
- `LOGIN_PASS` = `MANUS2026`

### 3️⃣ Habilite Actions
Settings → Actions → General
- ✅ Allow all actions
- ✅ Read and write permissions

### 4️⃣ Configure Pages
Settings → Pages
- Branch: `gh-pages`
- Folder: `/` (root)

### 5️⃣ Execute!
Actions → "Atualizar Dashboard" → Run workflow

---

## 🎁 Bônus: Teste Local

Antes de subir, teste localmente:

```bash
bash test_local.sh
```

---

## 📱 Seu Dashboard Estará Aqui

```
https://top-desenvolvimento.github.io/dashboard-metas/
```

---

## ⏰ Horário de Atualização

O sistema roda automaticamente:
- **A cada hora** (00:00, 01:00, 02:00, ... 23:00)
- **24 horas por dia, 7 dias por semana**
- **Sem precisar fazer nada!**

---

## 🔧 Personalizações Futuras

Você pode editar:

1. **Visual do dashboard:** `generate_dashboard.py`
2. **Como coleta dados:** `extract_metas.py`
3. **Frequência de atualização:** `.github/workflows/update-dashboard.yml`
   - Linha `cron: '0 * * * *'` (atualmente: a cada hora)
   - Para cada 30 min: `'*/30 * * * *'`
   - Para cada 6 horas: `'0 */6 * * *'`

---

## ❓ Dúvidas Comuns

**P: Preciso deixar meu computador ligado?**
R: NÃO! Tudo roda nos servidores do GitHub automaticamente.

**P: Como sei se está funcionando?**
R: Vá em Actions e veja o ✅ verde nas execuções.

**P: Posso mudar a senha?**
R: Sim! Settings → Secrets → Edite `LOGIN_PASS`

**P: E se der erro?**
R: Veja os logs em Actions. Eles mostram exatamente o que aconteceu.

---

## 📞 Checklist Final

- [ ] Upload feito no GitHub ✅
- [ ] 2 secrets configurados ✅
- [ ] GitHub Actions habilitado ✅
- [ ] GitHub Pages configurado ✅
- [ ] Primeira execução rodou ✅
- [ ] Dashboard online e funcionando ✅

---

## 🎉 Pronto!

Agora é só aproveitar! Seu dashboard está:
- ✅ Automatizado
- ✅ Sempre atualizado
- ✅ Acessível de qualquer lugar
- ✅ Rodando sozinho

**Nunca mais precisa pedir pro Manus atualizar! 🚀**

---

Para instruções detalhadas, veja **SETUP.md**
