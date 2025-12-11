# 🔵 LinkedIn Profile Scraper & Auto Connect

**Ferramenta automatizada para extração de perfis do LinkedIn e envio de convites de conexão**

---

## 📋 Sobre o Projeto

O **LinkedIn Profile Scraper & Auto Connect** é uma aplicação web completa que automatiza duas tarefas principais:

1. **📊 Scraping de Perfis** - Extrai informações detalhadas de perfis do LinkedIn baseado em uma busca por profissão
2. **🌐 Conexão Automática** - Envia convites de conexão automaticamente para os perfis extraídos

### ✨ Destaques

- Interface web moderna e intuitiva
- Extração completa de dados dos perfis
- Download de perfis em PDF
- Envio automático de convites de conexão
- Monitoramento em tempo real do progresso
- Relatórios detalhados de resultados

---

## 🎯 Recursos

### 📊 Módulo de Scraping

- ✅ Busca por profissão/cargo
- ✅ Extração de dados completos:
  - Nome, headline e localização
  - Seção "Sobre"
  - Experiências profissionais
  - Formação acadêmica
  - Licenças e certificados
  - Competências (skills)
  - Idiomas
  - Projetos
  - Recomendações
- ✅ Download de perfis em PDF
- ✅ Exportação de dados em JSON
- ✅ Progresso em tempo real
- ✅ Modo headless ou visível

### 🌐 Módulo de Conexão Automática

- ✅ Upload de arquivo JSON (gerado pelo scraper)
- ✅ Envio automático de convites
- ✅ Validação de perfis antes de conectar
- ✅ Relatório detalhado de sucessos/falhas
- ✅ Tratamento inteligente de erros
- ✅ Delays aleatórios para evitar bloqueios

---

## 🚀 Instalação

### Pré-requisitos

- **Python 3.8+** instalado
- **Navegador Chromium** (instalado automaticamente pelo Playwright)
- Conta do **LinkedIn** válida

### Passo 1: Clone ou Baixe o Projeto

```bash
# Clone o repositório (se aplicável)
git clone <url-do-projeto>
cd linkedin-scraper

# OU crie a estrutura manualmente
mkdir linkedin-scraper
cd linkedin-scraper
```

### Passo 2: Estrutura de Pastas

Crie a seguinte estrutura:

```
linkedin-scraper/
│
├── app.py                    # Backend Flask
├── .env                      # Credenciais (criar)
├── requirements.txt          # Dependências (criar)
│
└── templates/
    └── index.html           # Frontend
```

### Passo 3: Instale as Dependências

Crie o arquivo `requirements.txt`:

```txt
flask==3.0.0
playwright==1.40.0
python-dotenv==1.0.0
```

Instale:

```bash
pip install -r requirements.txt
playwright install chromium
```

### Passo 4: Configure as Credenciais

Crie o arquivo `.env` na raiz:

```env
LINKEDIN_USER=seu_email@exemplo.com
LINKEDIN_PASS=sua_senha_aqui
```

> ⚠️ **IMPORTANTE**
> 
> - Nunca compartilhe este arquivo
> - Adicione `.env` ao `.gitignore`
> - Use uma senha forte e única

### Passo 5: Execute a Aplicação

```bash
python app.py
```

Acesse: **http://localhost:5000**

---

## 💡 Como Usar

### 🔍 Etapa 1: Scraping de Perfis

1. **Acesse a aba "Scraping"**
2. **Digite a profissão** que deseja buscar
   - Exemplos: "Desenvolvedor Python", "Analista de Dados", "Designer UI/UX"
3. **(Opcional)** Marque "Mostrar navegador"
4. **Clique em "Iniciar Busca"**
5. **Acompanhe o progresso**
6. **Baixe os resultados**:
   - 📄 JSON (.txt)
   - 📁 PDFs (.zip)

### 🤝 Etapa 2: Conexão Automática

1. **Acesse a aba "Conexão"**
2. **Faça upload** do JSON gerado
3. **Aguarde a validação**
4. **(Opcional)** Marque "Mostrar navegador"
5. **Clique em "Iniciar Conexões"**
6. **Acompanhe resultados**:
   - ✅ Sucessos
   - ❌ Falhas
   - ⚠️ Perfis pulados
7. **Relatório final disponível**

---

## 📊 Dados Extraídos

```json
{
  "name": "Nome Completo",
  "headline": "Cargo/Descrição",
  "location": "Cidade, País",
  "about": "Biografia completa...",
  "url": "https://linkedin.com/in/perfil",
  "experiences": [
    {
      "title": "Cargo",
      "company": "Empresa",
      "date_range": "jan 2020 - presente",
      "location": "Cidade",
      "description": "Descrição..."
    }
  ],
  "education": [],
  "certifications": [],
  "skills": ["Python", "JavaScript"],
  "languages": [],
  "projects": [],
  "recommendations_count": "10",
  "pdf_downloaded": true
}
```

---

## 🛡️ Segurança e Boas Práticas

### ⚠️ Avisos Importantes

- Use respeitando os **Termos de Serviço do LinkedIn**
- Evite scraping excessivo
- Não envie convites em massa
- Possível risco de **bloqueio temporário/permanente**

### 🔒 Recomendações

1. Utilize delays aleatórios
2. Não processe mais de **50–100 perfis/dia**
3. Varie horários
4. Use uma conta secundária
5. Evite mensagens padrão repetitivas

---

## 🔧 Troubleshooting

### ❗ "ModuleNotFoundError: No module named 'flask'"

```bash
pip install flask
```

### ❗ "Playwright não instalado"

```bash
playwright install chromium
```

### ❗ "Login failed" ou "Credenciais inválidas"

- Verifique o `.env`
- Confirme email e senha
- Desative 2FA temporariamente
- Verifique se há CAPTCHA

---

## 📁 Estrutura de Arquivos Gerados

```
linkedin-scraper/
│
├── linkedin_profiles/
│   ├── pdf_1_Nome_Pessoa.pdf
│   ├── pdf_2_Outro_Nome.pdf
│
├── temp_results/
│   ├── linkedin_profiles_123456.json
│   └── uploaded_789012.json
│
└── screenshots/
    └── error_pdf_download_1.png
```

---

## 🎨 Interface

- Layout moderno
- Design responsivo
- Gradiente azul estilo LinkedIn
- Ícones FontAwesome
- Animações suaves
- Barras de progresso
- Estatísticas em tempo real

---

## 📞 Suporte

- Consulte o Troubleshooting
- Verifique logs
- Abra uma Issue no repositório

---

## ⚖️ Disclaimer Legal

Ferramenta para uso educacional.

O uso deve estar em conformidade com:
- Termos do LinkedIn
- LGPD, GDPR e leis de privacidade

O autor **não se responsabiliza** por:
- Bloqueios
- Uso indevido
- Violações de termos
- Danos diretos ou indiretos

**Use com responsabilidade.**

---

**[⬆ Voltar ao topo](#-linkedin-profile-scraper--auto-connect)**
