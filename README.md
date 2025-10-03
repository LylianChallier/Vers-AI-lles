# Hackathon Datacraft - Château de Versailles

Pour lancer le projet, se mettre à la racine et exécuter :
```bash
docker compose up --build
```

Une fois que les logs affichent les lignes suivantes :
```
backend-1  | INFO:     Started server process [1]
backend-1  | INFO:     Waiting for application startup.
backend-1  | INFO:     Application startup complete.
backend-1  | INFO:     Uvicorn running on http://0.0.0.0:1234 (Press CTRL+C to quit)
```

Rendez-vous sur la page [localhost:1234](localhost:1234) pour accéder à Swagger UI pour tester le résultat du backend.

Pour tester le chatbot, cliquez sur le premier élément (POST /chat Chat With Agent), puis cliquez sur `Try it out`. Le prompt se situe dans la clé message (initialement il y a écrit `string`). Ecrivez votre prompt puis cliquez sur `Exécuter`.

La réponse s'affiche plus bas, dans `Response body`.

Le front est à http://127.0.0.1:8501/
après un docker compose up