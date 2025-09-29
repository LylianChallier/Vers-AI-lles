# Hackathon Datacraft - Château de Versailles

## Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop) ou équivalent avec Docker Compose v2
- (Optionnel) Python 3.10+ si vous préférez lancer l'API sans conteneur
- Une clé [ngrok](https://ngrok.com/) si vous souhaitez exposer l'API publiquement

## Démarrage rapide

1. **Configurer l'environnement**
   - Dupliquez `.env.example` en `.env` si nécessaire et ajustez les clés (OpenWeather, etc.).
   - Placez-vous à la racine du dépôt (`les_4_MousquetAIres`).

2. **Construire et lancer l'API**
   ```bash
   docker compose up --build
   ```
   Attendez les logs suivants :
   ```
   backend-1  | INFO:     Application startup complete.
   backend-1  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
   ```

3. **Explorer la documentation interactive**
   Rendez-vous sur [http://localhost:8000/docs](http://localhost:8000/docs) pour tester les endpoints (`POST /chat`, `POST /plan`, etc.).

## Exposer l'API avec ngrok

Une fois Docker lancé, vous pouvez publier l'API :

```bash
ngrok http 8000 --url https://hackversailles-8-yeah.ngrok.app
```

> ℹ️ L'usage d'une URL statique nécessite un compte ngrok payant. Sans cela, omettez `--url …` et réutilisez l'URL générée dynamiquement.

## Exemple d'appel au planificateur

Testez l'endpoint MCP-aware `/plan` (qui ajuste le parcours selon la météo) :

```bash
curl -sS -X POST https://hackversailles-8-yeah.ngrok.app/plan \
  -H 'Content-Type: application/json' \
  -d '{
        "query":"Family with stroller, low budget, mostly outdoors",
        "date":"2025-10-05",
        "start_time":"14:00",
        "duration_min":210
      }' | jq '{reponse, itinerary, warnings, alternatives}'
```

> Remplacez l'URL par `http://localhost:8000/plan` si vous restez en local.

### Utiliser l'interface Swagger pour le chatbot

Dans `POST /chat`, cliquez sur `Try it out`, saisissez votre prompt dans le champ `message` puis `Execute`. La réponse du modèle apparaît dans `Response body`.
