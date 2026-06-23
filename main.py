import os
import requests
import anthropic
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from datetime import date

load_dotenv()

app = Flask(__name__)
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def extrair_topico(mensagem: str) -> str | None:
    resposta = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": f"""The user sent this WhatsApp message: "{mensagem}"

Is this a request for news about a topic? If yes, reply with ONLY the topic (e.g. "artificial intelligence", "Brazil economy", "NBA"). 
If it is NOT a news request, reply with exactly: NOT_NEWS

Reply with nothing else."""
        }]
    )
    resultado = resposta.content[0].text.strip()
    if resultado == "NOT_NEWS":
        return None
    return resultado


def buscar_artigos(topico: str) -> list:
    r = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "q": topico,
            "pageSize": 8,
            "sortBy": "publishedAt",
            "apiKey": os.getenv("NEWSAPI_KEY"),
        },
        timeout=10,
    )
    data = r.json()
    if data.get("status") != "ok":
        raise RuntimeError(f"NewsAPI: {data.get('message', 'unknown error')}")
    return [
        a for a in data.get("articles", [])
        if a.get("title") and "[Removed]" not in a["title"]
    ]


def formatar_briefing(topico: str, artigos: list) -> str:
    lista = "\n".join(
        f"• {a['title']} | {a['source']['name']} | {a['url']}"
        for a in artigos
    )
    resposta = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=700,
        messages=[{
            "role": "user",
            "content": f"""Create a WhatsApp news briefing about "{topico}" from the articles below.

Required format:
- Line 1: "📰 *{topico}* — {date.today().strftime('%B %d, %Y')}"
- 4-5 numbered highlights, each with a relevant emoji and 1 concise sentence
- Final section: numbered links, one per line, format: "1. [Source] url"
- Informal, direct tone. Reply in the same language the user wrote in.

Articles:
{lista}"""
        }]
    )
    return resposta.content[0].text


@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.form.get("Body", "").strip()
    resp = MessagingResponse()

    if not body:
        resp.message("👋 Send me a topic and I'll find the latest news for you.")
        return str(resp), 200, {"Content-Type": "text/xml"}

    try:
        topico = extrair_topico(body)
        if topico is None:
            resp.message(
                "👋 Hi! Ask me about any topic and I'll send you a news briefing.\n\n"
                "Examples:\n• tell me about AI\n• what's happening in Brazil?\n• NBA news"
            )
        else:
            artigos = buscar_artigos(topico)
            if not artigos:
                resp.message(f"😕 No articles found for *{topico}*. Try a different topic.")
            else:
                briefing = formatar_briefing(topico, artigos)
                resp.message(briefing)
    except Exception as e:
        resp.message(f"⚠️ Error: {e}")

    return str(resp), 200, {"Content-Type": "text/xml"}


@app.route("/", methods=["GET"])
def health():
    return "🤖 News agent running.", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
