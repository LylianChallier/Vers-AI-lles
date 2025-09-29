# Hackathon Datacraft - Château de Versailles

[Utilisateur]
      |
      v
[FastAPI / MCP frontal]
      |
      +--> [Route Input / LangGraph] ---(décision)---> [LLM direct] ou [Agent + Tools]
                                                   |--> [Tools: Versailles, Maps, Météo...]
                                                   |
                                                [Mémoire persistante: Redis / SQLite]
      |
      v
   Retour utilisateur
