import os
import requests
import anthropic
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Palavras que ativam o agente
GATILHOS = [
    "notícia", "noticias", "noticia",
    "news", "hoje", "o que aconteceu",
    "briefing", "resumo", "manchete"
]

def é_pedido_de_notícias(texto: str) -> bool:
    t = texto.lower()
    return any(g in t for g in GATILHOS)

def buscar_artigos() -> list[dict]:
    """Busca top headlines do Brasil via NewsAPI."""
    r = requests.get(
        "https://newsapi.org/v2/top-headlines",
        params={
            "country": "br",
            "pageSize": 8,
            "apiKey": os.getenv("NEWSAPI_KEY"),
        },
        timeout=10,
    )
    data = r.json()

    if data.get("status") != "ok":
        raise RuntimeError(f"NewsAPI: {data.get('message', 'erro desconhecido')}")

    return [
        a for a in data.get("articles", [])
        if a.get("title") and "[Removed]" not in a["title"]
    ]

def formatar_briefing(artigos: list[dict]) -> str:
    """Usa Claude para transformar artigos brutos em briefing estilo WhatsApp."""
    lista = "\n".join(
        f"• {a['title']} | {a['source']['name']} | {a['url']}"
        for a in artigos
    )

    resposta = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=700,
        messages=[{
            "role": "user",
            "content": f"""Crie um briefing de notícias para WhatsApp a partir dos artigos abaixo.

Formato obrigatório:
- Linha 1: "📰 *Notícias de hoje* — [data de hoje]"
- Em seguida, 4-5 destaques numerados, cada um com emoji relevante e 1 frase concisa
- Linha final: lista de links numerados, um por linha, no formato "1. [Fonte] url"
- Tom informal, direto, sem asteriscos excessivos

Artigos:
{lista}""",
        }],
    )
    return resposta.content[0].text

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.form.get("Body", "").strip()
    resp = MessagingResponse()

    try:
        if é_pedido_de_notícias(body):
            artigos = buscar_artigos()
            if not artigos:
                resp.message("😕 Não achei notícias agora. Tenta em alguns minutos.")
            else:
                briefing = formatar_briefing(artigos)
                resp.message(briefing)
        else:
            resp.message(
                '👋 Oi! Me manda *"quais são as notícias de hoje?"* '
                "para receber um briefing."
            )
    except Exception as e:
        resp.message(f"⚠️ Erro: {e}")

    return str(resp), 200, {"Content-Type": "text/xml"}

if __name__ == "__main__":
    print("🤖 Agente de notícias rodando em http://localhost:5000")
    app.run(port=5000, debug=True)
