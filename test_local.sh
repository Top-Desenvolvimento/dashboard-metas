# 🚀 Guia de Configuração - Passo a Passo

## ✅ Checklist de Configuração

Siga cada passo na ordem:

### 📦 Etapa 1: Fazer Upload dos Arquivos

1. Acesse seu repositório: https://github.com/Top-Desenvolvimento/dashboard-metas
2. Clique em **"Add file" → "Upload files"**
3. Arraste TODOS os arquivos e pastas deste projeto
4. Adicione uma mensagem de commit: `Configuração inicial do dashboard automatizado`
5. Clique em **"Commit changes"**

### 🔐 Etapa 2: Configurar Secrets (Credenciais)

1. No repositório, clique em **Settings** (⚙️)
2. No menu lateral, clique em **Secrets and variables → Actions**
3. Clique em **"New repository secret"**
4. Adicione o primeiro secret:
   - Name: `LOGIN_USER`
   - Secret: `MANUS`
   - Clique em **"Add secret"**
5. Clique novamente em **"New repository secret"**
6. Adicione o segundo secret:
   - Name: `LOGIN_PASS`
   - Secret: `MANUS2026`
   - Clique em **"Add secret"**

✅ **Resultado esperado:** Você deve ter 2 secrets configurados

### ⚙️ Etapa 3: Habilitar GitHub Actions

1. Ainda em **Settings**, clique em **Actions → General**
2. Em **"Actions permissions"**, selecione:
   - ✅ **"Allow all actions and reusable workflows"**
3. Em **"Workflow permissions"**, selecione:
   - ✅ **"Read and write permissions"**
   - ✅ Marque **"Allow GitHub Actions to create and approve pull requests"**
4. Clique em **Save** no final da página

✅ **Resultado esperado:** GitHub Actions está habilitado

### 🌐 Etapa 4: Configurar GitHub Pages

1. Ainda em **Settings**, clique em **Pages**
2. Em **"Source"**, selecione:
   - Branch: **gh-pages**
   - Folder: **/ (root)**
3. Clique em **Save**

⚠️ **Importante:** A branch `gh-pages` será criada automaticamente na primeira execução do workflow

✅ **Resultado esperado:** GitHub Pages configurado (pode mostrar erro inicialmente, é normal)

### ▶️ Etapa 5: Executar pela Primeira Vez

1. Clique na aba **Actions** (no topo do repositório)
2. No menu lateral esquerdo, clique em **"Atualizar Dashboard - A cada hora"**
3. Clique no botão **"Run workflow"** (canto superior direito)
4. Clique em **"Run workflow"** novamente no popup

⏱️ **Aguarde:** A execução leva cerca de 3-5 minutos

✅ **Resultado esperado:** 
- Workflow aparece com status ✅ verde (sucesso)
- Branch `gh-pages` é criada automaticamente

### 🎉 Etapa 6: Acessar seu Dashboard

Após o workflow terminar com sucesso:

1. Volte em **Settings → Pages**
2. Você verá uma mensagem: **"Your site is live at..."**
3. O endereço será: `https://top-desenvolvimento.github.io/dashboard-metas/`
4. Clique no link ou acesse diretamente

✅ **Resultado esperado:** Dashboard funcionando!

---

## 🔄 Funcionamento Automático

Após a configuração, o sistema funciona assim:

- ⏰ **A cada hora:** GitHub Actions executa automaticamente
- 🤖 **Coleta dados:** Script acessa os 9 sistemas
- 📊 **Atualiza dashboard:** Gera novo HTML
- 🚀 **Deploy:** Publica no GitHub Pages

Você não precisa fazer NADA! O dashboard atualiza sozinho.

---

## 🛠️ Executar Manualmente (Quando Precisar)

Se quiser forçar uma atualização imediata:

1. Vá em **Actions**
2. Clique no workflow **"Atualizar Dashboard - A cada hora"**
3. Clique em **"Run workflow"**
4. Aguarde 3-5 minutos

---

## ⚠️ Solução de Problemas

### ❌ Workflow falha com erro de permissão
**Solução:** Verifique Etapa 3 - Workflow permissions devem estar em "Read and write"

### ❌ Dashboard não aparece
**Solução:** 
1. Aguarde 5-10 minutos após primeiro workflow
2. Verifique se branch `gh-pages` foi criada
3. Force um hard refresh: Ctrl+Shift+R (Windows) ou Cmd+Shift+R (Mac)

### ❌ Erro "secrets not found"
**Solução:** Verifique Etapa 2 - Os nomes dos secrets devem ser exatamente `LOGIN_USER` e `LOGIN_PASS`

### ❌ Erro de login no sistema
**Solução:** 
1. Verifique se as credenciais em Secrets estão corretas
2. Teste fazer login manual no sistema
3. Veja os logs em Actions para detalhes

---

## 📋 Verificação Final

Marque cada item quando completar:

- [ ] Arquivos enviados para o GitHub
- [ ] 2 secrets configurados (LOGIN_USER e LOGIN_PASS)
- [ ] GitHub Actions habilitado com permissões
- [ ] GitHub Pages configurado
- [ ] Primeiro workflow executado com sucesso
- [ ] Dashboard acessível e funcionando
- [ ] Dados aparecendo corretamente

---

## 🎯 Próximos Passos

Depois de tudo configurado:

1. **Personalize o dashboard** - Edite `generate_dashboard.py` para ajustar visual
2. **Ajuste o script de coleta** - Edite `extract_metas.py` para melhorar a extração
3. **Monitore os logs** - Acesse Actions regularmente para ver se está tudo ok
4. **Adicione mais funcionalidades** - Gráficos, relatórios, etc.

---

## 📞 Precisa de Ajuda?

1. Verifique os **logs em Actions** - eles mostram exatamente o que aconteceu
2. Revise este guia - 90% dos problemas são etapas puladas
3. Verifique as **Issues** do repositório

---

**🎉 Parabéns! Seu dashboard está automatizado!**

Agora você tem um sistema que:
- ✅ Coleta dados automaticamente
- ✅ Atualiza a cada hora
- ✅ Não precisa de intervenção manual
- ✅ Está sempre disponível online

**Aproveite!** 🚀
