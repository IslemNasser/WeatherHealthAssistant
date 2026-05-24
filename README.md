# Weather Health Assistant

Un assistant santé intelligent qui analyse les conditions météo en temps réel et génère des conseils personnalisés (allergies, chaleur, activité physique, UV) via Gemini AI.

---

## Features

- Analyse météo complète — température, ressenti, humidité, vent, conditions
- Indice UV en temps réel avec interprétation du niveau de risque
- IA Gemini 2.5 Flash — conseils santé personnalisés 
- Tool Calling automatique — le LLM décide quand appeler l'API météo
- Chat conversationnel avec historique 
- Reset de session à tout moment

---

## Stack

| Outil | Rôle |
|---|---|
| Python 3.11+ | Langage principal |
| Streamlit | Interface web |
| Google Gemini 2.5 Flash | LLM + Tool Calling |
| OpenWeatherMap API | Données météo + Indice UV |
| python-dotenv | Gestion des clés API |

---

## Installation

### 1. Cloner le repo

```bash
git clone https://github.com/ton-username/weather-health-app.git
cd weather-health-app
```

### 2. Créer un environnement virtuel

```bash
uv venv
source venv/bin/activate     # Linux / Mac
venv\Scripts\activate        # Windows
```

### 3. Installer les dépendances

```bash
uv pip install -r requirements.txt
```

### 4. Configurer les clés API

Crée un fichier `.env` à la racine :

```env
weather_api_key=ta_clé_openweathermap
gemini_api_key=ta_clé_google_gemini
```

Obtenir les clés :
- OpenWeatherMap → https://openweathermap.org/api 
- Google Gemini → https://aistudio.google.com 

### 5. Lancer

```bash
streamlit run app.py
```

---

