# 🪟 Automação no Windows (sem GitHub Actions)

Se você quer que o dashboard **atualize sozinho no seu computador/servidor Windows** (sem depender de serviços externos), use o **Agendador de Tarefas**.

## ✅ Pré-requisitos

- **Python 3.11+** instalado e com o executável disponível (ex.: `python.exe`)
- Google Chrome instalado

Depois de instalar o Python:

```bat
python -m pip install -r requirements.txt
```

## ▶️ Rodar manualmente (teste)

Na pasta do projeto:

```bat
python update_all.py
```

Isso vai:
- coletar (`extract_metas.py`)
- exportar PPTX (`export_pptx.py`)
- gerar o HTML e copiar `data/` para `docs/` (`generate_dashboard.py`)

## ⏰ Criar a tarefa (Agendador de Tarefas)

1. Abra **Agendador de Tarefas**
2. Clique em **Criar Tarefa...**
3. Aba **Geral**
   - Nome: `Dashboard Metas - Atualizar`
   - Marque **Executar estando o usuário conectado ou não**
   - Marque **Executar com privilégios mais altos**
4. Aba **Disparadores**
   - **Novo...**
   - Iniciar a tarefa: **Em um agendamento**
   - Repetir a tarefa a cada: **1 hora**
   - Duração: **Indefinidamente**
5. Aba **Ações**
   - **Nova...**
   - Ação: **Iniciar um programa**
   - Programa/script: caminho do seu Python, por exemplo:
     - `C:\Python311\python.exe` (exemplo)  
   - Adicionar argumentos:
     - `update_all.py`
   - Iniciar em:
     - a pasta do projeto, por exemplo:
     - `C:\Users\Nicele Fagundes\Downloads\dashboard-metas`
6. Aba **Condições**
   - Desmarque “Iniciar a tarefa somente se o computador estiver na energia” se for notebook
7. Aba **Configurações**
   - Marque “Se a tarefa falhar, reiniciar a cada: 5 minutos (3 tentativas)”

## 🧾 Logs / Debug

- Log de execuções: `data/logs/update.log`
- Em falhas por cidade: `data/debug/*.png` e `data/debug/*.html`

## 🧩 Se o headless falhar

Em alguns ambientes Windows o Chrome headless pode dar problema.
Você pode desativar o headless configurando uma variável de ambiente na ação da tarefa:

- Variável: `HEADLESS`
- Valor: `0`

