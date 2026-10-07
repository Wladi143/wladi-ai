from flask import Flask, request, jsonify, send_file, Response, stream_with_context
import requests
import os
import json

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


@app.route("/")
def start():
    return send_file("index.html")


@app.route("/logo.png")
def logo():
    return send_file("logo.png")


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


def baue_verlauf(verlauf):
    messages = [{"role": "system", "content": SYSTEM_TEXT}]

    if isinstance(verlauf, list):
        for eintrag in verlauf[-20:]:
            if not isinstance(eintrag, dict):
                continue

            rolle = eintrag.get("role")
            text = eintrag.get("text", "")

            if rolle not in ("user", "ai") or not isinstance(text, str):
                continue

            text = text.strip()
            if not text:
                continue

            messages.append({
                "role": "assistant" if rolle == "ai" else "user",
                "content": text[:6000]
            })

    return messages


def payload(frage, stream=False, verlauf=None):
    messages = baue_verlauf(verlauf)
    messages.append({"role": "user", "content": frage})

    return {
        "model": "openai/gpt-oss-20b",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500,
        "stream": stream
    }


@app.route("/chat", methods=["POST"])
def chat():
    daten = request.get_json(silent=True) or {}
    frage = daten.get("frage", "").strip()
    verlauf = daten.get("verlauf", [])

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
            json=payload(frage, False, verlauf),
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
    verlauf = daten.get("verlauf", [])

    if not frage:
        return Response("Schreib mir einfach eine Frage 🙂", content_type="text/plain; charset=utf-8")

    if not GROQ_API_KEY:
        return Response(
            "Der API-Key für Wladi AI wurde noch nicht eingerichtet.",
            status=500,
            content_type="text/plain; charset=utf-8"
        )

    def generate():
        try:
            with requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                },
                json=payload(frage, True, verlauf),
                stream=True,
                timeout=60
            ) as antwort:
                antwort.raise_for_status()

                # Bytes selbst als UTF-8 dekodieren, damit Umlaute und Emojis
                # beim Streaming nicht kaputtgehen.
                for line in antwort.iter_lines(decode_unicode=False):
                    if not line:
                        continue

                    try:
                        line = line.decode("utf-8")
                    except UnicodeDecodeError:
                        line = line.decode("utf-8", errors="replace")

                    if not line.startswith("data:"):
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
        content_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
