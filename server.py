from flask import Flask, request, jsonify, send_file, Response, stream_with_context
import requests
import os
import json

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


@app.route("/")
def start():
    return send_file("index.html")


@app.route("/googleec9551de99885df5.html")
def google_verifizierung():
    return send_file("googleec9551de99885df5.html")


SYSTEM_TEXT = """
Du bist Wladi AI, ein freundlicher KI-Assistent.

Dein Name ist Wladi AI.

Wenn jemand fragt, wer dich erstellt hat, antworte:
"Wladi AI wurde von Wladimir Kissel erstellt."

Regeln:
- Antworte normalerweise kurz und verständlich.
- Nutze passende Emojis, aber nicht zu viele.
- Wenn der Nutzer Stichpunkte möchte, antworte in Stichpunkten.
- Verstehe Tippfehler so gut wie möglich.
- Wenn der Nutzer Deutsch schreibt, antworte auf Deutsch.
- Wenn der Nutzer eine andere Sprache benutzt, kannst du in dieser Sprache antworten.
- Erfinde keine Fakten.
- Wenn du etwas nicht weißt, sage es ehrlich.
"""


def payload(frage, stream=False):
    return {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": SYSTEM_TEXT},
            {"role": "user", "content": frage}
        ],
        "temperature": 0.7,
        "max_tokens": 500,
        "stream": stream
    }


@app.route("/chat", methods=["POST"])
def chat():
    daten = request.get_json(silent=True) or {}
    frage = daten.get("frage", "").strip()

    if not frage:
        return jsonify({"antwort": "Schreib mir einfach eine Frage 🙂"})

    if not GROQ_API_KEY:
        return jsonify({
            "antwort": "Der API-Key für Wladi AI wurde noch nicht eingerichtet."
        }), 500

    try:
        antwort = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload(frage, False),
            timeout=60
        )

        antwort.raise_for_status()
        ergebnis = antwort.json()
        text = ergebnis["choices"][0]["message"]["content"]

        return jsonify({"antwort": text.strip()})

    except Exception as fehler:
        print("WLADI AI FEHLER:", fehler)
        return jsonify({
            "antwort": "Wladi AI konnte gerade keine Verbindung zur KI herstellen. 😕"
        }), 500


@app.route("/chat-stream", methods=["POST"])
def chat_stream():
    daten = request.get_json(silent=True) or {}
    frage = daten.get("frage", "").strip()

    if not frage:
        return Response("Schreib mir einfach eine Frage 🙂", mimetype="text/plain")

    if not GROQ_API_KEY:
        return Response(
            "Der API-Key für Wladi AI wurde noch nicht eingerichtet.",
            status=500,
            mimetype="text/plain"
        )

    def generate():
        try:
            with requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload(frage, True),
                stream=True,
                timeout=60
            ) as antwort:
                antwort.raise_for_status()

                for line in antwort.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data:"):
                        continue

                    data = line[5:].strip()
                    if data == "[DONE]":
                        break

                    try:
                        obj = json.loads(data)
                        delta = obj.get("choices", [{}])[0].get("delta", {})
                        chunk = delta.get("content")
                        if chunk:
                            yield chunk
                    except (json.JSONDecodeError, IndexError, TypeError):
                        continue

        except Exception as fehler:
            print("WLADI AI STREAM FEHLER:", fehler)
            yield "\n\nWladi AI konnte gerade keine Verbindung zur KI herstellen. 😕"

    return Response(
        stream_with_context(generate()),
        mimetype="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
