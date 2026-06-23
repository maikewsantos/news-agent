# 📰 Agente de Notícias no WhatsApp

Manda "quais são as notícias de hoje?" no WhatsApp e recebe um briefing automático.

## Como funciona

```
Você (WhatsApp) → Twilio → Flask (webhook) → NewsAPI + Claude → resposta no WhatsApp
```

---

## Setup — passo a passo

### 1. Instalar dependências

```bash
cd news-agent
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Abra .env e preencha suas chaves
```

### 3. Configurar Twilio (WhatsApp Sandbox)

1. Crie conta em https://twilio.com (gratuito)
2. No console: **Messaging → Try it out → Send a WhatsApp message**
3. Siga as instruções para ativar o sandbox — você vai mandar uma mensagem como
   `join <palavra>` para o número do Twilio no WhatsApp
4. Deixe a tela aberta — você vai precisar do webhook URL em seguida

### 4. Rodar o servidor

```bash
python main.py
```

### 5. Expor o servidor com ngrok

Em outro terminal:

```bash
# Instala ngrok: https://ngrok.com/download
ngrok http 5000
```

Copie a URL que aparecer, ex: `https://abc123.ngrok-free.app`

### 6. Configurar webhook no Twilio

No console do Twilio (WhatsApp Sandbox), cole no campo
**"When a message comes in":**

```
https://abc123.ngrok-free.app/webhook
```

Método: `HTTP POST` → Salvar.

### 7. Testar

Mande no WhatsApp para o número do Twilio:
> quais são as notícias de hoje?

---

## Estrutura do projeto

```
news-agent/
├── main.py          # Servidor Flask + lógica do agente
├── requirements.txt
├── .env.example     # Template de variáveis de ambiente
└── README.md
```

## Notas

- **Sandbox Twilio**: funciona para testes, mas o número expira se não usado.
  Para produção, você precisaria de um número Twilio pago + aprovação Meta.
- **ngrok gratuito**: a URL muda a cada reinicialização. Para URL fixa, use
  a versão paga do ngrok ou deploy em Railway/Render.
- **NewsAPI gratuito**: limitado a 100 requests/dia e não inclui conteúdo
  completo dos artigos (só título + descrição).
