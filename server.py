from flask import Flask, request, jsonify, send_file
import requests
import os

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


@app.route("/")
def start():
    return send_file("index.html")


@app.route("/chat", methods=["POST"])
def chat():

    daten = request.get_json(silent=True) or {}
    frage = daten.get("frage", "").strip()

    if not frage:
        return jsonify({
            "antwort": "Schreib mir einfach eine Frage 🙂"
        })

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

            json={
                "model": "openai/gpt-oss-20b",

                "messages": [

                    {
                        "role": "system",
                        "content": """
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
                    },

                    {
                        "role": "user",
                        "content": frage
                    }

                ],

                "temperature": 0.7,
                "max_tokens": 500
            },

            timeout=60
        )


        antwort.raise_for_status()

        ergebnis = antwort.json()

        text = ergebnis[
            "choices"
        ][0][
            "message"
        ][
            "content"
        ]


        return jsonify({
            "antwort": text.strip()
        })


    except Exception as fehler:

        print("WLADI AI FEHLER:", fehler)

        return jsonify({
            "antwort": "Wladi AI konnte gerade keine Verbindung zur KI herstellen. 😕"
        }), 500


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
    )
