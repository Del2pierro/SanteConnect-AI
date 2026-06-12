# 🏥 SanteConnect AI - Assistant Médical

Un assistant médical alimenté par l'IA utilisant FastAPI et Transformers pour fournir des conseils de santé basés sur du traitement du langage naturel (NLP).

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [Structure du projet](#-structure-du-projet)
- [API Documentation](#-api-documentation)
- [Développement](#-développement)
- [Contribution](#-contribution)

## ✨ Fonctionnalités

- **Chat en temps réel** avec un assistant médical alimenté par l'IA
- **Génération de texte** basée sur le modèle DistilGPT-2 de Hugging Face
- **API REST** robuste avec FastAPI
- **Interface utilisateur** responsive et moderne
- **Gestion CORS** pour les appels cross-origin
- **Configuration modulaire** facile à maintenir et étendre
- **Historique persistant** des chats en SQLite en développement et PostgreSQL en audit
- **Logging** complet pour le débogage

## 🏗️ Architecture

```
Api_Assistant_medical/
├── app/                          # Code principal de l'application
│   ├── __init__.py              # Initialisation du package
│   ├── main.py                  # Point d'entrée FastAPI
│   ├── config.py                # Configuration de l'application
│   ├── models.py                # Modèles Pydantic (validation)
│   ├── routes/                  # Endpoints API
│   │   ├── __init__.py
│   │   └── chat.py              # Routes de chat
│   └── services/                # Logique métier
│       ├── __init__.py
│       └── llm_service.py       # Service du modèle LLM
├── frontend/                     # Application frontend
│   ├── index.html
│   ├── script.js
│   └── style.css
├── .env.example                 # Exemple de variables d'environnement
├── requirements.txt             # Dépendances Python
├── README.md                    # Ce fichier
└── main.py                      # Point d'entrée alternatif (ancien)

```

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Un token Hugging Face (optionnel pour les modèles privés)

### Étapes

1. **Cloner ou télécharger le projet**

```bash
cd Api_Assistant_medical
```

2. **Créer un environnement virtuel**

```bash
# Windows
python -m venv env
env\Scripts\activate

# macOS/Linux
python3 -m venv env
source env/bin/activate
```

3. **Installer les dépendances**

```bash
pip install -r requirements.txt
```

4. **Configurer les variables d'environnement**

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer le fichier .env avec vos paramètres
```

## ⚙️ Configuration

### Fichier `.env`

Créez un fichier `.env` à la racine du projet :

```env
# Configuration Debug
DEBUG=False

# Ollama local
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=120

# Paramètres du modèle
MAX_NEW_TOKENS=50
TEMPERATURE=0.7
TOP_P=0.9

# Serveur
HOST=0.0.0.0
PORT=8000
```

### Variables importantes

| Variable         | Description                    | Valeur par défaut        |
| ---------------- | ------------------------------ | ------------------------ |
| `OLLAMA_URL`     | URL de l'API Ollama locale     | `http://localhost:11434` |
| `OLLAMA_MODEL`   | Nom du modèle Ollama           | `llama3.2`               |
| `OLLAMA_TIMEOUT` | Délai max pour l'appel Ollama  | `120`                    |
| `MAX_NEW_TOKENS` | Nombre max de tokens générés   | `50`                     |
| `TEMPERATURE`    | Créativité du modèle (0.0-1.0) | `0.7`                    |
| `TOP_P`          | Paramètre nucleus sampling     | `0.9`                    |
| `PORT`           | Port du serveur                | `8000`                   |

## 📖 Utilisation

### Démarrer le serveur

```bash
# Avec uvicorn directement
uvicorn app.main:app --reload

# Ou avec le script main.py
python main.py
```

Le serveur démarrera sur `http://localhost:8000`

### Accéder à l'application

- **Interface utilisateur** : http://localhost:8000/static/
- **Documentation API (Swagger)** : http://localhost:8000/docs
- **Documentation API (ReDoc)** : http://localhost:8000/redoc

## 🔌 API Documentation

### Endpoints disponibles

#### 1. Vérification de santé

```http
GET /api/
```

**Réponse** (200):

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

#### 2. Chat avec l'assistant

```http
POST /api/chat
Content-Type: application/json

{
  "message": "Quels sont les symptômes de la grippe?"
}
```

**Réponse** (200):

```json
{
  "response": "Les symptômes de la grippe incluent..."
}
```

**Erreur** (500):

```json
{
  "detail": "Erreur lors de la génération de la réponse"
}
```

#### 3. Historique des chats

```http
GET /api/chat/history
```

**Réponse** (200):

```json
{
  "items": [
    {
      "id": 1,
      "message": "Quels sont les symptômes de la grippe ?",
      "response": "...",
      "created_at": "2026-06-10T12:34:56.000000+00:00"
    }
  ],
  "count": 1
}
```

L'historique est stocké en base de données. En développement, la configuration par défaut utilise SQLite via `DATABASE_URL=sqlite:///./app.db`. Pour l'audit ou la production, vous pouvez pointer `DATABASE_URL` vers PostgreSQL avec un format du type `postgresql+psycopg://user:password@host:5432/database`.

## 👨‍💻 Développement

### Structure modulaire

Le projet est organisé selon le pattern MVC :

- **Models** (`app/models.py`) : Définition des structures de données (Pydantic)
- **Routes** (`app/routes/`) : Endpoints API
- **Services** (`app/services/`) : Logique métier et interaction avec le modèle LLM

### Ajouter une nouvelle route

1. Créez un nouveau fichier dans `app/routes/` (ex: `app/routes/health.py`)
2. Définissez votre router :

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("/status")
async def get_status():
    return {"status": "ok"}
```

3. Incluez-le dans `app/main.py` :

```python
from app.routes import health
app.include_router(health.router)
```

### Ajouter une nouvelle dépendance

1. Mettez à jour `requirements.txt`
2. Installez-la : `pip install -r requirements.txt`

### Logging

Le logging est configuré dans `app/main.py`. Pour utiliser le logging :

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Message d'information")
logger.error("Message d'erreur")
```

## 🧪 Tests

Pour exécuter des tests :

```bash
# Installer pytest
pip install pytest httpx

# Créer un fichier tests/test_api.py
# Lancer les tests
pytest
```

Exemple de test :

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

## 📱 Frontend

Le frontend se trouve dans le dossier `frontend/` et contient :

- `index.html` : Structure HTML
- `script.js` : Logique JavaScript et appels API
- `style.css` : Styles CSS

Pour servir le frontend, la configuration StaticFiles dans `app/main.py` le monte automatiquement.

## 🐛 Dépannage

### Erreur "Module not found"

```bash
pip install -r requirements.txt
```

### Le modèle met du temps à charger

Le modèle DistilGPT-2 est téléchargé une fois au premier démarrage. C'est normal que le premier lancement soit plus lent.

### Erreur CORS

Vérifiez votre configuration CORS dans `app/config.py`. En production, remplacez `["*"]` par les domaines autorisés.

### Token Hugging Face

Pour utiliser des modèles privés, obtenez un token sur https://huggingface.co/settings/tokens et configurez-le dans `.env`.

## 📚 Ressources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Uvicorn Documentation](https://www.uvicorn.org/)

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Forker le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Committer vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Pousser vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 License

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 👤 Auteur

Créé par Pierre - 2026

---

**Note** : Ceci est un projet d'assistant médical à titre informatif. Pour des conseils médicaux réels, consultez toujours un professionnel de santé qualifié.
