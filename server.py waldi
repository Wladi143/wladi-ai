from flask import Flask, request, jsonify, send_file
import requests
import os

app = Flask(__name__)


@app.route("/")
def start():
    return send_file("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    frage = request.json.get("frage", "")

    prompt = f"""
Du bist Wladi AI, eine freundliche und hilfreiche KI.

Dein Name ist Wladi AI.

Wenn jemand fragt, wer dich erstellt hat, antworte:
"Wladi AI wurde von Wladimir Kissel erstellt."

Verstehe auch Nachrichten mit Tippfehlern.
Antworte auf Deutsch, wenn der Nutzer Deutsch schreibt.
Antworte direkt und verständlich.
Erfinde keine Fakten.
Wenn du etwas nicht weißt, sage es ehrlich.

Nachricht:
{frage}

Antwort:
"""

    try:
        antwort = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:1b",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        antwort.raise_for_status()
        daten = antwort.json()

        return jsonify({
            "antwort": daten.get("response", "").strip()
        })

    except Exception as fehler:
        print("FEHLER:", fehler)

        return jsonify({
            "antwort": "Wladi AI konnte gerade keine Verbindung zur KI herstellen."
        })


if __name__ == "__main__":
    print("WLADI AI SERVER STARTET")

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
