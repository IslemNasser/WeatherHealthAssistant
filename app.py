import requests
from dotenv import load_dotenv
import os
import streamlit as st
from google import genai
from google.genai import types
from datetime import datetime

load_dotenv()

if not os.getenv("weather_api_key"):
    raise ValueError("La clé API pour OpenWeatherMap n'est pas définie dans le fichier .env")
if not os.getenv("gemini_api_key"):
    raise ValueError("La clé API pour Gemini n'est pas définie dans le fichier .env")

API_KEY_WEATHER = os.getenv("weather_api_key")
API_KEY_GEMINI = os.getenv("gemini_api_key")

client = genai.Client(api_key=API_KEY_GEMINI)
model_name = "gemini-2.5-flash"
instructions = """
Tu es un conseiller santé & bien-être basé sur la météo.

Quand un utilisateur mentionne une ville ou pose une question liée à sa santé et la météo :
1. Utilise l'outil get_weather_health pour récupérer les données météo de la ville
2. Analyse les risques : chaleur, coup de chaleur, allergies, humidité, activité physique
3. Donne des conseils concrets, bienveillants et personnalisés en français

Si l'utilisateur ne mentionne pas de ville, demande-lui de préciser sa localisation.
Si la question n'est pas liée à la météo ou la santé, réponds poliment que tu es spécialisé dans ce domaine.
"""



weather_tool = {
    "name": "get_weather_health",
    "description": "Récupère les conditions météo actuelles d'une ville pour analyser les risques santé : chaleur, humidité, allergies, vent.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "city": {
                "type": "STRING",
                "description": "Le nom de la ville dont on veut analyser la météo santé."
            }
        },
        "required": ["city"]
    }
}

def get_weather_health(city: str) -> str:
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": API_KEY_WEATHER, "units": "metric", "lang": "fr"}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        temp     = data["main"]["temp"]
        feels    = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind     = data["wind"]["speed"]
        desc     = data["weather"][0]["description"]
        name     = data["name"]
        lat      = data["coord"]["lat"]
        lon      = data["coord"]["lon"]

        uv_url = "https://api.openweathermap.org/data/2.5/uvi"
        uv_params = {"lat": lat, "lon": lon, "appid": API_KEY_WEATHER}
        uv_data = requests.get(uv_url, params=uv_params, timeout=10).json()
        uv_index = uv_data.get("value", "indisponible")

        if isinstance(uv_index, float) or isinstance(uv_index, int):
            if uv_index <= 2:
                uv_level = "Faible — pas de protection nécessaire"
            elif uv_index <= 5:
                uv_level = "Modéré — crème solaire recommandée"
            elif uv_index <= 7:
                uv_level = "Élevé — crème solaire obligatoire, éviter 12h-16h"
            elif uv_index <= 10:
                uv_level = "Très élevé — rester à l'ombre, chapeau obligatoire"
            else:
                uv_level = "Extrême — éviter toute exposition"
        else:
            uv_level = "indisponible"

        return (
            f"Ville : {name}\n"
            f"Température : {temp}°C (ressenti {feels}°C)\n"
            f"Humidité : {humidity}%\n"
            f"Vent : {wind} m/s\n"
            f"Conditions : {desc}\n"
            f"Indice UV : {uv_index} — {uv_level}\n"
            f"Note : humidité >70% favorise les moisissures, "
            f"vent >4 m/s disperse le pollen."
        )

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"Ville introuvable : {city}."
        return f"Erreur API : {e}"
    except Exception as e:
        return f"Erreur : {e}"
    
    
def get_chat(model_name: str):
    if f"chat-{model_name}" not in st.session_state:
        tools = types.Tool(function_declarations=[weather_tool])
        config = types.GenerateContentConfig(
            temperature=0.3,
            top_p=0.95,
            system_instruction=[types.Part.from_text(text=instructions)],
            tools=[tools]
        )
        chat = client.chats.create(model=model_name, config=config)
        st.session_state[f"chat-{model_name}"] = chat
    return st.session_state[f"chat-{model_name}"]  # ← manquait ici


def call_model(prompt: str) -> str:
    chat = get_chat(model_name="gemini-2.5-flash")
    message_content = prompt

    while True:
        response = chat.send_message(message_content)
        has_tool_calls = False

        for part in response.candidates[0].content.parts:
            if part.function_call:
                has_tool_calls = True
                fn = part.function_call
                if fn.name == "get_weather_health":
                    result = get_weather_health(**fn.args)  # ta fonction météo
                    function_response_part = types.Part.from_function_response(
                        name=fn.name,
                        response={"result": result}
                    )
                    message_content = [function_response_part]

        if not has_tool_calls:
            break

    return response.text


# Interface Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Bonjour ! Posez-moi une question sur votre santé et la météo de votre ville 😊",
            "time": datetime.now().strftime("%H:%M")
        }
    ]

# --- 2. SIDEBAR ENSUITE ---
with st.sidebar:
    st.title("💬 Historique")
    st.divider()
    
    total = len(st.session_state.messages)
    st.write(f"**{total} messages**")
    
    if total > 5:
        st.caption(f"↑ {total - 5} messages plus anciens")
    
    st.divider()
    for msg in st.session_state.messages[-5:]:
        role = "🧑" if msg["role"] == "user" else "🤖"
        time = msg.get("time", "")
        preview = msg["content"][:40] + "..." if len(msg["content"]) > 40 else msg["content"]
        st.caption(f"{role} {time} — {preview}")
    
    st.divider()
    if st.button("🗑️ Effacer la conversation"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Bonjour ! Posez-moi une question sur votre santé et la météo de votre ville 😊",
                "time": datetime.now().strftime("%H:%M")
            }
        ]
        del st.session_state[f"chat-{model_name}"]
        st.rerun()

# ---  CHAT ---
st.title("Conseiller Santé & Météo 🌤️")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "time" in msg:
            st.caption(msg["time"])

if prompt := st.chat_input("Ex: J'ai des allergies, puis-je sortir à Tunis ?"):
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "time": datetime.now().strftime("%H:%M")
    })
    with st.chat_message("user"):
        st.write(prompt)
        st.caption(datetime.now().strftime("%H:%M"))

    with st.spinner("Analyse en cours..."):
        response = call_model(prompt)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "time": datetime.now().strftime("%H:%M")
    })
    with st.chat_message("assistant"):
        st.write(response)
        st.caption(datetime.now().strftime("%H:%M"))
